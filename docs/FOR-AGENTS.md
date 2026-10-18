# Implement REM PhysicalAI with an agent

You have an AI coding agent (Codex, Cursor, Copilot, Muse…) and a
Ventuno Q. This page takes the two of you from zero to a dreaming
robot, fast. Give the agent this repository — `AGENTS.md` at the root
is written for it — and follow the steps together.

## Step 0 · Point your agent at the repo

Paste this to your agent:

> Clone https://github.com/RemPhysicalAI/rem-physical-ai and read
> `AGENTS.md` and `docs/FOR-AGENTS.md` in full. You are deploying REM
> PhysicalAI on my Arduino Ventuno Q. Follow the steps exactly,
> verify each one with the checklist, and report measured results
> only. Ask me before anything destructive or anything that changes
> the robot's live model.

## Step 1 · Prepare the board (agent runs, you watch)

On the board (SSH, user `arduino`):

```bash
git clone https://github.com/RemPhysicalAI/rem-physical-ai.git
cd rem-physical-ai
./quickstart.sh
```

Expected: it ends with `== Dreaming. Open the dashboard:
http://<board-ip>:8080 ==`. The script installs the Python runtime
(PyTorch + ExecuTorch), places the engine in `~/walkersense`, builds
the first physics dreams, and starts the dashboard + dream engine.
Re-running it is safe.

## Step 2 · Flash the body (you plug in, agent uploads)

The microcontroller sketch is what lets the brain reach the LED
matrix and servos. USB cable connected, then:

```bash
arduino-cli compile --fqbn arduino:zephyr:ventunoq examples/walkersense/walker_bridge
arduino-cli upload  --fqbn arduino:zephyr:ventunoq -p /dev/ttyACM0 examples/walkersense/walker_bridge
```

Upload **only** via the serial port — network upload aborts in
non-interactive sessions. This is in `AGENTS.md` so your agent will
not waste your afternoon rediscovering it.

## Step 3 · Verify together (the checklist)

Open `http://<board-ip>:8080` and check, in order:

1. **The page loads** — eyes, dream, beliefs, dreaming, chat cards.
   The dream canvas says **"live simulation"** (your browser is
   running the physics). "Recorded dream data" also passes (fallback).
2. **Chat: `acende`** → the board's real LED matrix lights up.
   `apaga` turns it off. (This proves Linux → Bridge → MCU.)
3. **Chat: `caminhe`** → the twin walks in the dream.
   `cai` it falls, `vira` it flips, `levanta` it stands.
4. **Chat: `estado`** → it reports dream cycles and probe accuracy.
5. **Wait ~1 minute** — the Dreaming card's cycle count grows by
   itself. The robot is dreaming without you.

If a step fails, the agent should check, in this order: is
`arduino-router` running? Is the sketch flashed (Bridge error
`method X not available` means no)? Is the venv's python the one
running (`~/et-venv/bin/python`)?

## Step 4 · Teach it something (the magic moment)

Tip the board (or feed a pose) and teach it:

```bash
cd ~/walkersense
~/et-venv/bin/python teach.py add fallen 0.70 0.05 0.70 0 0 0
~/et-venv/bin/python teach.py retrain
```

~30 seconds later the robot believes you — and the same vector it
once read as "standing" now reads "fallen", while everything it knew
before still passes. That is the keep rule doing its job.

## Step 5 · Make it yours

- **New robot?** Add a folder under `projects/` with a `project.json`
  (see the WalkerSense example) and give the system its three plugs:
  act (Bridge methods), see (camera/sensors), think (the board).
- **New words?** Chat commands live in `dashboard.py` (`handle_command`)
  — accent-insensitive keywords, short replies, real state only.
- **A voice?** Optional: export Qwen3-0.6B with the official
  ExecuTorch LLM path into `~/walkersense/qwen3/` and `voice.py`
  starts answering from the robot's real state (see `docs/SETUP.md`).

## Rules your agent must keep

They are all in `AGENTS.md`: the keep rule, bounded MCU commands,
serial-only sketch uploads, no invented metrics, plain-language
public docs. If your agent proposes breaking one, it is wrong —
send it back to `AGENTS.md`.
