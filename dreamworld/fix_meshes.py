#!/usr/bin/env python3
"""Export browser-ready STLs from the compiled MuJoCo model.

The Hiwonder STLs are authored in a different axis frame than the one
MuJoCo compiles them into (mjModel mesh_vert, after the asset frame is
applied). The web viewer skins the RAW files with body ∘ geom
transforms — mathematically exact for the compiled vertices (verified:
0.0000 m error), wrong for the raw ones, which made the twin render
disassembled. This script writes, for every mesh in puppy_dream.xml,
an STL whose vertices ARE the compiled ones. Originals are preserved
in meshes-original/.

    python3 fix_meshes.py
"""
import os
import shutil
import struct

import mujoco
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "model", "puppy_dream.xml")
MESH_DIR = os.path.join(HERE, "model", "meshes")
ORIG_DIR = os.path.join(HERE, "model", "meshes-original")


def write_stl(path, verts, faces):
    with open(path, "wb") as f:
        f.write(b"\0" * 80)
        f.write(struct.pack("<I", len(faces)))
        for tri in faces:
            a, b, c = (verts[i] for i in tri)
            n = np.cross(b - a, c - a)
            ln = np.linalg.norm(n)
            n = n / ln if ln > 0 else n
            f.write(struct.pack("<12fH", *(list(n) + list(a) + list(b) + list(c)), 0))


def main():
    os.makedirs(ORIG_DIR, exist_ok=True)
    m = mujoco.MjModel.from_xml_path(MODEL)
    for did in range(m.nmesh):
        name = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_MESH, did)
        src = os.path.join(MESH_DIR, name + ".STL")
        if os.path.exists(src) and not os.path.exists(os.path.join(ORIG_DIR, name + ".STL")):
            shutil.copy2(src, os.path.join(ORIG_DIR, name + ".STL"))
        va, vn = m.mesh_vertadr[did], m.mesh_vertnum[did]
        fa, fn = m.mesh_faceadr[did], m.mesh_facenum[did]
        verts = np.array(m.mesh_vert[va:va + vn])
        faces = np.array(m.mesh_face[fa:fa + fn])
        write_stl(src, verts, faces)
        print(f"{name}: {vn} verts, {fn} faces -> browser-ready STL")
    print("done — originals kept in meshes-original/")


if __name__ == "__main__":
    main()
