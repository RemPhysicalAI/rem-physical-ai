# DreamRobot

![A robot dreaming under the moon](system/banner.jpg)

**A self-improvement system for any robot.**

> **Built for the Arduino Ventuno Q.** DreamRobot was designed for — and
> runs on — the **Arduino Ventuno Q**, Arduino's Qualcomm-powered board
> for physical AI. The Ventuno Q is **not yet on sale** (pre-order only);
> DreamRobot was developed and demonstrated on it at the ExecuTorch
> Hackathon (Founders, Inc., San Francisco, October 2026). When the
> board ships, DreamRobot ships with it.

DreamRobot is an independent learning layer that installs on a robot.
Give a robot three things — a way to **act**, a camera to **see**, and a
computer to **think** — and DreamRobot does the rest:

- **It learns by itself.** It commands actions, watches the results with
  its camera, and relates what it did to what it saw.
- **It is always learning.** Humans can teach it (poses, photos), and it
  keeps improving from its own experience.
- **It dreams while it sleeps.** When the robot is not being used, the
  self-learning engine rehearses variations of everything it knows,
  retrains its models on-device, verifies them against fixed probes,
  and keeps a new model only if it does not regress — the way a brain
  consolidates during sleep. It wakes up better than it went to sleep.
- **It tests itself in the mirror.** Facing a mirror, the robot commands
  itself, watches itself, and its vision must report what it did. The
  self-test score is how it knows the learning is real.

Everything runs **locally on the robot** — models are tiny ExecuTorch
programs (the reference pose model is 3,600 bytes and infers in under a
millisecond). No cloud, no connection, no data leaves the robot.

Built with PyTorch + ExecuTorch (open source). Reference host: an
Arduino Ventuno Q (Qualcomm Dragonwing IQ8 + STM32H5) running the
learning engine, with the Arduino Bridge carrying bounded commands to
the microcontroller that owns the actuators.

## Layout

- `system/` — the DreamRobot engine (robot-agnostic)
  - `dashboard.py` — the interface: eyes, beliefs, dreams, mirror test
  - `idle_learn.py` — the dream engine (rehearse → retrain → verify → keep)
  - `teach.py`, `train_model.py` — human teaching + on-device training
  - `vision.py`, `vision_train.py`, `vision_capture.py` — teach-by-camera
  - `rpc_client.py` — MsgPack-RPC client for the Arduino Router/Bridge
- `examples/walkersense/` — a disposable test robot (a $1 walker body):
  the MCU Bridge sketch and its seed posture dataset. Any other robot —
  an ODC-based walker, a different platform, or the Ventuno Q itself in
  front of a mirror — plugs into the same engine.

## Status

Engine proven live on hardware at the ExecuTorch Hackathon
(San Francisco, Oct 17–18, 2026): on-device inference + Bridge control,
human teach loop with on-device retraining, dream cycles running
continuously while idle, camera dataset collection and vision training.

## License

MIT — see `LICENSE`.
