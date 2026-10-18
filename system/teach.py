#!/usr/bin/env python3
"""
WalkerSense teach loop — learning happens ON the device.

    teach.py add --features "ax,ay,az,gx,gy,gz" --label fallen
    teach.py retrain
    teach.py classify --features "ax,ay,az,gx,gy,gz"

`add` appends a labeled sample to samples.json (marked source="taught",
with a timestamp). `retrain` re-runs train_model.py right here on the
board, verifies the new .pte loads and classifies, then swaps it in
atomically (the previous model is kept as model.prev.pte for rollback).
Nothing leaves the device; no cloud is involved at any point.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "samples.json")
MODEL = os.path.join(HERE, "model.pte")
CLASSES = ["standing", "walking", "fallen", "flipped"]


def parse_features(text):
    values = [float(v) for v in text.split(",")]
    if len(values) != 6:
        raise SystemExit("features must be 6 comma-separated numbers")
    return values


def classify(model_path, features):
    import torch
    from executorch.runtime import Runtime

    runtime = Runtime.get()
    method = runtime.load_program(model_path).load_method("forward")
    scores = method.execute([torch.tensor([features], dtype=torch.float32)])[0][0]
    probs = torch.softmax(scores, dim=0)
    return CLASSES[int(torch.argmax(probs))], [round(float(p), 3) for p in probs]


def log_event(kind, detail):
    path = os.path.join(HERE, "events.log")
    with open(path, "a") as f:
        f.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "kind": kind, "detail": detail}) + "\n")


def cmd_add(args):
    features = parse_features(args.features)
    label = CLASSES.index(args.label)
    with open(SAMPLES) as f:
        samples = json.load(f)
    before = None
    if os.path.exists(MODEL):
        before = classify(MODEL, features)
    samples.append(
        {
            "features": features,
            "label": label,
            "source": "taught",
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )
    with open(SAMPLES, "w") as f:
        json.dump(samples, f, indent=1)
    print(f"sample added: {args.label} {features} (dataset now {len(samples)} base samples)")
    log_event("teach-add", f"human taught: {features} = {args.label}")
    if before:
        print(f"current model says: {before[0]} {before[1]}")


def cmd_retrain(args):
    t0 = __import__("time").perf_counter()
    new_path = os.path.join(HERE, "model.new.pte")
    result = subprocess.run(
        [sys.executable, os.path.join(HERE, "train_model.py"), "--out", new_path],
        capture_output=True,
        text=True,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr[-2000:])
        raise SystemExit("training failed; model unchanged")
    # Verify the new program loads before swapping it in.
    probe = [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    pose, probs = classify(new_path, probe)
    print(f"new model verified (probe standing -> {pose} {probs})")
    if os.path.exists(MODEL):
        os.replace(MODEL, os.path.join(HERE, "model.prev.pte"))
    os.replace(new_path, MODEL)
    print(f"model swapped in ({os.path.getsize(MODEL)} bytes), "
          f"retrain took {__import__('time').perf_counter() - t0:.1f}s on-device")
    log_event("teach-retrain", "human teaching retrained the model on-device")


def cmd_classify(args):
    features = parse_features(args.features)
    pose, probs = classify(MODEL, features)
    print(f"{features} -> {pose} {probs}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add")
    p_add.add_argument("--features", required=True)
    p_add.add_argument("--label", required=True, choices=CLASSES)
    p_add.set_defaults(fn=cmd_add)
    p_retrain = sub.add_parser("retrain")
    p_retrain.set_defaults(fn=cmd_retrain)
    p_classify = sub.add_parser("classify")
    p_classify.add_argument("--features", required=True)
    p_classify.set_defaults(fn=cmd_classify)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
