#!/usr/bin/env python3
"""
REM PhysicalAI — turn photos into a robot detector dataset.

Takes ordinary photos (jpg/png) of a robot — e.g. one phone photo of
the PuppyPi — and builds dataset_detect/<label>/ frames in the same
format the camera capture produces, multiplying each photo with
honest augmentations (flips, crops at several scales, brightness and
contrast jitters) so a single photo becomes a small training set.

    python3 vision_ingest.py --label puppy --photos a.jpg b.jpg [--per 24]
    python3 vision_ingest.py --label other --from-dataset center,left
"""
import argparse
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "dataset_detect")
rng = np.random.default_rng(11)


def variants(img, per):
    h, w = img.shape[:2]
    outs = [img, cv2.flip(img, 1)]
    while len(outs) < per:
        scale = rng.uniform(0.55, 1.0)
        cw, ch = int(w * scale), int(h * scale)
        x = int(rng.integers(0, max(1, w - cw)))
        y = int(rng.integers(0, max(1, h - ch)))
        crop = img[y:y + ch, x:x + cw]
        crop = cv2.resize(crop, (w, h))
        if rng.random() < 0.5:
            crop = cv2.flip(crop, 1)
        alpha = rng.uniform(0.75, 1.25)
        beta = rng.uniform(-25, 25)
        crop = np.clip(crop * alpha + beta, 0, 255).astype(np.uint8)
        outs.append(crop)
    return outs[:per]


def save(label, frames):
    folder = os.path.join(ROOT, label)
    os.makedirs(folder, exist_ok=True)
    n0 = len([f for f in os.listdir(folder) if f.endswith(".npy")])
    for i, fr in enumerate(frames):
        np.save(os.path.join(folder, f"img_{n0 + i:03d}.npy"), fr)
    print(f"{label}: +{len(frames)} frames (total {n0 + len(frames)})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--photos", nargs="*", default=[])
    ap.add_argument("--from-dataset", default="",
                    help="comma labels of dataset/ to copy as-is")
    ap.add_argument("--per", type=int, default=24,
                    help="frames generated per photo")
    args = ap.parse_args()

    frames = []
    for path in args.photos:
        img = cv2.imread(path)
        if img is None:
            raise SystemExit(f"cannot read {path}")
        frames += variants(img, args.per)
    for lab in [s for s in args.from_dataset.split(",") if s]:
        folder = os.path.join(HERE, "dataset", lab)
        for name in sorted(os.listdir(folder)):
            if name.endswith(".npy"):
                frames.append(np.load(os.path.join(folder, name)))
    if not frames:
        raise SystemExit("nothing to ingest")
    save(args.label, frames)


if __name__ == "__main__":
    main()
