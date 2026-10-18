# How it works

REM PhysicalAI in plain words.

## The problem

A robot is only as smart as the day it left the factory. Teaching it
something new means an engineer, a lab, and a new software release.
REM PhysicalAI gives the robot a way to keep learning on its own —
safely, on the device, for the rest of its life.

## Three plugs

REM PhysicalAI is not a robot. It is a learning system that installs
**on** a robot. A host robot gives it three plugs:

- **Act** — a way to do things (motors, an LED matrix, a buzzer…)
- **See** — a camera and simple body sensors (which way is up, how
  fast it is turning)
- **Think** — a computer to run the learning (the Ventuno Q)

WalkerSense (a $1 walker body on a Ventuno Q) is the first host.
A robot dog, a humanoid, or the Ventuno Q itself in front of a mirror
can be the next.

## The five states

**Awake.** The robot feels its body — gravity and rotation, six
numbers — and a tiny learned model tells it what is happening:
standing, walking, fallen, flipped. It answers in milliseconds and
acts through its plugs (for example, lighting its LED matrix).

**Teach.** A human shows it something new: a pose it got wrong, photos
of an object from different positions. The system adds the example to
its memory and **retrains itself on the device** — under a minute,
no cloud, no engineer. What was taught is never silently unlearned
(see the rule below).

**Dream.** When nobody is using the robot, it dreams. A physics
simulation holds its digital twin; the twin stands, walks, falls and
flips thousands of times, and every imagined experience becomes
training data. The robot retrains on its dreams, then **verifies**
itself against fixed probes — poses it must always get right,
including everything a human taught it.

> **The keep rule:** a dreamed model replaces the old one only if the
> probes do not regress. Otherwise it is discarded. The robot can
> dream freely because it can never wake up worse.

**Mirror.** Learning claims are cheap; the mirror is the judge. The
robot commands itself, watches itself with its camera, and its vision
must report what it actually did. The self-test score is public on
the dashboard.

**Voice.** A small language model runs on the device. Asked about
itself, the robot answers from its real state — how many dreams it
had, what it has been taught, how sure it is — never from a script.

## Dreams are data, not video

The dream is a simulation, so the interface never streams video. The
robot sends **data** — the model, and what the dream is doing — and
your browser runs the same physics simulation locally to show it.
That is why the dashboard feels instant, and why it would work over
almost any connection.

## Small on purpose

Everything is tiny and local by design: the pose model that runs the
body is 3,600 bytes and decides in under a millisecond; training
happens on the robot; the largest component, the voice, is a 0.6B
model running fully offline. Physical AI does not need a data center.
It needs a body, a dream, and time.

## One system, many robots

REM PhysicalAI is not built for one robot — it is a system that many
robots (many *projects*) plug into. Every session starts the same way:

1. **The camera opens.** It is the front door of the system.
2. **It detects and identifies the robot in view.** The system knows
   which robot it is looking at — each robot is a registered project
   (`system/projects.json`).
3. **If it can control that robot, it controls it.** The host body on
   the board is commanded for real, through the Bridge.
4. **If it cannot, it dreams about it.** A robot this system cannot
   drive — like the PuppyPi at this event, another team's robot — gets
   a physics twin: the system rehearses with the twin on the dream
   stage and trains it virtually, ready for the real thing.

The dashboard's Projects panel shows this live: every registered
robot, its mode (⚙️ full control / 🌙 dream only), and which one the
camera is looking at right now.

## Adding robots, configuring control, plugins

- **Add project** — the dashboard's Projects panel takes a new robot
  in seconds; it is saved in the registry (`system/projects.json`)
  and gets its own folder under `projects/` with everything it has
  learned.
- **Detect** — the system identifies the robot in front of the camera
  with a small on-device detector (`detect.pte`), trained from
  ordinary photos: upload a photo, it is multiplied into a training
  set (`vision_ingest.py`), and the board trains the detector itself
  (`detect_train.py`).
- **Configure control** — each project declares how the system may
  treat its robot: ⚙️ full control (it commands the body), 🌙 dream
  only (it dreams and trains virtually), or 📷 camera only.
- **Plugins** — software accessories: a project carries a list of
  plugins that extend what the system can do with that robot, added
  from the same panel. Hardware has accessories; here, software does.
