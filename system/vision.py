#!/usr/bin/env python3
"""
WalkerSense vision — where is the robot? (live, on-device)

Webcam → tiny ExecuTorch CNN (vision.pte) → zone: absent|left|center|right
→ the robot reacts through the Bridge (matrix ack) and the dashboard gets
a fresh preview frame + the detection (vision_state.json + latest.jpg).

    python3 vision.py [--camera 0] [--frames N]   (N=0: run until Ctrl-C)
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import cv2
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rpc_client import Bridge, BridgeError  # noqa: E402

SIZE = 64


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--frames", type=int, default=0)
    ap.add_argument("--model", default=os.path.join(HERE, "vision.pte"))
    args = ap.parse_args()

    labels = ["absent", "left", "center", "right"]
    if os.path.exists(os.path.join(HERE, "vision_labels.json")):
        with open(os.path.join(HERE, "vision_labels.json")) as f:
            labels = json.load(f)["labels"]

    method = None
    if os.path.exists(args.model):
        from executorch.runtime import Runtime

        runtime = Runtime.get()
        method = runtime.load_program(args.model).load_method("forward")
        print(f"vision model loaded: {args.model} labels={labels}")
    else:
        print("no vision model yet — preview mode: the camera streams and "
              "the dashboard watches; teach it (vision_train.py) to name zones")

    detect_method, detect_labels = None, []
    dpath = os.path.join(HERE, "detect.pte")
    if os.path.exists(dpath) and os.path.exists(os.path.join(HERE, "detect_labels.json")):
        from executorch.runtime import Runtime

        detect_labels = json.load(open(os.path.join(HERE, "detect_labels.json")))["labels"]
        detect_method = Runtime.get().load_program(dpath).load_method("forward")
        print(f"robot detector loaded: labels={detect_labels}")

    try:
        bridge = Bridge()
    except Exception:
        bridge = None

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit("camera did not open")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    for _ in range(15):
        cap.read()

    n = 0
    last_zone = None
    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.1)
            continue
        small = cv2.resize(frame, (SIZE, SIZE))
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(rgb).permute(2, 0, 1).float().unsqueeze(0) / 255.0
        if method is not None:
            t0 = time.perf_counter()
            scores = method.execute([tensor])[0][0]
            infer_ms = (time.perf_counter() - t0) * 1000
            probs = torch.softmax(scores, dim=0)
            zone = labels[int(torch.argmax(probs))]
            conf = float(torch.max(probs))
            state = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "zone": zone, "confidence": round(conf, 3),
                     "infer_ms": round(infer_ms, 1),
                     "probs": {labels[i]: round(float(probs[i]), 3) for i in range(len(labels))}}
            print(f"zone={zone:7s} conf={conf:.2f} infer={infer_ms:.1f}ms", flush=True)
        else:
            zone = "watching"
            state = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "zone": "watching", "confidence": None, "probs": {},
                     "note": "camera live — vision model not trained yet"}
            print("preview frame", flush=True)
        if detect_method is not None:
            dscores = detect_method.execute([tensor])[0][0]
            dprobs = torch.softmax(dscores, dim=0)
            dlabel = detect_labels[int(torch.argmax(dprobs))]
            dconf = float(torch.max(dprobs))
            state["robot_probs"] = {detect_labels[i]: round(float(dprobs[i]), 3)
                                     for i in range(len(detect_labels))}
            if dlabel != "other" and dconf >= 0.6:
                state["robot"] = dlabel
                state["robot_confidence"] = round(dconf, 3)
                print(f"robot detected: {dlabel} ({dconf:.2f})", flush=True)
        with open(os.path.join(HERE, "vision_state.json"), "w") as f:
            json.dump(state, f, indent=1)
        cv2.imwrite(os.path.join(HERE, "latest.jpg"), frame)

        if bridge is not None and zone != last_zone:
            try:
                bridge.call("matrix_fill", zone != "absent")
            except BridgeError:
                pass
            last_zone = zone
        n += 1
        if args.frames and n >= args.frames:
            break
        time.sleep(0.3)
    cap.release()


if __name__ == "__main__":
    main()
