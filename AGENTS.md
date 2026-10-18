# AGENTS.md — REM PhysicalAI

Instructions for any AI coding agent (or human) working in this repo or
deploying this system on an Arduino Ventuno Q. Read this first; it is
the contract. Everything here is verified on real hardware.

## What this is

REM PhysicalAI is a self-learning system that installs on a robot: it
learns by itself, dreams in a physics simulation while idle, verifies
every new model against fixed probes, and keeps a change only if it
does not regress. The reference host is WalkerSense on an **Arduino
Ventuno Q** (Linux side: Qualcomm Dragonwing IQ8; MCU side: STM32H5
running an Arduino Bridge sketch). All inference is on-device
(ExecuTorch). No cloud.

## Repo map

- `system/` — the engine, copied to `~/walkersense/` on the board
  - `dashboard.py` — web interface + chat + dream viewer, port 8080
  - `idle_learn.py` — the dream engine (dream → retrain → verify → keep)
  - `teach.py` / `train_model.py` — human teaching, on-device training
  - `walkersense.py` — the live posture loop (sense → infer → act)
  - `vision*.py` — teach-by-camera (capture / train / live)
  - `voice.py` — the robot's voice (optional Qwen3 model, see SETUP)
  - `rpc_client.py` — MsgPack-RPC client for the Arduino Bridge
- `dreamworld/` — the dream: MuJoCo model of the robot twin
  (`model/puppy_dream.xml`, browser twin `model/puppy_twin.xml`),
  `dream_sim.py` (physics dream data), `dream_replay.py` (a dream as
  data), `render_dreams.py`, `make_twin.py`, `build_mjcf.py`
- `examples/walkersense/` — the Bridge sketch (`walker_bridge/`) + the
  seed posture dataset (`samples.json`)
- `projects/` — one folder per host robot (`project.json` registry)
- `docs/` — human docs (`HOW-IT-WORKS.md`, `SETUP.md`, `COMMANDS.md`,
  `FOR-AGENTS.md`)

## Deploy on a Ventuno Q (the fast path)

```bash
git clone https://github.com/RemPhysicalAI/rem-physical-ai.git
cd rem-physical-ai
./quickstart.sh        # venv + runtime + engine + first dreams + services
```

Then flash the Bridge sketch **once, over the serial port** (network
upload does not work non-interactively):

```bash
arduino-cli compile --fqbn arduino:zephyr:ventunoq examples/walkersense/walker_bridge
arduino-cli upload  --fqbn arduino:zephyr:ventunoq -p /dev/ttyACM0 examples/walkersense/walker_bridge
```

Verify: open `http://<board>:8080` — eyes, dream, beliefs, chat.
Chat `acende` must light the real LED matrix; `caminhe` walks in the
dream. See `docs/FOR-AGENTS.md` for the full verification checklist
with expected outputs.

## Board facts (do not rediscover these)

- Python venv: `~/et-venv` (Python 3.12). Install `torch` **and**
  `executorch` together — executorch does not pull torch.
- Board needs `libatomic1` (Qwen runner) and `libosmesa6` +
  `MUJOCO_GL=osmesa` for headless MuJoCo rendering.
- The Bridge lives on a unix socket (`/var/run/arduino-router.sock`),
  MsgPack-RPC. Use `system/rpc_client.py` (`Bridge().call(method,
  *args)`). Do **not** use `arduino-router-cli` (it crashes on
  responses) and do not talk to `/dev/ttyACM0` directly for RPC.
- Bridge methods from the sketch: `matrix_fill(bool)`,
  `servo_set(pin, pulse_us)` (clamped 500–2500 µs), `servo_run(frames)`
  (software 20 ms frames, max 100), `servo_stop()`. An error like
  `[2, 'method X not available']` means the sketch is not flashed.
- Servo pulses are software-generated on purpose — the core's
  `analogWrite` depends on devicetree PWM period; do not "fix" it.
- Power: servos on their own pack/BEC with common ground. A 5 V/3 A
  power bank will not hold the board under AI load.

## Invariants (never break these)

- **The keep rule:** a retrained model replaces the live one only if
  fixed probes (including every human-taught example) do not regress
  and mean confidence drops ≤ 0.02. Keep the previous model as
  `model.prev.pte`. Teaching and dreaming must never silently unlearn.
- **Bounded MCU:** Linux decides, the MCU executes bounded commands
  and owns actuator limits. Keep Bridge callbacks short.
- **Honesty:** never claim NPU acceleration without profiling output;
  never invent metrics. Report measured numbers only.
- **Docs are plain language, concepts first** — the public docs carry
  no jargon dumps. Code comments may be technical.
- The public repo holds the generic system only. No product IP, no
  credentials, no tokens — ever.

## Working agreements

- After changing `system/*.py`, sync the copies an installed board
  runs from `~/walkersense/` and restart the affected service
  (`dashboard.py`, `idle_learn.py` — plain background processes).
- The dashboard serves the dream as **data** (simulation runs in the
  viewer's browser via the official MuJoCo WASM bindings, same
  version as the board). Do not replace it with video streaming.
- Models: pose model is a tiny MLP exported to `.pte` (XNNPACK,
  3,600 bytes, sub-ms inference). Re-export through
  `train_model.py`; never hand-edit `.pte` files.
