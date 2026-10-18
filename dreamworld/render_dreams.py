#!/usr/bin/env python3
"""
REM PhysicalAI — render the dream.

Renders the three MuJoCo dream scenes (standing, fallen, flipped) with
the robot's own renderer, into the interface folder. Run on the board:

    MUJOCO_GL=osmesa python3 render_dreams.py
"""
import math
import os

import mujoco
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "model", "puppy_dream.xml")
OUT_DIR = "/home/arduino/walkersense"

SCENES = {
    "dream_stand.jpg": ([0, 0, 0.11], [1, 0, 0, 0]),
    "dream_fallen.jpg": ([0, 0, 0.07],
                         [math.cos(math.radians(45)), math.sin(math.radians(45)), 0, 0]),
    "dream_flipped.jpg": ([0, 0, 0.07], [0, 1, 0, 0]),
}


def main():
    model = mujoco.MjModel.from_xml_path(MODEL)
    data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=480, width=640)
    cam = mujoco.MjvCamera()
    cam.distance = 0.8
    cam.azimuth = 130
    cam.elevation = -16
    cam.lookat = [0, 0, 0.07]
    for name, (pos, quat) in SCENES.items():
        mujoco.mj_resetData(model, data)
        data.qpos[0:3] = pos
        data.qpos[3:7] = quat
        data.ctrl[:] = 0.0
        for _ in range(int(1.5 / model.opt.timestep)):
            mujoco.mj_step(model, data)
        renderer.update_scene(data, camera=cam)
        out = os.path.join(OUT_DIR, name)
        Image.fromarray(renderer.render()).save(out, quality=88)
        print("rendered", out)


if __name__ == "__main__":
    main()
