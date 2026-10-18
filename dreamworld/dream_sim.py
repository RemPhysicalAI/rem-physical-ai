#!/usr/bin/env python3
"""
REM PhysicalAI — the dream itself: MuJoCo physics dreams of the PuppyPi.

Each dream is a physics rollout of the robot's digital twin: place the
twin in a situation (upright, tipped, pushed over, flipped), let physics
run, and record what its IMU would feel — the gravity vector and angular
velocity in the body frame, sampled along the fall/settle. Those are
dream training samples in exactly the format the posture brain eats
(6 features -> standing/walking/fallen/flipped), except they were
earned from physics instead of interpolation. The wake/sleep loop stays
the same: dreams feed training; probes verify; keep only if better.

    python3 dream_sim.py [--dreams 60] [--out dream_samples_mujoco.json]
"""
import argparse
import json
import math
import os
import random

import mujoco
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "model", "puppy_dream.xml")
CLASSES = ["standing", "walking", "fallen", "flipped"]


def quat_up_and_gravity(q):
    """Accelerometer reading in the body frame + up_z, from a wxyz quat.

    At rest an accelerometer measures proper acceleration: +1 g along
    body up when standing (the walkersense feature convention), -1 g
    when flipped. That vector is the third row of the rotation matrix.
    """
    w, x, y, z = q
    ax = 2 * (x * z - w * y)
    ay = 2 * (y * z + w * x)
    az = 1 - 2 * (x * x + y * y)
    return (ax, ay, az), az


def rollout(model, data, quat, z, seconds, push=None, rock=False,
            sample_every=0.05):
    mujoco.mj_resetData(model, data)
    data.qpos[0:3] = [0, 0, z]
    data.qpos[3:7] = quat
    data.ctrl[:] = 0.0
    base_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "base_link")
    steps = int(seconds / model.opt.timestep)
    every = max(1, int(sample_every / model.opt.timestep))
    feats = []
    for i in range(steps):
        if push is not None and i == steps // 3:
            data.qvel[0:3] = push
        if rock:
            # Real walking rocks the body on BOTH axes (~2 Hz pitch and
            # roll, phase-shifted, like a quadruped's gait), so the
            # gyroscope carries a true walking signature on every axis.
            # A pure slide feels identical to standing to an IMU —
            # because it is.
            t = i * model.opt.timestep
            data.xfrc_applied[base_body] = [
                0, 0, 0,
                1.0 * math.sin(2 * math.pi * 2.0 * t + math.pi / 2),
                1.2 * math.sin(2 * math.pi * 2.0 * t), 0]
        mujoco.mj_step(model, data)
        if i % every == 0 or i == steps - 1:
            (ax, ay, az), _ = quat_up_and_gravity(data.qpos[3:7])
            gx, gy, gz = data.qvel[3:6]
            feats.append([round(float(v), 4) for v in (ax, ay, az, gx, gy, gz)])
    return feats


def euler_quat(roll, pitch, yaw=0.0):
    cr, sr = math.cos(roll / 2), math.sin(roll / 2)
    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
    return [cy * cp * cr + sy * sp * sr, cy * cp * sr - sy * sp * cr,
            cy * sp * cr + sy * cp * sr, sy * cp * cr - cy * sp * sr]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dreams", type=int, default=60)
    ap.add_argument("--out", default=os.path.join(HERE, "dream_samples_mujoco.json"))
    args = ap.parse_args()
    rng = random.Random(20261017)
    model = mujoco.MjModel.from_xml_path(MODEL)
    data = mujoco.MjData(model)

    scenarios = {
        # class: (quat, z, seconds, push, rock) builders
        "standing": lambda: (euler_quat(rng.uniform(-0.06, 0.06),
                                        rng.uniform(-0.06, 0.06)), 0.11, 1.2, None, False),
        "walking": lambda: (euler_quat(0, 0), 0.11, 1.2,
                            [rng.uniform(0.2, 0.5), 0, 0], True),
        "fallen": lambda: (euler_quat(math.radians(90) + rng.uniform(-0.15, 0.15),
                                      rng.uniform(-0.1, 0.1)), 0.07, 1.2, None, False),
        "flipped": lambda: (euler_quat(math.pi + rng.uniform(-0.12, 0.12),
                                        rng.uniform(-0.1, 0.1)), 0.07, 1.2, None, False),
    }

    samples = []
    per = max(1, args.dreams // len(CLASSES))
    for label, name in enumerate(CLASSES):
        for _ in range(per):
            quat, z, secs, push, rock = scenarios[name]()
            for feats in rollout(model, data, quat, z, secs, push, rock):
                samples.append({"features": feats, "label": label,
                                "source": "dream-mujoco"})
    rng.shuffle(samples)
    with open(args.out, "w") as f:
        json.dump(samples, f)
    counts = {name: sum(1 for s in samples if s["label"] == i)
              for i, name in enumerate(CLASSES)}
    print(f"dreamed {len(samples)} physics samples -> {args.out}")
    print("per class:", counts)


if __name__ == "__main__":
    main()
