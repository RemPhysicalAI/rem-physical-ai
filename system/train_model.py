#!/usr/bin/env python3
"""
Train the WalkerSense pose classifier and export it to ExecuTorch (.pte).

Features: 6 IMU-style values (ax, ay, az, gx, gy, gz).
Classes:  0 standing | 1 walking | 2 fallen | 3 flipped

Training data comes from samples.json: a list of {"features": [6 floats],
"label": int}. The seed file ships with physics prototypes (gravity along
+Z = standing, along X/Y = fallen on a side, along -Z = flipped, plus
gyro activity for walking) with noise augmentation applied here.

The same script runs on the laptop and on the board itself — on-device
retraining after teaching is literally: append samples, re-run, reload.

    python3 train_model.py [--samples samples.json] [--out model.pte]
"""
import argparse
import json
import os

import torch
from executorch.exir import to_edge_transform_and_lower
from executorch.backends.xnnpack.partition.xnnpack_partitioner import XnnpackPartitioner

torch.manual_seed(42)


class WalkerPoseNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(6, 16),
            torch.nn.ReLU(),
            torch.nn.Linear(16, 4),
        )

    def forward(self, x):
        return self.net(x)


def load_dataset(path, augment=40, noise=0.08):
    with open(path) as f:
        samples = json.load(f)
    xs, ys = [], []
    gen = torch.Generator().manual_seed(1234)
    for s in samples:
        base = torch.tensor(s["features"], dtype=torch.float32)
        for _ in range(augment):
            xs.append(base + torch.randn(6, generator=gen) * noise)
            ys.append(int(s["label"]))
    return torch.stack(xs), torch.tensor(ys, dtype=torch.long)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", default=os.path.join(here, "samples.json"))
    ap.add_argument("--out", default=os.path.join(here, "model.pte"))
    ap.add_argument("--epochs", type=int, default=300)
    ap.add_argument("--augment", type=int, default=40)
    ap.add_argument("--noise", type=float, default=0.08)
    args = ap.parse_args()

    x, y = load_dataset(args.samples, augment=args.augment, noise=args.noise)
    model = WalkerPoseNet()
    opt = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = torch.nn.CrossEntropyLoss()
    for epoch in range(args.epochs):
        opt.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        opt.step()
    with torch.no_grad():
        acc = (model(x).argmax(1) == y).float().mean().item()
    print(f"trained on {len(x)} samples, train accuracy {acc:.3f}")

    model = model.eval()
    exported = torch.export.export(model, (torch.randn(1, 6),))
    program = to_edge_transform_and_lower(
        exported, partitioner=[XnnpackPartitioner()]
    ).to_executorch()
    with open(args.out, "wb") as f:
        f.write(program.buffer)
    print(f"wrote {args.out} ({os.path.getsize(args.out)} bytes)")


if __name__ == "__main__":
    main()
