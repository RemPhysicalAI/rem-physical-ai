#!/usr/bin/env python3
"""
REM PhysicalAI — make the twin's physics feel like Earth.

The URDF conversion left three things wrong for a 1.5 kg robot dog:
  * joint force capped at 0.5 N·m — the legs cannot hold the body,
    so it sinks and sways in slow motion ("moon gravity");
  * stock soft contacts (solref 0.02) — landings bounce like foam;
  * 10 g upper legs — a real coreless servo alone weighs ~55 g.

Tunes both models (dream + browser twin) identically: force range
±3 N·m, position gain 40→80 / damping 4→8, firm contacts, and a
believable mass distribution (total stays ≈1.53 kg, the real
PuppyPi's weight class), inertias scaled with their masses.

    python3 tune_physics.py [model.xml ...]
"""
import sys
import xml.etree.ElementTree as ET

MASS = {"base_link": 1.13}
for leg in ("lb", "rb", "rf", "lf"):
    MASS[f"{leg}_link1"] = 0.06   # upper leg + its servo
    MASS[f"{leg}_link2"] = 0.04   # lower leg


def tune(path):
    tree = ET.parse(path)
    root = tree.getroot()

    # firm ground: one <default> for all geoms
    default = root.find("default")
    if default is None:
        default = ET.Element("default")
        root.insert(1, default)
    geom = default.find("geom")
    if geom is None:
        geom = ET.SubElement(default, "geom")
    geom.set("solimp", "0.9 0.95 0.001")
    geom.set("solref", "0.005 1")
    geom.set("friction", "1.0 0.005 0.0001")

    for joint in root.iter("joint"):
        if joint.get("actuatorfrcrange"):
            joint.set("actuatorfrcrange", "-3 3")
        if joint.get("type") != "free" and joint.get("name") != "floating_base":
            joint.set("damping", "0.35")
            joint.set("armature", "0.01")
    for act in root.iter("general"):
        act.set("gainprm", "80")
        act.set("biasprm", "0 -80 -12")

    total = 0.0
    for body in root.iter("body"):
        name = body.get("name")
        inertial = body.find("inertial")
        if inertial is None or name not in MASS:
            continue
        old = float(inertial.get("mass"))
        new = MASS[name]
        k = new / old
        inertial.set("mass", f"{new:.4f}")
        if inertial.get("diaginertia"):
            vals = [float(v) * k for v in inertial.get("diaginertia").split()]
            inertial.set("diaginertia", " ".join(f"{v:.6g}" for v in vals))
        total += new
    tree.write(path, xml_declaration=False)
    print(f"{path}: tuned (force ±3 N·m, gain 80/8, firm contacts, "
          f"tuned bodies total {total:.2f} kg)")


if __name__ == "__main__":
    for p in sys.argv[1:] or ["model/puppy_dream.xml", "model/puppy_twin.xml"]:
        tune(p)
