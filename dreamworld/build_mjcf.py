"""Free the PuppyPi: URDF transform + dream-world build + first renders.

1. Delete the fixed base_joint and the empty base_footprint link, so
   base_link becomes the root and MuJoCo gives it a free joint.
2. Give base_link a real inertial (the stock URDF has none).
3. Add floor, light and position actuators via MjSpec; compile; settle
   the dog under physics for 2 s; render before/after frames.
"""
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from PIL import Image

SRC = "/home/hatch/workspace/hackathons/executorch-2026/dreamworld/model/puppy.urdf"
FREED = "/home/hatch/workspace/hackathons/executorch-2026/dreamworld/model/puppy_freed.urdf"
OUT = "/home/hatch/workspace/hackathons/executorch-2026/dreamworld/model/puppy_dream.xml"
PNG0 = "/home/hatch/workspace/hackathons/executorch-2026/dreamworld/dream-stand.png"
PNG1 = "/home/hatch/workspace/hackathons/executorch-2026/dreamworld/dream-settled.png"

tree = ET.parse(SRC)
robot = tree.getroot()
for el in list(robot):
    if el.tag == "joint" and el.get("name") == "base_joint":
        robot.remove(el)
    if el.tag == "link" and el.get("name") == "base_footprint":
        robot.remove(el)
for link in robot.iter("link"):
    if link.get("name") == "base_link" and link.find("inertial") is None:
        inertial = ET.SubElement(link, "inertial")
        ET.SubElement(inertial, "origin", {"xyz": "0 0 0", "rpy": "0 0 0"})
        ET.SubElement(inertial, "mass", {"value": "1.2"})
        ET.SubElement(inertial, "inertia", {
            "ixx": "0.008", "ixy": "0", "ixz": "0",
            "iyy": "0.014", "iyz": "0", "izz": "0.016"})
# An explicit floating joint on a dummy world link: this is what makes
# MuJoCo's URDF parser give base_link a free joint instead of welding it.
world = ET.SubElement(robot, "link", {"name": "world"})
floating = ET.SubElement(robot, "joint", {"name": "floating_base", "type": "floating"})
ET.SubElement(floating, "parent", {"link": "world"})
ET.SubElement(floating, "child", {"link": "base_link"})
ET.SubElement(floating, "origin", {"xyz": "0 0 0.11", "rpy": "0 0 0"})
tree.write(FREED)
print("freed URDF written")

spec = mujoco.MjSpec.from_file(FREED)
spec.visual.headlight.ambient = [0.45, 0.45, 0.5]
spec.visual.headlight.diffuse = [0.9, 0.9, 0.95]
spec.visual.headlight.specular = [0.35, 0.35, 0.35]
floor = spec.worldbody.add_geom()
floor.name = "floor"
floor.type = mujoco.mjtGeom.mjGEOM_PLANE
floor.size = [0, 0, 0.05]
floor.rgba = [0.3, 0.34, 0.46, 1]
light = spec.worldbody.add_light()
light.pos = [0.4, -0.5, 0.9]
light.dir = [-0.3, 0.4, -1]
light2 = spec.worldbody.add_light()
light2.pos = [-0.5, 0.4, 0.7]
light2.dir = [0.4, -0.3, -1]
light2.diffuse = [0.45, 0.45, 0.5]


def style(frame):
    for g in frame.geoms:
        if g.type == mujoco.mjtGeom.mjGEOM_MESH:
            g.rgba = [0.5, 0.58, 0.72, 1]
    for b in frame.bodies:
        style(b)


style(spec.worldbody)
def prm(*vals):
    a = np.zeros((10, 1))
    for i, v in enumerate(vals):
        a[i, 0] = v
    return a


for jname in ("lb_joint1", "lb_joint2", "rb_joint1", "rb_joint2",
              "rf_joint1", "rf_joint2", "lf_joint1", "lf_joint2"):
    act = spec.add_actuator()
    act.name = jname
    act.target = jname
    act.trntype = mujoco.mjtTrn.mjTRN_JOINT
    act.gaintype = mujoco.mjtGain.mjGAIN_FIXED
    act.gainprm = prm(40)
    act.biastype = mujoco.mjtBias.mjBIAS_AFFINE
    act.biasprm = prm(0, -40, -4)
    act.ctrlrange = [-2, 2]

model = spec.compile()
print("compiled: nq", model.nq, "nu", model.nu,
      "mass", round(float(model.body_mass.sum()), 2))
spec.to_file(OUT)
print("saved", OUT)

data = mujoco.MjData(model)
data.qpos[2] = 0.11
renderer = mujoco.Renderer(model, height=480, width=640)
cam = mujoco.MjvCamera()
cam.distance = 0.8
cam.azimuth = 130
cam.elevation = -16
cam.lookat = [0, 0, 0.08]

mujoco.mj_forward(model, data)
renderer.update_scene(data, camera=cam)
Image.fromarray(renderer.render()).save(PNG0)

data.ctrl[:] = 0.0
for _ in range(int(2.0 / model.opt.timestep)):
    mujoco.mj_step(model, data)
q = data.qpos
up_z = 1 - 2 * (q[4] ** 2 + q[5] ** 2)
print("after 2s: base z", round(float(q[2]), 3), "up_z", round(float(up_z), 3),
      "joint drift max", round(float(np.abs(q[7:]).max()), 3))
renderer.update_scene(data, camera=cam)
Image.fromarray(renderer.render()).save(PNG1)
print("rendered", PNG0, PNG1)
