#!/usr/bin/env python3
"""
REM PhysicalAI — board status keeper (runs on the Ventuno Q).

Three jobs:
1. BOOT GREETING — when it starts, the board shows how to reach it:
   its IP scrolls across the Arduino LED matrix (and a password too,
   if the owner put one in connect.json — Tailscale SSH needs none).
2. HEARTBEAT — a gentle blink on the LED matrix while online;
   three quick blinks when the internet is gone.
3. TELEMETRY — writes board_state.json every cycle: network, load,
   memory, disk, temperature, which services are alive, and where
   the AI models actually run (CPU/XNNPACK today; the Hexagon NPU
   waits for the QNN runtime). The dashboard shows all of it.

    python3 board_status.py [--interval 5]
"""
import argparse
import json
import os
import socket
import subprocess
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))


def sh(cmd, timeout=3):
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout).stdout.strip()
    except Exception:
        return ""


def ips():
    out = sh(["ip", "-4", "-o", "addr", "show"])
    found = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            found[parts[1]] = parts[3].split("/")[0]
    return {"wifi": found.get("wlp3s0") or found.get("wlan0"),
            "tailnet": found.get("tailscale0")}


def cpu_percent():
    def snap():
        with open("/proc/stat") as f:
            v = [int(x) for x in f.readline().split()[1:]]
        return sum(v), v[3] + v[4]
    t1, i1 = snap()
    time.sleep(0.4)
    t2, i2 = snap()
    dt, di = t2 - t1, i2 - i1
    return round(100 * (1 - di / dt), 1) if dt else 0.0


def online():
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=1.2):
            return True
    except OSError:
        return False


def service_alive(pat):
    return bool(sh(["pgrep", "-fc", pat]))


def collect(net_online):
    mem = {}
    with open("/proc/meminfo") as f:
        for line in f:
            k, v = line.split(":")
            if k in ("MemTotal", "MemAvailable"):
                mem[k] = int(v.split()[0])
    temps = []
    import glob
    for z in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            temps.append(int(open(z).read().strip()) / 1000)
        except Exception:
            pass
    st = os.statvfs("/")
    net = ips()
    wifi_ssid = sh(["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"])
    ssid = next((l.split(":", 1)[1] for l in wifi_ssid.splitlines()
                 if l.startswith("yes:")), None)
    return {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hostname": socket.gethostname(),
        "uptime_s": int(float(open("/proc/uptime").read().split()[0])),
        "load": [round(float(x), 2) for x in open("/proc/loadavg").read().split()[:3]],
        "cpu_percent": cpu_percent(),
        "mem_percent": round(100 * (1 - mem.get("MemAvailable", 0) / max(1, mem.get("MemTotal", 1))), 1),
        "disk_percent": round(100 * (1 - st.f_bavail / max(1, st.f_blocks)), 1),
        "temp_c": max(temps) if temps else None,
        "online": net_online,
        "wifi_ssid": ssid,
        "ips": net,
        "services": {
            "arduino_router": sh(["systemctl", "is-active", "arduino-router"]) == "active",
            "dashboard": service_alive("dashboar[d].py"),
            "idle_learn": service_alive("idle_lear[n].py"),
            "vision": service_alive("visio[n].py"),
        },
        "ai": {
            "accelerator": "Hexagon NPU — on this chip",
            "npu_status": "not in use yet (QNN runtime bundle pending)",
            "pose_model": "CPU · XNNPACK",
            "vision_model": "CPU · XNNPACK",
            "voice_model": "CPU · XNNPACK",
        },
        "connect": {
            "dashboard": f"http://{net.get('tailnet')}:8080" if net.get("tailnet") else None,
            "ssh": f"ssh arduino@{net.get('tailnet')}" if net.get("tailnet") else None,
            "note": "Tailscale SSH needs no password — your account is the key. "
                    "The board scrolls its IP on the LED matrix at startup.",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=5)
    args = ap.parse_args()
    import sys
    sys.path.insert(0, HERE)
    bridge = None
    try:
        from rpc_client import Bridge
        bridge = Bridge()
    except Exception:
        bridge = None

    # ---- boot greeting on the LED matrix
    net = ips()
    if bridge is not None:
        try:
            if net.get("tailnet"):
                bridge.call("matrix_text", f"  IP {net['tailnet']}  ")
                time.sleep(9)
            cfg = {}
            cpath = os.path.join(HERE, "connect.json")
            if os.path.exists(cpath):
                cfg = json.load(open(cpath))
            if cfg.get("password"):
                bridge.call("matrix_text", f"  PASS {cfg['password']}  ")
                time.sleep(9)
        except Exception:
            pass

    last_online = None
    last_blink = 0.0
    while True:
        is_on = online()
        state = collect(is_on)
        tmp = os.path.join(HERE, "board_state.json.tmp")
        with open(tmp, "w") as f:
            json.dump(state, f, indent=1)
        os.replace(tmp, os.path.join(HERE, "board_state.json"))

        now = time.time()
        if bridge is not None and now - last_blink >= 15:
            last_blink = now
            try:
                if is_on:
                    bridge.call("matrix_fill", True)
                    time.sleep(0.15)
                    bridge.call("matrix_fill", False)
                else:
                    for _ in range(3):
                        bridge.call("matrix_fill", True)
                        time.sleep(0.12)
                        bridge.call("matrix_fill", False)
                        time.sleep(0.12)
            except Exception:
                pass
        last_online = is_on
        time.sleep(max(1, args.interval - 1))


if __name__ == "__main__":
    main()
