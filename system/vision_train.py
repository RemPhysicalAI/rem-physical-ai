#!/usr/bin/env python3
"""
Train the "where is the robot?" vision model and export it to ExecuTorch.

Input:  dataset/<label>/*.npy frames from vision_capture.py
Task:   4-way classification — absent | left | center | right
Model:  tiny CNN over 64x64 RGB. Exports vision.pte (XNNPACK) and
        vision_labels.json. Runs on the board or a laptop; the .pte is
        what ships to the device runtime either way.

    python3 vision_train.py [--epochs 40] [--out vision.pte]
"""
import argparse
import json
import os
import random

import cv2
import numpy as np
import torch
from executorch.exir import to_edge_transform_and_lower
from executorch.backends.xnnpack.partition.xnnpack_partitioner import XnnpackPartitioner

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS = ["absent", "left", "center", "right"]
SIZE = 64


class RobotFinderNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.features = torch.nn.Sequential(
            torch.nn.Conv2d(3, 16, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
            torch.nn.Conv2d(16, 32, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
            torch.nn.Conv2d(32, 32, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
        )
        self.classifier = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(32 * 8 * 8, 64), torch.nn.ReLU(),
            torch.nn.Linear(64, len(LABELS)),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


def load_dataset():
    xs, ys = [], []
    root = os.path.join(HERE, "dataset")
    for label_idx, label in enumerate(LABELS):
        folder = os.path.join(root, label)
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".npy"):
                continue
            frame = np.load(os.path.join(folder, name))
            small = cv2.resize(frame, (SIZE, SIZE))
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            xs.append(torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0)
            ys.append(label_idx)
    if not xs:
        raise SystemExit("dataset is empty — run vision_capture.py first")
    return torch.stack(xs), torch.tensor(ys, dtype=torch.long)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--out", default=os.path.join(HERE, "vision.pte"))
    args = ap.parse_args()

    torch.manual_seed(7)
    x, y = load_dataset()
    counts = {LABELS[i]: int((y == i).sum()) for i in range(len(LABELS))}
    print(f"dataset: {len(x)} frames {counts}")

    # Held-out split (stratified-ish shuffle) for an honest number.
    idx = list(range(len(x)))
    random.Random(3).shuffle(idx)
    cut = max(1, int(0.8 * len(idx)))
    tr, va = idx[:cut], idx[cut:]
    xtr, ytr, xva, yva = x[tr], y[tr], x[va], y[va]

    model = RobotFinderNet()
    opt = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = torch.nn.CrossEntropyLoss()
    for epoch in range(args.epochs):
        model.train()
        opt.zero_grad()
        loss = loss_fn(model(xtr), ytr)
        loss.backward()
        opt.step()
    model.eval()
    with torch.no_grad():
        acc_tr = (model(xtr).argmax(1) == ytr).float().mean().item()
        acc_va = (model(xva).argmax(1) == yva).float().mean().item() if va else float("nan")
    print(f"train acc {acc_tr:.3f} · held-out acc {acc_va:.3f} ({len(va)} frames)")

    exported = torch.export.export(model, (torch.randn(1, 3, SIZE, SIZE),))
    program = to_edge_transform_and_lower(
        exported, partitioner=[XnnpackPartitioner()]
    ).to_executorch()
    with open(args.out, "wb") as f:
        f.write(program.buffer)
    with open(os.path.join(HERE, "vision_labels.json"), "w") as f:
        json.dump({"labels": LABELS, "size": SIZE,
                   "held_out_accuracy": acc_va}, f, indent=1)
    print(f"wrote {args.out} ({os.path.getsize(args.out)} bytes)")


if __name__ == "__main__":
    main()
