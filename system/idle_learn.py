#!/usr/bin/env python3
"""
WalkerSense idle self-learning — "dream, verify, keep what works".

While the robot has nothing to do, it rehearses internally:
  1. DREAM: build rehearsal samples from its own memory — interpolations
     between same-pose experiences ("what if I tipped between these two?")
     plus harder sensor noise than it was originally trained with.
  2. RETRAIN a candidate model on memory + dreams, entirely on-device.
  3. VERIFY the candidate against a fixed probe set (canonical poses +
     every pose a human taught it). Keep the candidate ONLY if it does
     not regress: probe accuracy must not drop and mean confidence must
     not fall by more than a small epsilon. Otherwise discard it.
  4. LOG the cycle to state.json + events.log for the dashboard.

Nothing is ever unlearned silently: a kept swap preserves the previous
model as model.prev.pte, and every cycle — kept or not — is on the record.

    python3 idle_learn.py [--cycles N] [--interval SECONDS]
"""
import argparse
import itertools
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "samples.json")
MODEL = os.path.join(HERE, "model.pte")
STATE = os.path.join(HERE, "state.json")
EVENTS = os.path.join(HERE, "events.log")
DREAM = os.path.join(HERE, "dream_samples.json")
CANDIDATE = os.path.join(HERE, "model.candidate.pte")
CLASSES = ["standing", "walking", "fallen", "flipped"]

# Fixed probes: (name, expected class, features). Includes the pose a
# human taught the robot (tipped45) — self-learning must never undo teaching.
PROBES = [
    ("standing", "standing", [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]),
    ("walking", "walking", [0.15, 0.1, 0.95, 0.6, 0.2, 0.1]),
    ("fallen (side)", "fallen", [1.0, 0.0, 0.05, 0.0, 0.0, 0.0]),
    ("tipped 45° (taught)", "fallen", [0.7, 0.05, 0.7, 0.0, 0.0, 0.0]),
    ("flipped", "flipped", [0.0, 0.05, -1.0, 0.0, 0.0, 0.0]),
]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log_event(kind, detail):
    with open(EVENTS, "a") as f:
        f.write(json.dumps({"at": now(), "kind": kind, "detail": detail}) + "\n")


def evaluate(model_path):
    """Run the probe set through a .pte; return per-probe results + summary."""
    import torch
    from executorch.runtime import Runtime

    runtime = Runtime.get()
    method = runtime.load_program(model_path).load_method("forward")
    results, correct, conf_sum = [], 0, 0.0
    for name, expected, features in PROBES:
        scores = method.execute([torch.tensor([features], dtype=torch.float32)])[0][0]
        probs = torch.softmax(scores, dim=0)
        pose = CLASSES[int(torch.argmax(probs))]
        conf = float(probs[CLASSES.index(expected)])
        ok = pose == expected
        correct += ok
        conf_sum += conf
        results.append(
            {"name": name, "expected": expected, "pose": pose,
             "confidence": round(conf, 3), "ok": ok}
        )
    return results, correct / len(PROBES), conf_sum / len(PROBES)


def build_dreams(samples, rng):
    """The dream source: MuJoCo physics dreams of the robot's twin.

    dream_sim.py rolls the twin through standing/walking/fallen/flipped
    in the 3D physics world and records what its IMU would feel; those
    are the dreams the brain trains on. (Fallback, only if the MuJoCo
    dream file is missing: interpolate between same-class memories.)
    """
    mujoco_dreams = os.path.join(HERE, "..", "dreamworld",
                                 "dream_samples_mujoco.json")
    if os.path.exists(mujoco_dreams):
        with open(mujoco_dreams) as f:
            dreams = json.load(f)
        rng.shuffle(dreams)
        return dreams
    dreams = []
    by_class = {}
    for s in samples:
        by_class.setdefault(int(s["label"]), []).append(s["features"])
    for label, feats in by_class.items():
        for a, b in itertools.combinations(feats, 2):
            for alpha in (0.33, 0.66):
                mixed = [round(alpha * x + (1 - alpha) * y, 4) for x, y in zip(a, b)]
                dreams.append({"features": mixed, "label": label, "source": "dream"})
    rng.shuffle(dreams)
    return dreams


def write_state(cycles, last, probe_results, acc, conf):
    with open(SAMPLES) as f:
        samples = json.load(f)
    state = {
        "updated": now(),
        "model": {
            "size_bytes": os.path.getsize(MODEL),
            "updated": datetime.fromtimestamp(
                os.path.getmtime(MODEL), timezone.utc
            ).isoformat(timespec="seconds"),
        },
        "dataset": {
            "base": sum(1 for s in samples if s.get("source") != "taught"),
            "taught": sum(1 for s in samples if s.get("source") == "taught"),
            "total": len(samples),
        },
        "probes": probe_results,
        "probe_accuracy": acc,
        "probe_confidence": round(conf, 3),
        "idle": {"cycles": cycles, "last": last},
    }
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=1)
    os.replace(tmp, STATE)


def one_cycle(cycle_no):
    with open(SAMPLES) as f:
        samples = json.load(f)
    rng = random.Random(1000 + cycle_no)
    dreams = build_dreams(samples, rng)
    with open(DREAM, "w") as f:
        json.dump(samples + dreams, f, indent=1)

    _, acc_before, conf_before = evaluate(MODEL)
    result = subprocess.run(
        [sys.executable, os.path.join(HERE, "train_model.py"),
         "--samples", DREAM, "--noise", "0.12", "--out", CANDIDATE],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log_event("idle-cycle", f"cycle {cycle_no}: training failed, model kept")
        return {"cycle": cycle_no, "kept": False, "reason": "train failed"}
    probe_results, acc_after, conf_after = evaluate(CANDIDATE)

    keep = acc_after >= acc_before and conf_after >= conf_before - 0.02
    detail = (
        f"cycle {cycle_no}: dreamed {len(dreams)} rehearsals; "
        f"probes acc {acc_before:.2f}->{acc_after:.2f}, "
        f"conf {conf_before:.3f}->{conf_after:.3f}; "
        + ("model KEPT (improved or held)" if keep else "candidate discarded (would regress)")
    )
    if keep:
        os.replace(MODEL, os.path.join(HERE, "model.prev.pte"))
        os.replace(CANDIDATE, MODEL)
    else:
        os.remove(CANDIDATE)
    log_event("idle-cycle", detail)
    last = {"at": now(), "cycle": cycle_no, "dreamed": len(dreams),
            "kept": keep, "acc_before": acc_before, "acc_after": acc_after,
            "conf_before": round(conf_before, 3), "conf_after": round(conf_after, 3)}
    write_state(cycle_no, last, probe_results, acc_after, conf_after)
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=0, help="0 = run forever")
    ap.add_argument("--interval", type=float, default=20.0)
    args = ap.parse_args()
    cycle = 0
    # Publish an initial state so the dashboard has data before cycle 1 ends.
    results, acc, conf = evaluate(MODEL)
    write_state(0, None, results, acc, conf)
    log_event("idle-start", "self-learning started")
    while True:
        cycle += 1
        last = one_cycle(cycle)
        print(f"[{last['at']}] cycle {cycle}: kept={last.get('kept')} "
              f"acc {last.get('acc_before')}->{last.get('acc_after')} "
              f"conf {last.get('conf_before')}->{last.get('conf_after')}", flush=True)
        if args.cycles and cycle >= args.cycles:
            break
        time.sleep(args.interval)
    log_event("idle-stop", f"self-learning stopped after {cycle} cycles")


if __name__ == "__main__":
    main()
