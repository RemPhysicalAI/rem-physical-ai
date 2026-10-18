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
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DreamRobot — self-learning system</title>
<style>
  * { box-sizing: border-box; }
  body { background: radial-gradient(1200px 700px at 75% -10%, #1b2350 0%, transparent 60%),
         radial-gradient(1000px 600px at 10% 0%, #251b4d 0%, transparent 55%),
         linear-gradient(180deg, #05070f 0%, #0a0f22 55%, #0d1130 100%);
         background-attachment: fixed; color:#e9edff; font-family: system-ui, sans-serif;
         margin:0; padding:22px; min-height:100vh; }
  .hero { position:relative; border-radius:20px; overflow:hidden; margin-bottom:14px;
          border:1px solid rgba(140,160,255,.25); box-shadow: 0 18px 50px rgba(2,4,18,.65); }
  .hero img { width:100%; height:230px; object-fit:cover; object-position:center 63%; display:block;
              animation: heroFloat 26s ease-in-out infinite alternate; }
  @keyframes heroFloat { from { transform: scale(1) translateY(0); } to { transform: scale(1.07) translateY(-6px); } }
  .hero .veil { position:absolute; inset:0; background:linear-gradient(90deg, rgba(4,6,18,.85) 0%, rgba(4,6,18,.45) 48%, rgba(4,6,18,0) 78%); }
  .hero .txt { position:absolute; left:26px; bottom:20px; right:26px; }
  .hero h1 { font-size:37px; margin:0; font-weight:800; text-shadow: 0 2px 24px rgba(90,110,255,.45); }
  .hero .tag { color:#cdd7ff; font-size:15.5px; margin-top:5px; text-shadow: 0 1px 10px rgba(0,0,0,.65); }
  .pill { display:inline-block; padding:2px 11px; border-radius:999px; font-size:12.5px; vertical-align:middle;
          background:rgba(63,185,80,.16); border:1px solid rgba(63,185,80,.45); color:#7ee2a0; margin-left:6px; }
  .sub { color:#9aa7d4; margin:2px 2px 16px; font-size:13.5px; }
  .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:15px; }
  .card { background: linear-gradient(180deg, rgba(23,30,58,.82), rgba(13,18,38,.88));
          border:1px solid rgba(130,150,255,.18); border-radius:16px; padding:16px 18px;
          box-shadow: 0 10px 30px rgba(2,4,16,.5); }
  .card h2 { font-size:13px; text-transform:uppercase; letter-spacing:.09em; color:#aebaff; margin:0 0 12px; }
  .probe { margin:10px 0; } .probe .lbl { display:flex; justify-content:space-between; font-size:14px; }
  .bar { height:10px; background:rgba(255,255,255,.07); border-radius:5px; overflow:hidden; margin-top:4px; }
  .fill { height:100%; border-radius:5px; transition: width .6s; }
  .ok { background:linear-gradient(90deg,#2ea043,#3fb950); } .bad { background:linear-gradient(90deg,#d73a49,#f85149); } .see { background:linear-gradient(90deg,#4c8dff,#58a6ff); }
  .big { font-size:32px; font-weight:800; } .muted { color:#8f9cc9; font-size:13px; }
  .evt { font-size:13px; padding:6px 0; border-bottom:1px solid rgba(130,150,255,.1); }
  .evt b { color:#d2a8ff; font-weight:600; } .kept { color:#3fb950; } .disc { color:#d29922; }
  #live { color:#7ee2a0; } .row { display:flex; justify-content:space-between; margin:4px 0; font-size:14px; }
  img.cam { width:100%; border-radius:12px; border:1px solid rgba(130,150,255,.22); background:#000; }
  #dreamCanvas { border:1px solid rgba(140,160,255,.4) !important; animation: dreamPulse 3.4s ease-in-out infinite; }
  @keyframes dreamPulse { 0%,100% { box-shadow: 0 0 20px rgba(96,120,255,.22); } 50% { box-shadow: 0 0 42px rgba(150,130,255,.42); } }
  .zone { font-size:20px; font-weight:700; }
</style></head><body>
<div class="hero">
  <img src="/banner.jpg" alt="A robot dreaming under the moon">
  <div class="veil"></div>
  <div class="txt">
    <h1>🌙 DreamRobot <span class="pill" id="live">● live</span></h1>
    <div class="tag">It learns by itself. It dreams while it sleeps — and wakes up better.</div>
  </div>
</div>
<div class="sub">An independent self-learning system for any robot. Host robot: <b id="host">WalkerSense — ODC body + Ventuno Q brain</b> · <span id="updated"></span></div>
<div class="grid">
  <div class="card"><h2>👀 Eyes — what the robot sees</h2>
    <img class="cam" id="cam" alt="camera preview">
    <div class="row" style="margin-top:8px"><span class="zone" id="zone">—</span><b id="zconf"></b></div>
    <div class="muted" id="zprobs"></div></div>
  <div class="card"><h2>🌙 The dream — simulation</h2>
    <canvas id="dreamCanvas" style="width:100%;display:block;background:#0a0e14;border-radius:8px;border:1px solid #30363d"></canvas>
    <img class="cam" id="dreamFallback" alt="dream" style="display:none">
    <div class="row" style="margin-top:6px"><span id="dreamScene">the dream</span><b>simulation</b></div>
    <div class="muted">The robot dreams in a physics simulation and sends only the data —
    your screen rebuilds the dream locally. No video, no delay.</div></div>
  <div class="card"><h2>🧠 What it believes</h2><div id="probes"></div>
    <div class="row"><span>Probe accuracy</span><b id="acc"></b></div>
    <div class="row"><span>Mean confidence</span><b id="conf"></b></div></div>
  <div class="card"><h2>💤 Dreaming — idle self-learning</h2>
    <div class="big"><span id="cycles">0</span> <span class="muted" style="font-size:15px">dream cycles</span></div>
    <div id="voice" style="font-size:17px; font-style:italic; margin:6px 0"></div>
    <div id="last"></div>
    <div class="muted" style="margin-top:8px">While idle, the robot dreams variations of what it knows,
    retrains itself, and keeps the new model only if the probes do not regress.</div>
    <h2 style="margin-top:16px">💾 Memory</h2>
    <div class="row"><span>Labeled samples on device</span><b id="total"></b></div>
    <div class="row"><span>Seed · taught by a human</span><b><span id="base"></span> · <span id="taught"></span></b></div>
    <div class="row"><span>Pose model</span><b id="msize"></b></div></div>
  <div class="card"><h2>🪞 Mirror self-test</h2><div id="selftest"><div class="muted">Not run yet.
    The robot will command itself, watch itself, and grade what its vision reports.</div></div></div>
  <div class="card"><h2>💬 Talk to the robot</h2>
    <div id="chatLog" style="height:170px;overflow-y:auto;display:flex;flex-direction:column;gap:6px;margin-bottom:8px"></div>
    <form id="chatForm" style="display:flex;gap:6px">
      <input id="chatInput" autocomplete="off" placeholder="caminhe · levanta · cai · vira · acende · fala · estado"
        style="flex:1;background:rgba(5,8,20,.7);border:1px solid rgba(130,150,255,.3);border-radius:10px;color:#e9edff;padding:9px">
      <button type="submit" style="background:linear-gradient(135deg,#4c6fff,#8b5cf6);border:none;color:#fff;border-radius:10px;padding:9px 16px;cursor:pointer;font-weight:600">Send</button>
    </form></div>
  <div class="card"><h2>📜 Learning timeline</h2><div id="events"></div></div>
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
    if (s.voice && s.voice.said)
      document.getElementById('voice').textContent = '🗣 “' + s.voice.said + '” — the robot, in its own words (Qwen3, local)';
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
tick(); setInterval(tick, 3000);
</script>
<script>
const chatLog = document.getElementById('chatLog');
function chatAdd(who, text) {
  const d = document.createElement('div');
  d.innerHTML = '<b>' + who + ':</b> ' + text;
  d.style.cssText = who === 'you'
    ? 'align-self:flex-end;background:rgba(76,110,255,.18);border:1px solid rgba(124,140,255,.5);padding:6px 9px;border-radius:10px;max-width:92%'
    : 'align-self:flex-start;background:rgba(255,255,255,.05);border:1px solid rgba(130,150,255,.25);padding:6px 9px;border-radius:10px;max-width:92%';
  chatLog.appendChild(d); chatLog.scrollTop = chatLog.scrollHeight;
}
chatAdd('robot', 'Diz-me o que fazer: caminhe, levanta, cai, vira, sonha, acende, apaga, fala, estado.');
document.getElementById('chatForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const inp = document.getElementById('chatInput');
  const text = inp.value.trim(); if (!text) return; inp.value = '';
  chatAdd('you', text.replace(/</g, '&lt;'));
  try {
    const r = await (await fetch('/command', {method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text})})).json();
    chatAdd('robot', r.reply || '…');
    if (r.scene !== undefined) window.__dreamScene = r.scene;
    if (r.reload) window.__dreamReload = true;
  } catch (err) { chatAdd('robot', 'Sem ligação ao robô agora.'); }
});
setTimeout(() => {
  if (!window.__dreamReady) {
    const img = document.getElementById('dreamFallback');
    img.style.display = 'block'; img.src = '/dream_stand.jpg';
    document.getElementById('dreamCanvas').style.display = 'none';
  }
}, 9000);
</script>
<script type="importmap">
{"imports": {"three": "https://unpkg.com/three@0.160.0/build/three.module.js",
             "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/",
             "@mujoco/mujoco": "https://cdn.jsdelivr.net/npm/@mujoco/mujoco@3.16.0/mujoco.js"}}
</script>
<script type="module">
import * as THREE from 'three';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import loadMujoco from '@mujoco/mujoco';
const LABELS = {standing: 'dreaming: standing', walking: 'dreaming: walking',
  fallen: 'dreaming: fallen on its side', flipped: 'dreaming: flipped upside down'};
const canvas = document.getElementById('dreamCanvas');
function showFallback() {
  const img = document.getElementById('dreamFallback');
  img.style.display = 'block'; img.src = '/dream_stand.jpg';
  canvas.style.display = 'none';
}
try {
  const meta = await (await fetch('/dream_replay.json')).json();
  const renderer = new THREE.WebGLRenderer({canvas, antialias: true});
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a0e14);
  scene.fog = new THREE.Fog(0x0a0e14, 1.7, 3.4);
  const camera = new THREE.PerspectiveCamera(42, 4 / 3, 0.01, 20);
  camera.position.set(0.58, -0.74, 0.44);
  camera.up.set(0, 0, 1); camera.lookAt(0, 0, 0.05);
  scene.add(new THREE.HemisphereLight(0xbdd3ff, 0x1a2030, 1.15));
  const key = new THREE.DirectionalLight(0xffffff, 2.2);
  key.position.set(0.4, -0.5, 0.9); scene.add(key);
  const rim = new THREE.DirectionalLight(0x6ea8ff, 1.1);
  rim.position.set(-0.6, 0.5, 0.4); scene.add(rim);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(1.4, 48),
    new THREE.MeshStandardMaterial({color: 0x11161d, roughness: 1}));
  scene.add(ground);
  const grid = new THREE.PolarGridHelper(1.2, 12, 6, 48, 0x2b3a4d, 0x1c2735);
  grid.rotation.x = Math.PI / 2; grid.position.z = 0.001; scene.add(grid);
  const groups = {};
  for (const name of meta.bodies) {
    const g = new THREE.Group(); groups[name] = g; scene.add(g);
  }
  const loader = new STLLoader();
  const mat = new THREE.MeshStandardMaterial({color: 0x93a7cc,
    metalness: 0.35, roughness: 0.45});
  await Promise.all(meta.parts.map(async (p) => {
    const geo = await loader.loadAsync('/meshes/' + p.mesh + '.STL');
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(p.pos[0], p.pos[1], p.pos[2]);
    mesh.quaternion.set(p.quat[1], p.quat[2], p.quat[3], p.quat[0]);
    groups[p.body].add(mesh);
  }));
  function resize() {
    const w = canvas.clientWidth || 460;
    renderer.setSize(w, Math.round(w * 0.72), false);
  }
  resize(); window.addEventListener('resize', resize);
  const caption = document.getElementById('dreamScene');
  function poseFromSim(xpos, xquat) {
    meta.bodies.forEach((name, i) => {
      const b = i + 1, g = groups[name];
      g.position.set(xpos[b * 3], xpos[b * 3 + 1], xpos[b * 3 + 2]);
      g.quaternion.set(xquat[b * 4 + 1], xquat[b * 4 + 2],
                       xquat[b * 4 + 3], xquat[b * 4]);
    });
  }

  // ---- First choice: LIVE MuJoCo simulation, right here in the page.
  let sim = null;
  try {
    const mujoco = await loadMujoco();
    const xml = await (await fetch('/model/twin.xml')).text();
    const model = mujoco.MjModel.from_xml_string(xml);
    sim = {mujoco, model, data: new mujoco.MjData(model),
           scene: null, t: 0, auto: 0};
  } catch (e) { sim = null; }

  if (sim) {
    const {mujoco, model} = sim;
    const SCENES = {
      standing: {pos: [0, 0, 0.11], roll: 0.03},
      walking: {pos: [0, 0, 0.11], roll: 0.0, walk: true},
      fallen: {pos: [0, 0, 0.07], roll: Math.PI / 2, loop: 1.15},
      flipped: {pos: [0, 0, 0.07], roll: Math.PI, loop: 2.2},
    };
    const ORDER = ['standing', 'walking', 'fallen', 'flipped'];
    function setScene(name) {
      const cfg = SCENES[name]; if (!cfg) return;
      try { mujoco.mj_resetData(model, sim.data); }
      catch (e) {
        try { sim.data.delete(); } catch (_) {}
        sim.data = new mujoco.MjData(model);
      }
      const q = sim.data.qpos;
      q[0] = cfg.pos[0]; q[1] = cfg.pos[1]; q[2] = cfg.pos[2];
      q[3] = Math.cos(cfg.roll / 2); q[4] = Math.sin(cfg.roll / 2);
      q[5] = 0; q[6] = 0;
      if (cfg.walk) sim.data.qvel[0] = 0.9;
      sim.scene = name; sim.t = 0;
      caption.textContent = LABELS[name] + ' · live simulation';
    }
    setScene('standing');
    window.__dreamReady = true;
    document.getElementById('dreamFallback').style.display = 'none';
    canvas.style.display = 'block';
    const clock = new THREE.Clock();
    renderer.setAnimationLoop(() => {
      const want = window.__dreamScene;
      if (window.__dreamReload) {
        window.__dreamReload = false;
        sim.auto = 0; setScene(want || 'standing');
      } else if (want && want !== sim.scene) setScene(want);
      else if (!want) {
        sim.auto += clock.getDelta();
        if (sim.auto > 8) {
          sim.auto = 0;
          setScene(ORDER[(ORDER.indexOf(sim.scene) + 1) % ORDER.length]);
        }
      }
      const dt = Math.min(clock.getDelta(), 0.05);
      const steps = Math.max(1, Math.round(dt / model.opt.timestep));
      const cfg = SCENES[sim.scene];
      for (let s = 0; s < steps; s++) {
        if (cfg && cfg.walk) {
          try {
            const t = sim.data.time;
            const fx = sim.data.xfrc_applied;
            fx[6 + 3] = 1.0 * Math.sin(2 * Math.PI * 2.0 * t + Math.PI / 2);
            fx[6 + 4] = 1.2 * Math.sin(2 * Math.PI * 2.0 * t);
          } catch (e) {}
          if (sim.data.qvel[0] < 0.25) sim.data.qvel[0] = 0.8;
          if (Math.abs(sim.data.qpos[0]) > 0.5) sim.data.qpos[0] = 0;
        }
        mujoco.mj_step(model, sim.data);
        sim.t += model.opt.timestep;
      }
      if (cfg && cfg.loop && sim.t > cfg.loop) setScene(sim.scene);
      poseFromSim(sim.data.xpos, sim.data.xquat);
      renderer.render(scene, camera);
    });
  } else {
    // ---- Fallback: replay the dream data the robot recorded.
    let frames = meta.frames, fi = 0;
    window.__dreamReady = true;
    document.getElementById('dreamFallback').style.display = 'none';
    canvas.style.display = 'block';
    const clock = new THREE.Clock();
    const qa = new THREE.Quaternion(), qb = new THREE.Quaternion();
    function range() {
      const want = window.__dreamScene;
      if (!want) return [0, frames.length - 1];
      let a = -1, b = -1;
      frames.forEach((f, i) => { if (f.scene === want) { if (a < 0) a = i; b = i; } });
      return a < 0 ? [0, frames.length - 1] : [a, b];
    }
    renderer.setAnimationLoop(() => {
      if (window.__dreamReload) {
        window.__dreamReload = false;
        fetch('/dream_replay.json').then(r => r.json())
          .then(d => { frames = d.frames; fi = 0; });
      }
      const [a, b] = range();
      fi += clock.getDelta() * meta.fps;
      if (fi < a || fi > b) fi = a;
      const i0 = Math.min(Math.floor(fi), b), i1 = Math.min(i0 + 1, b);
      const t = Math.min(fi - Math.floor(fi), 1);
      const fa = frames[i0], fb = frames[i1];
      meta.bodies.forEach((name, bi) => {
        const A = fa.bodies[bi], B = fb.bodies[bi], g = groups[name];
        g.position.set(A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t,
                       A[2] + (B[2] - A[2]) * t);
        qa.set(A[4], A[5], A[6], A[3]); qb.set(B[4], B[5], B[6], B[3]);
        qa.slerp(qb, t); g.quaternion.copy(qa);
      });
      caption.textContent = (LABELS[frames[i0].scene] || 'the dream') + ' · recorded dream data';
      renderer.render(scene, camera);
    });
  }
} catch (e) { showFallback(); }
</script></body></html>"""


ABOUT_SLIDES = [
    ("slide1.jpg", "DreamRobot",
     "A system that lets any robot learn by itself. This is a PuppyPi. "
     "It learns on its own, dreams about itself — and wakes up better."),
    ("slide2.jpg", "The problem",
     "Robots leave the factory and never learn again. The smart ones cost a "
     "fortune, and their brains live far away, in the cloud. The affordable "
     "ones cannot learn at all."),
    ("slide3.jpg", "How it works",
     "It sees a robot and knows which one it is. Awake, it moves and watches "
     "itself move — and learns from what it sees. Asleep, it dreams: it "
     "imagines itself in a little 3D world, practicing without tiring its "
     "real body. When nobody needs it, it goes back to dreaming — now with "
     "everything it learned while awake."),
    ("slide4.jpg", "It is already alive",
     "All of this is already running, live, inside one small robot — no "
     "internet, no cloud. Tonight, while nobody was using it, it practiced "
     "and improved by itself, again and again. A person showed it something "
     "new, and it learned. And the PuppyPi in this story is real: the robot "
     "in this photo is right here at this event."),
    ("slide5.jpg", "The vision",
     "Any robot can have it: a one-dollar walker, this PuppyPi, any body at "
     "all. One system, many bodies. The intelligence lives inside the robot — "
     "where it should. Robots that dream themselves better."),
]

_ABOUT_CSS = """
  body { background: radial-gradient(1100px 650px at 75% -10%, #1b2350 0%, transparent 60%),
         radial-gradient(900px 550px at 10% 0%, #251b4d 0%, transparent 55%),
         linear-gradient(180deg, #05070f, #0a0f22 60%, #0d1130);
         background-attachment: fixed; color:#e9edff; font-family: system-ui, sans-serif; margin:0; }
  .slide { display:none; min-height:100vh; box-sizing:border-box; padding:28px 5vw 70px;
           flex-direction:column; align-items:center; justify-content:center; text-align:center; }
  .slide.on { display:flex; }
  .slide img { max-width:min(880px, 92vw); max-height:52vh; border-radius:16px;
               border:1px solid rgba(140,160,255,.3); object-fit:cover;
               box-shadow: 0 18px 50px rgba(2,4,18,.6), 0 0 34px rgba(96,120,255,.18); }
  h1 { font-size:clamp(26px, 4.5vw, 44px); margin:22px 0 10px; text-shadow: 0 2px 22px rgba(90,110,255,.4); }
  p { font-size:clamp(15px, 2.2vw, 20px); line-height:1.55; color:#cdd7ff; max-width:760px; }
  .nav { position:fixed; bottom:18px; left:0; right:0; display:flex; gap:14px;
         justify-content:center; align-items:center; }
  .nav button { background:linear-gradient(135deg,#4c6fff,#8b5cf6); color:#fff; border:none; border-radius:10px;
                padding:10px 20px; font-size:15px; cursor:pointer; font-weight:600;
                box-shadow: 0 6px 20px rgba(80,90,255,.35); }
  .nav span { color:#9aa7d4; font-size:14px; }
  a { color:#58a6ff; }
"""

ABOUT_PAGE = ("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
              "<meta name='viewport' content='width=device-width, initial-scale=1'>"
              "<title>DreamRobot — about</title><style>" + _ABOUT_CSS + "</style></head><body>"
              + "".join(
                  f"<section class='slide'><img src='/about/{img}' alt=''>"
                  f"<h1>{title}</h1><p>{text}</p></section>"
                  for img, title, text in ABOUT_SLIDES)
              + """<div class='nav'><button onclick='go(-1)'>← Prev</button>
<span id='counter'></span><button onclick='go(1)'>Next →</button></div>
<script>
let cur = 0; const slides = document.querySelectorAll('.slide');
function show(n) { cur = Math.max(0, Math.min(slides.length - 1, n));
  slides.forEach((s, i) => s.classList.toggle('on', i === cur));
  document.getElementById('counter').textContent = (cur + 1) + ' / ' + slides.length; }
function go(d) { show(cur + d); }
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === ' ') go(1);
  if (e.key === 'ArrowLeft') go(-1); });
show(0);
</script></body></html>""")


def read_json(name):
    path = os.path.join(HERE, name)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def _norm(text):
    import unicodedata
    t = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _matrix(on):
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        from rpc_client import Bridge
        Bridge().call("matrix_fill", on)
        return True
    except Exception:
        return False


def handle_command(text):
    """Chat commands (PT/EN). Returns (reply, extra-json-fields)."""
    t = _norm(text)
    scenes = [
        (("caminh", "anda", "walk"), "walking", "A caminhar no sonho."),
        (("levanta", "stand", "de pe", "acorda"), "standing", "De pé no sonho."),
        (("cai", "deita", "fall"), "fallen", "Caiu — a sonhar que caiu."),
        (("vira", "flip", "capota"), "flipped", "Virado de costas no sonho."),
    ]
    for words, scene, reply in scenes:
        if any(w in t for w in words):
            return reply, {"scene": scene}
    if "sonha" in t or "dorme" in t or "dream" in t:
        subprocess.Popen([sys.executable, os.path.join(
            HERE, "..", "dreamworld", "dream_replay.py")])
        return "A sonhar outra vez — dados novos a caminho.", \
            {"scene": None, "reload": True}
    if "apaga" in t:
        ok = _matrix(False)
        return ("Luz apagada." if ok
                else "Não consegui falar com o corpo agora."), {}
    if "acende" in t or "luz" in t:
        ok = _matrix(True)
        return ("Luz acesa." if ok
                else "Não consegui falar com o corpo agora."), {}
    if "fala" in t or "diz" in t or "voz" in t:
        subprocess.Popen([sys.executable,
                          os.path.join(HERE, "qwen3", "voice.py")])
        return "A pensar em voz alta… a frase aparece no cartão Dreaming.", {}
    if "estado" in t or "como" in t or "status" in t:
        s = read_json("state.json") or {}
        idle = s.get("idle", {})
        acc = round(100 * (s.get("probe_accuracy") or 0))
        return (f"Já sonhei {idle.get('cycles', 0)} ciclos. "
                f"Nas poses de prova acerto {acc}%."), {}
    if "ajuda" in t or "help" in t:
        return ("Comandos: caminhe · levanta · cai · vira · sonha · "
                "acende · apaga · fala · estado"), {}
    return ("Não conheço esse comando. Tenta: caminhe · levanta · cai · "
            "vira · sonha · acende · apaga · fala · estado"), {}


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
        if path == "/about":
            self._send(ABOUT_PAGE, "text/html; charset=utf-8")
        elif path.startswith("/about/"):
            fname = os.path.basename(path)
            fpath = os.path.join(HERE, "about", fname)
            if fname and os.path.exists(fpath):
                mime = "image/png" if fname.endswith(".png") else "image/jpeg"
                with open(fpath, "rb") as f:
                    self._send(f.read(), mime)
            else:
                self.send_response(404)
                self.end_headers()
        elif path == "/":
            self._send(PAGE, "text/html; charset=utf-8")
        elif path == "/state.json":
            state = read_json("state.json") or {}
            vision = read_json("vision_state.json")
            if vision:
                state["vision"] = vision
            selftest = read_json("selftest_state.json")
            if selftest:
                state["selftest"] = selftest
            voice = read_json("voice_state.json")
            if voice:
                state["voice"] = voice
            self._send(json.dumps(state), "application/json")
        elif path in ("/latest.jpg", "/banner.jpg", "/dream_stand.jpg", "/dream_fallen.jpg",
                      "/dream_flipped.jpg"):
            jpg = os.path.join(HERE, path.lstrip("/"))
            if os.path.exists(jpg):
                with open(jpg, "rb") as f:
                    self._send(f.read(), "image/jpeg")
            else:
                self.send_response(404)
                self.end_headers()
        elif path == "/model/twin.xml":
            fpath = os.path.join(HERE, "..", "dreamworld", "model",
                                 "puppy_twin.xml")
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    self._send(f.read(), "text/xml")
            else:
                self.send_response(404)
                self.end_headers()
        elif path == "/dream_replay.json":
            fpath = os.path.join(HERE, "dream_replay.json")
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    self._send(f.read(), "application/json")
            else:
                self.send_response(404)
                self.end_headers()
        elif path.startswith("/meshes/"):
            fname = os.path.basename(path)
            fpath = os.path.join(HERE, "..", "dreamworld", "model",
                                 "meshes", fname)
            if fname.endswith(".STL") and os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    self._send(f.read(), "application/octet-stream")
            else:
                self.send_response(404)
                self.end_headers()
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

    def do_POST(self):
        if self.path.split("?")[0] != "/command":
            self.send_response(404)
            self.end_headers()
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
            reply, extra = handle_command(str(payload.get("text", "")))
            body = {"reply": reply}
            body.update(extra)
            self._send(json.dumps(body), "application/json")
        except Exception as e:
            self._send(json.dumps({"reply": f"Erro: {e}"}),
                       "application/json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()
