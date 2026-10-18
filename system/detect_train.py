#!/usr/bin/env python3
"""
REM PhysicalAI — train the "which robot is this?" detector.

Same tiny CNN as the zone finder, but the classes are robots:
dataset_detect/<robot>/*.npy → detect.pte + detect_labels.json.
The live vision loop runs it next to the zone model: when it
recognizes a registered robot in the camera, the dashboard knows
which robot it is looking at — and can prepare to dream about it.

    python3 detect_train.py [--epochs 60]
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
SIZE = 64


class RobotIdNet(torch.nn.Module):
    def __init__(self, classes):
        super().__init__()
        self.features = torch.nn.Sequential(
            torch.nn.Conv2d(3, 16, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
            torch.nn.Conv2d(16, 32, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
            torch.nn.Conv2d(32, 32, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
        )
        self.classifier = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(32 * 8 * 8, 64), torch.nn.ReLU(),
            torch.nn.Linear(64, classes),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


def load(root):
    labels = sorted(d for d in os.listdir(root)
                    if os.path.isdir(os.path.join(root, d)))
    xs, ys = [], []
    for li, label in enumerate(labels):
        folder = os.path.join(root, label)
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".npy"):
                continue
            frame = np.load(os.path.join(folder, name))
            small = cv2.resize(frame, (SIZE, SIZE))
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            xs.append(torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0)
            ys.append(li)
    if not xs:
        raise SystemExit("dataset_detect is empty — run vision_ingest.py")
    return labels, torch.stack(xs), torch.tensor(ys, dtype=torch.long)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--dataset", default=os.path.join(HERE, "dataset_detect"))
    ap.add_argument("--out", default=os.path.join(HERE, "detect.pte"))
    args = ap.parse_args()

    torch.manual_seed(7)
    labels, x, y = load(args.dataset)
    counts = {labels[i]: int((y == i).sum()) for i in range(len(labels))}
    print(f"dataset: {len(x)} frames {counts}")
    idx = list(range(len(x)))
    random.Random(3).shuffle(idx)
    cut = max(1, int(0.8 * len(idx)))
    tr, va = idx[:cut], idx[cut:]

    model = RobotIdNet(len(labels))
    opt = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = torch.nn.CrossEntropyLoss()
    for epoch in range(args.epochs):
        model.train()
        opt.zero_grad()
        loss = loss_fn(model(x[tr]), y[tr])
        loss.backward()
        opt.step()
    model.eval()
    with torch.no_grad():
        acc_tr = (model(x[tr]).argmax(1) == y[tr]).float().mean().item()
        acc_va = (model(x[va]).argmax(1) == y[va]).float().mean().item() if va else float("nan")
    print(f"train acc {acc_tr:.3f} · held-out acc {acc_va:.3f} ({len(va)} frames)")

    exported = torch.export.export(model, (torch.randn(1, 3, SIZE, SIZE),))
    program = to_edge_transform_and_lower(
        exported, partitioner=[XnnpackPartitioner()]
    ).to_executorch()
    with open(args.out, "wb") as f:
        f.write(program.buffer)
    with open(os.path.join(HERE, "detect_labels.json"), "w") as f:
        json.dump({"labels": labels, "size": SIZE,
                   "held_out_accuracy": acc_va}, f, indent=1)
    print(f"wrote {args.out} ({os.path.getsize(args.out)} bytes) labels={labels}")


if __name__ == "__main__":
    main()
