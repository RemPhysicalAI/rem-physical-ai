#!/usr/bin/env bash
# REM PhysicalAI — quick start on an Arduino Ventuno Q.
# Installs the runtime, places the engine, starts the dream.
# Safe to re-run. See docs/SETUP.md for the full guide.
set -e
cd "$(dirname "$0")"
REPO="$PWD"

echo "== REM PhysicalAI quick start =="

# 1 · System pieces the board image may lack
if [ ! -d "$HOME/et-venv" ]; then
  sudo apt-get install -y -q python3.12-venv libatomic1 libosmesa6 >/dev/null
  python3 -m venv "$HOME/et-venv"
fi
PY="$HOME/et-venv/bin/python"

# 2 · Python runtime (PyTorch + ExecuTorch + helpers)
"$PY" -m pip install -q torch executorch msgpack opencv-python-headless pillow mujoco
echo "runtime ready: $("$PY" -c 'import torch, executorch; print("torch", torch.__version__)')"

# 3 · Place the engine and the dream world
mkdir -p "$HOME/walkersense" "$HOME/dreamworld"
cp system/*.py "$HOME/walkersense/"
cp system/banner.jpg "$HOME/walkersense/" 2>/dev/null || true
cp -r about "$HOME/walkersense/about"
cp -r dreamworld/* "$HOME/dreamworld/"
cp examples/walkersense/samples.json "$HOME/walkersense/samples.json"
[ -f "$HOME/walkersense/model.pte" ] || \
  (cd "$HOME/walkersense" && "$PY" train_model.py --samples samples.json --out model.pte)

# 4 · First dreams (physics data the brain + interface use)
(cd "$HOME/dreamworld" && "$PY" dream_sim.py --dreams 40 && "$PY" dream_replay.py)

# 5 · (Re)start the two services
for p in $(pgrep -f "^$HOME/et-venv/bin/python (dashboard|idle_learn)\.py" || true); do kill "$p" || true; done
sleep 1
(cd "$HOME/walkersense" && setsid nohup "$PY" dashboard.py --port 8080 </dev/null >dashboard.log 2>&1 &)
(cd "$HOME/walkersense" && setsid nohup "$PY" idle_learn.py --interval 30 </dev/null >idle.log 2>&1 &)
sleep 3
IP=$(hostname -I | awk '{print $1}')
echo "== Dreaming. Open the dashboard: http://$IP:8080 =="
echo "   Flash the body sketch once (see docs/SETUP.md, step 3) for the LED matrix + servos."
