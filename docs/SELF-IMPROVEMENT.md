# Self-improvement, fast — the Ventuno Q tool

REM PhysicalAI is the self-improvement tool built **especially for the
Arduino Ventuno Q**: plug it into the board and the board starts
getting better at being a robot — by itself, on-device, while it
sleeps. This page is the fast path: from zero to a robot that teaches
itself, in about five minutes.

## 1 · Start it (1 minute)

Fresh board? One command does everything (see `docs/SETUP.md`):

```bash
./quickstart.sh
```

Already installed? The self-improvement is two services:

```bash
cd ~/walkersense
~/et-venv/bin/python dashboard.py --port 8080      # the interface
~/et-venv/bin/python idle_learn.py --interval 30  # the dream engine
```

Open the interface: `http://<your-board>:8080`

## 2 · Watch it improve (the loop)

Every ~30 seconds, one **dream cycle** runs:

1. **Dream** — the robot's twin practices in simulation (standing,
   walking, falling, flipped): 1,000 physics-generated experiences.
2. **Retrain** — a candidate brain is trained on the dreams plus
   everything in memory (seed data + anything a human taught).
3. **Verify** — the candidate must pass fixed probes: the canonical
   poses **and every human-taught example**.
4. **Keep or discard** — it goes live only if the probes do not
   regress. Otherwise it is thrown away and the old brain stays.

You see it live in the **💤 Dreaming** card: the cycle counter grows
on its own, and the **📜 Learning timeline** shows each verdict
(kept / discarded, with the probe score). The robot can dream freely
*because it can never wake up worse*.

## 3 · Teach it in 30 seconds

It misread a pose? Teach the right answer — it retrains on the spot:

```bash
cd ~/walkersense
~/et-venv/bin/python teach.py add fallen 0.70 0.05 0.70 0 0 0
~/et-venv/bin/python teach.py retrain
```

(The six numbers are the body sensors: gravity x/y/z, rotation x/y/z.)
From then on, that pose is one of the probes — **dreams can never
un-teach it**. Teaching by camera works the same way
(`docs/COMMANDS.md`).

## 4 · Prove it to yourself (2 minutes)

- Chat **`estado`** in the interface → it reports its dream cycles
  and probe accuracy from its real state.
- Chat **`caminhe`** → it walks in the live simulation; **`acende`**
  → its real LED matrix lights (the learning reaches the body).
- `curl localhost:8080/state.json` → everything the interface knows:
  model size, dataset counts, per-probe confidence.
- `tail ~/walkersense/events.log` → the paper trail: every teach,
  retrain, keep and discard, timestamped.

## If something looks wrong

| Symptom | Check |
|---|---|
| Dashboard won't load | Is `dashboard.py` running? Restart it (step 1). |
| Cycles not growing | Is `idle_learn.py` running? Check `~/walkersense/idle.log`. |
| Chat `acende` does nothing | The Bridge sketch is not flashed — `docs/SETUP.md`, step 3 (serial upload). |
| Candidates always discarded | The keep rule is protecting the live model — read the probe scores in the timeline before "fixing" anything. |

## Why this belongs on the Ventuno Q

The board was made for physical AI: a real Linux brain, a real
microcontroller for the body, and room to run models locally. REM
PhysicalAI is the layer that makes that hardware *improve itself* —
tiny ExecuTorch models, on-device training, physics dreams, and a
voice — with no cloud anywhere in the loop.
