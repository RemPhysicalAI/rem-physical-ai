#!/usr/bin/env python3
"""
WalkerSense — on-device loop on the Ventuno Q (Linux side).

    sensor features (ax, ay, az, gx, gy, gz)
      -> ExecuTorch model (.pte, runs 100% on this board, offline)
      -> pose class: standing | walking | fallen | flipped
      -> action on the MCU via Arduino Bridge (LED matrix ack today,
         servo gaits on the same calls once wired)

Run the four built-in posture scenarios through the real model and fire
the matching MCU action for each:

    python3 walkersense.py [--model model.pte] [--scenario fallen]

Latency printed per scenario is input-to-action: inference time plus the
first Bridge call that starts the visible response.
"""
import argparse
import os
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpc_client import Bridge, BridgeError  # noqa: E402

CLASSES = ["standing", "walking", "fallen", "flipped"]

# Clean posture prototypes (gravity in g, gyro in rad/s).
SCENARIOS = {
    "standing": [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    "walking": [0.15, 0.1, 0.95, 0.6, 0.2, 0.1],
    "fallen": [1.0, 0.0, 0.05, 0.0, 0.0, 0.0],
    "flipped": [0.0, 0.05, -1.0, 0.0, 0.0, 0.0],
}


def act(bridge, pose):
    """Map a pose class to a bounded MCU response. Returns action name."""
    if pose == "walking":
        bridge.call("matrix_fill", True)
        return "matrix ON (walking)"
    if pose == "standing":
        bridge.call("matrix_fill", False)
        return "matrix OFF (standing)"
    blinks = 3 if pose == "fallen" else 5
    period = 0.25 if pose == "fallen" else 0.12
    for _ in range(blinks):
        bridge.call("matrix_fill", True)
        time.sleep(period)
        bridge.call("matrix_fill", False)
        time.sleep(period)
    return f"matrix blink x{blinks} ({pose})"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.path.join(here, "model.pte"))
    ap.add_argument("--scenario", choices=list(SCENARIOS), default=None)
    args = ap.parse_args()

    from executorch.runtime import Runtime

    runtime = Runtime.get()
    method = runtime.load_program(args.model).load_method("forward")
    print(f"model loaded: {args.model}")

    try:
        bridge = Bridge()
        bridge.call("matrix_fill", False)  # bridge liveness check
    except Exception as e:
        print(f"Bridge not reachable ({e}); running inference only.")
        bridge = None

    names = [args.scenario] if args.scenario else list(SCENARIOS)
    for name in names:
        features = torch.tensor([SCENARIOS[name]], dtype=torch.float32)
        t0 = time.perf_counter()
        scores = method.execute([features])[0][0]
        t_infer = time.perf_counter()
        probs = torch.softmax(scores, dim=0)
        pose = CLASSES[int(torch.argmax(probs))]
        action = "—"
        if bridge is not None:
            action = act(bridge, pose)
        t_end = time.perf_counter()
        print(
            f"input={name:9s} -> pose={pose:9s} "
            f"probs={[round(float(p), 2) for p in probs]} "
            f"infer={(t_infer - t0) * 1000:.1f}ms "
            f"input-to-action={(t_end - t0) * 1000:.1f}ms action: {action}"
        )
        time.sleep(0.4)


if __name__ == "__main__":
    main()
