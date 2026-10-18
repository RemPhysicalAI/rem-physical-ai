#!/usr/bin/env python3
"""
Collect a labeled vision dataset from the board's webcam.

    python3 vision_capture.py --label left --count 25
    python3 vision_capture.py --label absent --count 25

Labels: absent | left | center | right — where the robot (with the ODC
on top) sits in the frame. Frames land in dataset/<label>/ as .npy
(full 640x480 BGR) plus one .jpg reference per label for eyeballing.
Move the robot between calls; keep the camera still.
"""
import argparse
import os
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS = ["absent", "left", "center", "right"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, choices=LABELS)
    ap.add_argument("--count", type=int, default=25)
    ap.add_argument("--interval", type=float, default=0.4)
    ap.add_argument("--camera", type=int, default=0)
    args = ap.parse_args()

    outdir = os.path.join(HERE, "dataset", args.label)
    os.makedirs(outdir, exist_ok=True)
    existing = len([f for f in os.listdir(outdir) if f.endswith(".npy")])

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit("camera /dev/video%d did not open" % args.camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    for _ in range(15):  # let auto-exposure settle
        cap.read()
    saved = 0
    while saved < args.count:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.1)
            continue
        idx = existing + saved
        np.save(os.path.join(outdir, f"img_{idx:03d}.npy"), frame)
        if saved == 0:
            cv2.imwrite(os.path.join(outdir, "reference.jpg"), frame)
        saved += 1
        print(f"{args.label}: {saved}/{args.count}", flush=True)
        time.sleep(args.interval)
    cap.release()
    print(f"done: {saved} frames in {outdir}")


if __name__ == "__main__":
    main()
