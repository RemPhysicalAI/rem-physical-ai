#!/usr/bin/env python3
"""
DreamRobot — interface.

DreamRobot is an independent self-learning system that installs on any
robot: give it a way to act, a camera to see, and a computer to think,
and it learns by itself — teaching itself while awake, dreaming while
idle, and testing itself in the mirror. This page is its window: what
the robot sees, what it believes, how it dreams, and its learning
timeline. Read-only; the learning happens on the device.

    python3 dashboard.py [--port 8080]

State comes from the robot's own files: state.json (beliefs + dreams,
written by idle_learn.py), vision_state.json + latest.jpg (vision.py),
selftest_state.json (selftest.py), events.log (everything, in order).
"""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DreamRobot — self-learning system</title>
<style>
  body { background:#0d1117; color:#e6edf3; font-family: system-ui, sans-serif;
         margin:0; padding:20px; }
  h1 { font-size:24px; margin:0 0 2px; } .sub { color:#8b949e; margin-bottom:18px; }
  .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap:14px; }
  .card { background:#161b22; border:1px solid #30363d; border-radius:10px; padding:14px 16px; }
  .card h2 { font-size:13px; text-transform:uppercase; letter-spacing:.07em; color:#8b949e; margin:0 0 10px; }
  .probe { margin:10px 0; } .probe .lbl { display:flex; justify-content:space-between; font-size:14px; }
  .bar { height:10px; background:#21262d; border-radius:5px; overflow:hidden; margin-top:4px; }
  .fill { height:100%; border-radius:5px; transition: width .6s; }
  .ok { background:#3fb950; } .bad { background:#f85149; } .see { background:#58a6ff; }
  .big { font-size:30px; font-weight:700; } .muted { color:#8b949e; font-size:13px; }
  .evt { font-size:13px; padding:6px 0; border-bottom:1px solid #21262d; }
  .evt b { color:#d2a8ff; font-weight:600; } .kept { color:#3fb950; } .disc { color:#d29922; }
  #live { color:#3fb950; } .row { display:flex; justify-content:space-between; margin:4px 0; font-size:14px; }
  img.cam { width:100%; border-radius:8px; border:1px solid #30363d; background:#000; }
  .zone { font-size:20px; font-weight:700; }
</style></head><body>
<h1>🌙 DreamRobot <span id="live">● live</span></h1>
<div class="sub">An independent self-learning system for any robot. It learns by itself,
dreams while it sleeps, and wakes up better. <span class="muted">Host robot: <b id="host">WalkerSense — ODC body + Ventuno Q brain</b> · <span id="updated"></span></span></div>
<div class="grid">
  <div class="card"><h2>Eyes — what the robot sees</h2>
    <img class="cam" id="cam" alt="camera preview">
    <div class="row" style="margin-top:8px"><span class="zone" id="zone">—</span><b id="zconf"></b></div>
    <div class="muted" id="zprobs"></div></div>
  <div class="card"><h2>Dream simulator — what it's dreaming</h2>
    <canvas id="dreamCanvas" width="460" height="240" style="width:100%;background:#0a0e14;border-radius:8px;border:1px solid #30363d"></canvas>
    <div class="row" style="margin-top:6px"><span id="dreamCaption">loading dreams…</span><b id="dreamCount"></b></div>
    <div class="muted">Each frame is one imagined pose from the robot's current dream batch —
    rehearsals it generated from its own memories while idle.</div></div>
  <div class="card"><h2>What it believes (probe poses)</h2><div id="probes"></div>
    <div class="row"><span>Probe accuracy</span><b id="acc"></b></div>
    <div class="row"><span>Mean confidence</span><b id="conf"></b></div></div>
  <div class="card"><h2>Dreaming (idle self-learning)</h2>
    <div class="big"><span id="cycles">0</span> <span class="muted" style="font-size:15px">dream cycles</span></div>
    <div id="last"></div>
    <div class="muted" style="margin-top:8px">While idle, the robot dreams variations of what it knows,
    retrains itself, and keeps the new model only if the probes do not regress.</div>
    <h2 style="margin-top:16px">Memory</h2>
    <div class="row"><span>Labeled samples on device</span><b id="total"></b></div>
    <div class="row"><span>Seed · taught by a human</span><b><span id="base"></span> · <span id="taught"></span></b></div>
    <div class="row"><span>Pose model</span><b id="msize"></b></div></div>
  <div class="card"><h2>Mirror self-test</h2><div id="selftest"><div class="muted">Not run yet.
    The robot will command itself, watch itself, and grade what its vision reports.</div></div></div>
  <div class="card"><h2>Learning timeline</h2><div id="events"></div></div>
</div>
<script>
async function tick() {
  try {
    const s = await (await fetch('/state.json')).json();
    document.getElementById('updated').textContent = 'updated ' + (s.updated || '');
    const v = s.vision || {};
    if (v.zone) {
      document.getElementById('cam').src = '/latest.jpg?t=' + Date.now();
      document.getElementById('zone').textContent = 'ODC is: ' + v.zone;
      document.getElementById('zconf').textContent = Math.round((v.confidence || 0) * 100) + '% · ' + (v.infer_ms ?? '') + ' ms';
      document.getElementById('zprobs').textContent = v.probs ?
        Object.entries(v.probs).map(([k, p]) => k + ' ' + Math.round(p * 100) + '%').join(' · ') : '';
    }
    document.getElementById('probes').innerHTML = (s.probes || []).map(p => `
      <div class="probe"><div class="lbl"><span>${p.name} → <b>${p.pose}</b></span>
      <span>${Math.round(p.confidence * 100)}%</span></div>
      <div class="bar"><div class="fill ${p.ok ? 'ok' : 'bad'}" style="width:${p.confidence * 100}%"></div></div></div>`).join('');
    document.getElementById('acc').textContent = Math.round((s.probe_accuracy || 0) * 100) + '%';
    document.getElementById('conf').textContent = (s.probe_confidence || 0).toFixed(2);
    const d = s.dataset || {};
    document.getElementById('total').textContent = d.total ?? '–';
    document.getElementById('base').textContent = d.base ?? '–';
    document.getElementById('taught').textContent = d.taught ?? '–';
    const m = s.model || {};
    document.getElementById('msize').textContent = m.size_bytes ? m.size_bytes + ' bytes' : '–';
    const idle = s.idle || {};
    document.getElementById('cycles').textContent = idle.cycles || 0;
    if (idle.last) { const L = idle.last;
      document.getElementById('last').innerHTML =
        `<div class="row"><span>Last dream</span><b class="${L.kept ? 'kept' : 'disc'}">${L.kept ? 'kept ✓' : 'discarded'}</b></div>
         <div class="row"><span>Dreamed rehearsals</span><b>${L.dreamed}</b></div>
         <div class="row"><span>Accuracy</span><b>${L.acc_before} → ${L.acc_after}</b></div>
         <div class="row"><span>Confidence</span><b>${L.conf_before} → ${L.conf_after}</b></div>`;
    }
    const st = s.selftest;
    if (st) {
      document.getElementById('selftest').innerHTML =
        `<div class="big">${st.score}</div><div class="muted">times the vision correctly reported what the robot did (${st.at})</div>
         <div style="margin-top:6px">` + (st.trials || []).map(t =>
           `<div class="row"><span>commanded: ${t.commanded}</span><b class="${t.ok ? 'kept' : 'disc'}">saw: ${t.seen}</b></div>`).join('') + `</div>`;
    }
    const ev = await (await fetch('/events')).json();
    document.getElementById('events').innerHTML = ev.slice(-9).reverse().map(e =>
      `<div class="evt"><b>${e.kind}</b> · ${e.detail}<br><span class="muted">${e.at}</span></div>`).join('')
      || '<div class="muted">No events yet.</div>';
    document.getElementById('live').textContent = '● live';
  } catch (e) { document.getElementById('live').textContent = '○ reconnecting'; }
}
let dreams = [], di = 0;
const DCLS = ['standing', 'walking', 'fallen', 'flipped'];
const DCOL = {standing: '#3fb950', walking: '#58a6ff', fallen: '#d29922', flipped: '#f85149'};
async function loadDreams() {
  try { const d = await (await fetch('/dreams.json')).json(); dreams = d.dreams || [];
    document.getElementById('dreamCount').textContent = dreams.length ? dreams.length + ' poses in this dream' : '';
  } catch (e) {}
}
function drawDream() {
  const c = document.getElementById('dreamCanvas');
  if (!c || !dreams.length) return;
  const ctx = c.getContext('2d'), W = c.width, H = c.height;
  const s = dreams[di % dreams.length]; di++;
  const [ax, , az, gx] = s.features;
  const tilt = Math.atan2(ax, az);
  const cls = DCLS[s.label] || 'standing';
  ctx.clearRect(0, 0, W, H);
  const groundY = H - 30;
  ctx.strokeStyle = '#30363d'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(0, groundY); ctx.lineTo(W, groundY); ctx.stroke();
  const cx = W / 2;
  const lift = Math.max(0, Math.cos(tilt)) * 36;
  const by = groundY - 16 - lift;
  const stride = cls === 'walking' ? Math.sin(Date.now() / 130) * 9 : 0;
  ctx.save(); ctx.translate(cx, by); ctx.rotate(tilt);
  ctx.strokeStyle = '#8b949e'; ctx.lineWidth = 4; ctx.lineCap = 'round';
  [[-30, stride], [-12, -stride], [14, -stride], [32, stride]].forEach(([lx, sw]) => {
    ctx.beginPath(); ctx.moveTo(lx, 10); ctx.lineTo(lx + sw * 0.4, 22); ctx.lineTo(lx + sw, 34); ctx.stroke();
  });
  ctx.fillStyle = DCOL[cls]; ctx.beginPath(); ctx.roundRect(-44, -13, 88, 26, 6); ctx.fill();
  ctx.fillStyle = '#e6edf3'; ctx.fillRect(36, -17, 15, 13);
  ctx.beginPath(); ctx.arc(41, -10, 2.4, 0, 7); ctx.fillStyle = '#0d1117'; ctx.fill();
  ctx.restore();
  const deg = Math.round(tilt * 180 / Math.PI);
  document.getElementById('dreamCaption').textContent =
    `dreaming: ${cls} · tilt ${deg}° · ${s.source === 'dream' ? 'imagined from memory' : 'a memory'}`;
}
loadDreams(); setInterval(loadDreams, 15000); setInterval(drawDream, 900);
tick(); setInterval(tick, 3000);
</script></body></html>"""


def read_json(name):
    path = os.path.join(HERE, name)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, content_type):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self._send(PAGE, "text/html; charset=utf-8")
        elif path == "/state.json":
            state = read_json("state.json") or {}
            vision = read_json("vision_state.json")
            if vision:
                state["vision"] = vision
            selftest = read_json("selftest_state.json")
            if selftest:
                state["selftest"] = selftest
            self._send(json.dumps(state), "application/json")
        elif path == "/latest.jpg":
            jpg = os.path.join(HERE, "latest.jpg")
            if os.path.exists(jpg):
                with open(jpg, "rb") as f:
                    self._send(f.read(), "image/jpeg")
            else:
                self.send_response(404)
                self.end_headers()
        elif path == "/dreams.json":
            dreams = read_json("dream_samples.json") or []
            imagined = [d for d in dreams if d.get("source") == "dream"]
            memories = [d for d in dreams if d.get("source") != "dream"]
            self._send(json.dumps({"dreams": (imagined + memories)[-160:],
                                   "total": len(dreams)}), "application/json")
        elif path == "/events":
            events = []
            log = os.path.join(HERE, "events.log")
            if os.path.exists(log):
                with open(log) as f:
                    events = [json.loads(line) for line in f if line.strip()]
            self._send(json.dumps(events[-30:]), "application/json")
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()
