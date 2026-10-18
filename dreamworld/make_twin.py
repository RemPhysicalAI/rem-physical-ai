#!/usr/bin/env python3
"""
Build the browser twin: a self-contained MJCF for the local MuJoCo WASM
simulation. Identical bodies, joints, inertials and actuators to
puppy_dream.xml — only the mesh geoms become boxes (the bounding box of
each mesh's convex hull, placed exactly where the compiled model puts
the mesh), because a browser model must load from a single string with
no external files. The viewer still skins it with the real STL meshes.

    python3 make_twin.py   ->   model/puppy_twin.xml
"""
import os
import re

import mujoco
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "model", "puppy_dream.xml")
OUT = os.path.join(HERE, "model", "puppy_twin.xml")


def fmt(v):
    return " ".join(f"{float(x):.5g}" for x in v)


def main():
    model = mujoco.MjModel.from_xml_path(SRC)
    # Per mesh-geom: name -> (geom_pos, geom_quat, half extents in mesh frame)
    boxes = {}
    for g in range(model.ngeom):
        if model.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
            continue
        mid = int(model.geom_dataid[g])
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_MESH, mid)
        adr, num = int(model.mesh_vertadr[mid]), int(model.mesh_vertnum[mid])
        verts = model.mesh_vert[adr:adr + num]
        half = (verts.max(axis=0) - verts.min(axis=0)) / 2
        boxes[name] = (model.geom_pos[g], model.geom_quat[g], half)

    with open(SRC) as f:
        xml = f.read()
    # Drop the asset block (no external files in the twin).
    xml = re.sub(r"<asset>.*?</asset>", "", xml, flags=re.S)

    def swap(m):
        tag = m.group(0)
        name = re.search(r'mesh="([^"]+)"', tag).group(1)
        pos, quat, half = boxes[name]
        return (f'<geom type="box" size="{fmt(half)}" pos="{fmt(pos)}" '
                f'quat="{fmt(quat)}" rgba="0.5 0.58 0.72 1"/>')

    xml = re.sub(r'<geom[^>]*type="mesh"[^>]*/>', swap, xml)
    with open(OUT, "w") as f:
        f.write(xml)
    print("twin written:", OUT, len(xml), "bytes;",
          len(boxes), "mesh geoms -> boxes")


if __name__ == "__main__":
    main()
