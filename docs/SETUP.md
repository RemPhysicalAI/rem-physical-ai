# Setup on the Ventuno Q

From a fresh board to a dreaming robot in a few minutes.

## You need

- An **Arduino Ventuno Q** on your network (or on a tailnet), with SSH
  access (user `arduino`)
- A computer to clone this repo and copy it to the board — or clone
  directly on the board

## 1 · Get the code onto the board

```bash
git clone https://github.com/RemPhysicalAI/rem-physical-ai.git
cd rem-physical-ai
```

(On the board itself, or copy the folder to `~/rem-physical-ai` there.)

## 2 · Run the quick start

```bash
./quickstart.sh
```

This creates a Python environment (`~/et-venv`), installs PyTorch +
ExecuTorch (+ the small libraries the system needs), places the engine
in `~/walkersense` and the dream world in `~/dreamworld`, and starts
the dashboard and the dream engine. It is safe to run it again.

## 3 · Flash the body sketch (once)

The Ventuno Q's microcontroller runs the Bridge sketch, which is how
the brain reaches the LED matrix and servos. Upload it **over the
serial port**:

```bash
arduino-cli compile --fqbn arduino:zephyr:ventunoq examples/walkersense/walker_bridge
arduino-cli upload  --fqbn arduino:zephyr:ventunoq -p /dev/ttyACM0 examples/walkersense/walker_bridge
```

## 4 · Open the dashboard

```
http://<your-board>:8080
```

You should see the robot's eyes, what it believes, its dream
(simulated live in your browser), and a chat box. Say `caminhe` —
it walks in the dream. Say `acende` — its real LED matrix lights up.

## Notes from the bench

- **Power:** give the board a proper supply for AI work (a small
  power bank may not hold it under load). Power servos from their own
  pack, with a common ground — never from the board's rail.
- **The dream data:** `dreamworld/dream_sim.py` generates the physics
  dreams; `dreamworld/dream_replay.py` records a dream as data for
  the interface. The quick start runs both once.
- **Voice (optional):** the voice needs a Qwen3-0.6B ExecuTorch model
  in `~/walkersense/qwen3/` (`qwen3_0_6b.pte` + tokenizer files),
  produced with the official ExecuTorch LLM export. Without it,
  everything else works; the robot just stays quiet.
- **Stop / restart:** the two services are plain background processes
  (`dashboard.py`, `idle_learn.py` in `~/walkersense`); the quick
  start restarts them cleanly.
