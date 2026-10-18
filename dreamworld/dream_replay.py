#!/usr/bin/env python3
"""
DreamRobot — record the dream as DATA, not video.

Rolls the twin through a dream montage (standing -> walking -> fallen
-> flipped) in the physics simulation and records, 20 times a second,
the world pose (position + quaternion) of every body. The viewer
rebuilds and replays the dream locally from this data alone — a few
dozen KB instead of a video stream, so there is no delay.

    python3 dream_replay.py [--out /home/arduino/walkersense/dream_replay.json]
"""
import argparse
import json
import math
import os

import mujoco

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "model", "puppy_dream.xml")
FPS = 20


def parts_and_bodies(model):
    bodies, parts = [], []
    for i in range(1, model.nbody):
        bodies.append(mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i))
    for g in range(model.ngeom):
        if model.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
            continue
        parts.append({
            "body": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY,
                                      int(model.geom_bodyid[g])),
            "mesh": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_MESH,
                                      int(model.geom_dataid[g])),
            "pos": [round(float(v), 4) for v in model.geom_pos[g]],
            "quat": [round(float(v), 4) for v in model.geom_quat[g]],
        })
    return bodies, parts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/home/arduino/walkersense/dream_replay.json")
    args = ap.parse_args()
    model = mujoco.MjModel.from_xml_path(MODEL)
    data = mujoco.MjData(model)
    bodies, parts = parts_and_bodies(model)
    base = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "base_link")
    dt = model.opt.timestep
    every = max(1, int(1.0 / FPS / dt))

    def quat(roll):
        return [math.cos(roll / 2), math.sin(roll / 2), 0, 0]

    # scene: (name, start pos, start quat, seconds, mode)
    scenes = [
        ("standing", [0, 0, 0.11], quat(0.03), 1.2, None),
        ("walking", [0, 0, 0.11], quat(0.0), 2.4, "walk"),
        ("fallen", [0, 0, 0.07], quat(math.radians(90)), 1.8, None),
        ("flipped", [0, 0, 0.07], quat(math.pi), 1.8, None),
    ]
    frames = []
    for name, pos, q, seconds, mode in scenes:
        mujoco.mj_resetData(model, data)
        data.qpos[0:3] = pos
        data.qpos[3:7] = q
        data.ctrl[:] = 0.0
        steps = int(seconds / dt)
        for i in range(steps):
            if mode == "walk":
                t = i * dt
                data.xfrc_applied[base] = [
                    0, 0, 0,
                    1.0 * math.sin(2 * math.pi * 2.0 * t + math.pi / 2),
                    1.2 * math.sin(2 * math.pi * 2.0 * t), 0]
                if i == steps // 4:
                    data.qvel[0] += 0.9
            mujoco.mj_step(model, data)
            if i % every == 0:
                frames.append({
                    "scene": name,
                    "bodies": [[round(float(v), 4) for v in
                                list(data.xpos[b]) + list(data.xquat[b])]
                               for b in range(1, model.nbody)],
                })
    payload = {"fps": FPS, "bodies": bodies, "parts": parts, "frames": frames}
    with open(args.out, "w") as f:
        json.dump(payload, f)
    print(f"dream recorded: {len(frames)} frames, "
          f"{os.path.getsize(args.out)} bytes -> {args.out}")


if __name__ == "__main__":
    main()
