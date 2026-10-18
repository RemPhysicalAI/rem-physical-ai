# Project: PuppyPi — the robot under test

The saved test project for the ExecuTorch Hackathon (Oct 18, 2026).
The robot is a Hiwonder PuppyPi (another team's robot dog). REM
PhysicalAI cannot drive it — so this is a **dream-only** project:

- the **camera** on the Ventuno Q watches it;
- a **detector** (`detect.pte`, trained from photos of the real
  robot) recognizes it in view;
- its **physics twin** lives on the dream stage — the system dreams
  about the PuppyPi and trains it virtually, in simulation.

Everything about the project is in `project.json`: the plugs it
uses, the control mode, its plugins, its dream files, and what it
has learned. The twin and meshes live in `../../dreamworld/model/`;
the real-robot photos used across the presentation live in
`../../about/`.

Plugins for this project go in `plugins/` — software accessories
that extend what the system can do with this robot.
