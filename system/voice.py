#!/usr/bin/env python3
"""
DreamRobot voice — the robot speaks from its own state.

Reads the robot's live state (dream cycles, memory, probe scores, what
the camera currently sees), grounds a short prompt in those facts, and
generates ONE first-person sentence with the local Qwen3-0.6B
ExecuTorch model. No cloud, no templates: the words are the model's;
only the facts are the robot's. Writes voice_state.json (shown in the
interface) and appends a "voice" event to the timeline.

Lives next to the model files (~/walkersense/qwen3/ on the board).

    python3 voice.py
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)


def load(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def main():
    state = load(os.path.join(WS, "state.json"))
    vision = load(os.path.join(WS, "vision_state.json"))
    cycles = (state.get("idle") or {}).get("cycles", 0)
    dataset = state.get("dataset") or {}
    total = dataset.get("total", 0)
    taught = dataset.get("taught", 0)
    acc = round((state.get("probe_accuracy") or 0) * 100)

    facts = (f"you have completed {cycles} dream cycles while sleeping, "
             f"you remember {total} experiences ({taught} of them taught by a human), "
             f"and your posture tests score {acc}%")
    zone = vision.get("zone")
    if zone:
        facts += f". Right now your camera sees the One Dollar Computer: {zone}"
    prompt = ("You are a small robot that learns by itself and dreams of itself "
              "in 3D while it sleeps. Facts about you: " + facts + ".\n"
              "The robot says: \"I")

    cmd = [sys.executable, "-m", "executorch.examples.models.llama.runner.native",
           "--model", "qwen3_0_6b",
           "--pte", os.path.join(HERE, "qwen3_0_6b.pte"),
           "--tokenizer", os.path.join(HERE, "tokenizer.json"),
           "--tokenizer_config", os.path.join(HERE, "tokenizer_config.json"),
           "--prompt", prompt,
           "--params", os.path.join(HERE, "0_6b_config.json"),
           "--max_len", "72", "-kv", "--temperature", "0.7"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=600).stdout

    # The runner prints logs, then the completion inline, then perf stats.
    chunk = out.split("Prefill time:")[0]
    if "Warning - given vocab_size" in chunk:
        chunk = chunk.split("Warning - given vocab_size", 1)[1]
        chunk = chunk.split("\n", 1)[1] if "\n" in chunk else chunk
    chunk = chunk.strip().lstrip('". ')
    first = re.split(r"[\"\n]", chunk)[0].strip()
    parts = re.split(r"(?<=[.!?])\s", first, maxsplit=2)
    said = " ".join(parts[:1]).strip()
    if said and not said.startswith("I "):
        said = "I " + said[0].lower() + said[1:] if len(said) > 1 else said
    if not said:
        said = "(the robot stayed quiet)"

    record = {"said": said, "at": datetime.now(timezone.utc).isoformat(),
              "grounded": {"dream_cycles": cycles, "memories": total,
                           "taught": taught, "probe_accuracy_pct": acc,
                           "vision_zone": zone}}
    with open(os.path.join(WS, "voice_state.json"), "w") as f:
        json.dump(record, f, indent=2)
    with open(os.path.join(WS, "events.log"), "a") as f:
        f.write(json.dumps({"at": record["at"], "kind": "voice",
                            "detail": said}) + "\n")
    print("THE ROBOT SAYS:", said)


if __name__ == "__main__":
    main()
