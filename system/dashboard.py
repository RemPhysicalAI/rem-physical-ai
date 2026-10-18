#!/usr/bin/env python3
"""
REM PhysicalAI — interface.

REM PhysicalAI is an independent self-learning system that installs on any
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
<title>REM PhysicalAI — self-learning system</title>
<link rel="icon" href="/logo.png">
<style>
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body { background: radial-gradient(1200px 700px at 75% -10%, #1b2350 0%, transparent 60%),
         radial-gradient(1000px 600px at 10% 0%, #251b4d 0%, transparent 55%),
         linear-gradient(180deg, #05070f 0%, #0a0f22 55%, #0d1130 100%);
         background-attachment: fixed; color:#e9edff; font-family: system-ui, sans-serif;
         margin:0; padding:14px; display:flex; flex-direction:column; gap:12px; min-height:100vh; }
  body::after { content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
    background-image:
      radial-gradient(2px 2px at 8% 18%, rgba(255,241,190,.95), transparent 60%),
      radial-gradient(1.6px 1.6px at 22% 64%, rgba(210,220,255,.9), transparent 60%),
      radial-gradient(2.2px 2.2px at 36% 10%, rgba(255,241,190,.85), transparent 60%),
      radial-gradient(1.5px 1.5px at 55% 30%, rgba(255,255,255,.85), transparent 60%),
      radial-gradient(2px 2px at 68% 8%, rgba(210,220,255,.9), transparent 60%),
      radial-gradient(1.6px 1.6px at 82% 42%, rgba(255,241,190,.9), transparent 60%),
      radial-gradient(2.2px 2.2px at 93% 16%, rgba(255,255,255,.8), transparent 60%),
      radial-gradient(1.5px 1.5px at 47% 78%, rgba(210,220,255,.75), transparent 60%),
      radial-gradient(1.8px 1.8px at 15% 88%, rgba(255,241,190,.8), transparent 60%),
      radial-gradient(1.5px 1.5px at 76% 84%, rgba(255,255,255,.75), transparent 60%);
    animation: twinkle 6s ease-in-out infinite alternate; }
  @keyframes twinkle { from { opacity:.55; } to { opacity:.95; } }
  .topbar { position:relative; z-index:1; display:flex; align-items:center; gap:15px;
            background: linear-gradient(180deg, rgba(27,35,66,.85), rgba(15,20,44,.9));
            border:1px solid rgba(150,168,255,.22); border-radius:20px; padding:10px 18px 10px 12px;
            box-shadow: 0 12px 34px rgba(2,4,16,.5), inset 0 1px 0 rgba(255,255,255,.05); }
  .brand-pup { width:58px; height:58px; border-radius:17px; object-fit:cover;
               border:2px solid rgba(255,222,150,.55);
               box-shadow: 0 0 24px rgba(255,206,110,.35);
               animation: pupFloat 5.2s ease-in-out infinite; }
  @keyframes pupFloat { 0%,100% { transform: translateY(0) rotate(-1.6deg); } 50% { transform: translateY(-5px) rotate(1.6deg); } }
  .brand-name { font-size:24px; font-weight:800; letter-spacing:.01em; }
  .brand-tag { color:#9fb0e8; font-size:13px; margin-top:1px; }
  .pill { display:inline-block; padding:2px 11px; border-radius:999px; font-size:12.5px; vertical-align:middle;
          background:rgba(63,185,80,.16); border:1px solid rgba(63,185,80,.45); color:#7ee2a0; margin-left:8px; }
  .top-meta { margin-left:auto; text-align:right; color:#8f9cc9; font-size:12.5px; line-height:1.5; }
  .top-meta b { color:#cdd7ff; }
  .zzz { font-weight:800; color:#ffe9a8; text-shadow: 0 0 16px rgba(255,215,120,.85);
         animation: zFloat 3.8s ease-in-out infinite; white-space:nowrap; }
  @keyframes zFloat { 0%,100% { transform: translateY(0); opacity:.85; } 50% { transform: translateY(-7px); opacity:1; } }
  .main { position:relative; z-index:1; flex:1; min-height:0;
          display:grid; grid-template-columns: 302px minmax(0,1fr) 352px; gap:12px; }
  .panel { background: linear-gradient(180deg, rgba(27,35,66,.85), rgba(15,20,44,.9));
           border:1px solid rgba(150,168,255,.22); border-radius:20px; padding:15px 17px;
           box-shadow: 0 12px 34px rgba(2,4,16,.5), inset 0 1px 0 rgba(255,255,255,.05); }
  .panel h2 { font-size:12.5px; text-transform:uppercase; letter-spacing:.09em; color:#aebaff;
              margin:0 0 11px; border-bottom:1px solid rgba(150,168,255,.14); padding-bottom:8px; }
  .side { overflow-y:auto; min-height:0; }
  .stage { display:flex; flex-direction:column; min-height:0; overflow:hidden; }
  .probe { margin:10px 0; } .probe .lbl { display:flex; justify-content:space-between; font-size:14px; }
  .bar { height:12px; background:rgba(255,255,255,.07); border-radius:999px; overflow:hidden; margin-top:4px; }
  .fill { height:100%; border-radius:999px; transition: width .6s; }
  .ok { background:linear-gradient(90deg,#2ea043,#3fb950); } .bad { background:linear-gradient(90deg,#d73a49,#f85149); } .see { background:linear-gradient(90deg,#4c8dff,#58a6ff); }
  .big { font-size:32px; font-weight:800; } .muted { color:#8f9cc9; font-size:13px; }
  .evt { font-size:13px; padding:6px 0; border-bottom:1px solid rgba(130,150,255,.1); }
  .evt b { color:#d2a8ff; font-weight:600; } .kept { color:#3fb950; } .disc { color:#d29922; }
  #live { color:#7ee2a0; } .row { display:flex; justify-content:space-between; margin:4px 0; font-size:14px; }
  img.cam { width:100%; border-radius:16px; border:1px solid rgba(130,150,255,.22); background:#000; }
  .side-note { margin-top:12px; color:#8f9cc9; font-size:13px; line-height:1.5;
               background:rgba(255,233,168,.05); border:1px solid rgba(255,222,150,.18);
               border-radius:14px; padding:10px 12px; }
  #dreamCanvas { border:1px solid rgba(140,160,255,.4) !important; animation: dreamPulse 3.4s ease-in-out infinite; }
  @keyframes dreamPulse { 0%,100% { box-shadow: 0 0 20px rgba(96,120,255,.22); } 50% { box-shadow: 0 0 42px rgba(150,130,255,.42); } }
  #dreamWrap { position:relative; flex:1; min-height:180px; display:flex; align-items:center; justify-content:center; overflow:hidden; }
  #dreamWrap canvas { max-height:100%; }
  #fsBtn { position:absolute; right:10px; bottom:10px; z-index:6; background:rgba(5,8,20,.68);
           color:#ffe9a8; border:1px solid rgba(255,222,150,.55); border-radius:999px;
           padding:7px 14px; font-size:13.5px; font-weight:600; cursor:pointer; backdrop-filter: blur(3px); }
  #fsBtn:hover { background:rgba(24,30,64,.9); }
  #dreamWrap:fullscreen { background:#05070f; display:flex; align-items:center; justify-content:center; }
  #dreamWrap:fullscreen canvas, #dreamWrap:fullscreen img.cam { width:100% !important; max-height:100vh; object-fit:contain; }
  .zone { font-size:20px; font-weight:700; }
  .proj { border:1px solid rgba(150,168,255,.2); border-radius:14px; padding:10px 12px; margin-bottom:10px;
          background:rgba(255,255,255,.03); }
  .proj.inview { border-color:rgba(255,222,150,.6); background:rgba(255,233,168,.06);
                 box-shadow: 0 0 18px rgba(255,206,110,.15); }
  .proj-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
  .chip { font-size:11.5px; padding:2px 9px; border-radius:999px; white-space:nowrap; }
  .chip.ctl { background:rgba(63,185,80,.16); border:1px solid rgba(63,185,80,.45); color:#7ee2a0; }
  .chip.drm { background:rgba(139,92,246,.18); border:1px solid rgba(139,92,246,.5); color:#cdb4ff; }
  .proj-status { font-size:12.5px; color:#9fb0e8; margin-top:5px; }
  #voice { background:rgba(255,233,168,.07); border:1px solid rgba(255,222,150,.32); border-radius:16px;
           padding:10px 14px; color:#ffedb5; }
  #voice:empty { display:none; }
  .chatbox { margin-top:10px; border-top:1px solid rgba(150,168,255,.14); padding-top:10px; }
  #chatLog { height:104px; overflow-y:auto; display:flex; flex-direction:column; gap:6px; margin-bottom:8px; }
  #chatInput:focus { outline:none; border-color:rgba(255,222,150,.65) !important;
           box-shadow: 0 0 0 3px rgba(255,222,150,.15); }
  .ticker { position:relative; z-index:1; display:flex; align-items:flex-start; gap:16px; padding:11px 17px; }
  .ticker-title { font-size:12.5px; text-transform:uppercase; letter-spacing:.09em; color:#aebaff;
                  white-space:nowrap; padding-top:5px; }
  #events { display:flex; gap:20px; overflow-x:auto; overflow-y:hidden; flex:1; padding-bottom:2px; }
  #events .evt { white-space:nowrap; border-bottom:none; padding:4px 0; }
  .foot { display:flex; align-items:center; gap:10px; justify-content:center;
          color:#8f9cc9; font-size:13px; position:relative; z-index:1; }
  .foot img { width:30px; height:30px; border-radius:10px; border:1px solid rgba(255,222,150,.5);
          box-shadow: 0 0 16px rgba(255,206,110,.3); }
  .foot a { color:#aebaff; text-decoration:none; } .foot a:hover { text-decoration:underline; }
  @media (max-width: 1080px) {
    body { height:auto; }
    .main { grid-template-columns: 1fr; }
    .side { overflow:visible; }
    #dreamWrap { min-height:300px; }
    .top-meta { display:none; }
  }
  @media (prefers-reduced-motion: reduce) {
    .brand-pup, .zzz, #dreamCanvas, body::after { animation: none !important; } }
</style></head><body>
<div class="topbar">
  <img class="brand-pup" src="/logo.png" alt="REM PhysicalAI — the sleeping robot pup">
  <div>
    <div class="brand-name">REM PhysicalAI <span class="pill" id="live">● live</span></div>
    <div class="brand-tag">It learns by itself. It dreams while it sleeps — and wakes up better.</div>
  </div>
  <div class="top-meta">An independent self-learning system for any robot.<br>
    Host robot: <b id="host">WalkerSense — ODC body + Ventuno Q brain</b> · <span id="updated"></span></div>
  <span class="zzz"><span style="font-size:12px">z</span> <span style="font-size:17px">z</span> <span style="font-size:23px">Z</span></span>
</div>
<div class="main">
  <aside class="panel side"><h2>🗂 Projects — one system, many robots</h2>
    <div id="projects"><div class="muted">The camera is the front door: the system
    detects the robot in view, knows which robot it is — then it controls it if
    it can, or dreams about it and trains it virtually if it cannot.</div></div>
    <h2 style="margin-top:16px">👀 Eyes — the camera</h2>
    <img class="cam" id="cam" alt="camera preview">
    <div class="row" style="margin-top:8px"><span class="zone" id="zone">—</span><b id="zconf"></b></div>
    <div class="muted" id="zprobs"></div>
    <div class="side-note">This camera is the robot's window on the world — and on itself.
    What it sees becomes what it learns.</div>
  </aside>
  <section class="panel stage"><h2>🌙 The dream — simulation</h2>
    <div id="dreamWrap">
      <canvas id="dreamCanvas" style="width:100%;display:block;background:#0a0e14;border-radius:16px;border:1px solid #30363d"></canvas>
      <img class="cam" id="dreamFallback" alt="dream" style="display:none">
      <button id="fsBtn" type="button" title="Full screen">⛶ Full screen</button>
    </div>
    <div class="row" style="margin-top:6px"><span id="dreamScene">the dream</span><b>simulation</b></div>
    <div class="muted">The robot dreams in a physics simulation and sends only the data —
    your screen rebuilds the dream locally. No video, no delay.</div>
    <div class="chatbox">
      <div id="chatLog"></div>
      <form id="chatForm" style="display:flex;gap:6px">
        <input id="chatInput" autocomplete="off" placeholder="walk · stand · fall · flip · dream · lights on · speak · status"
          style="flex:1;background:rgba(5,8,20,.7);border:1px solid rgba(130,150,255,.3);border-radius:999px;color:#e9edff;padding:10px 16px">
        <button type="submit" style="background:linear-gradient(135deg,#4c6fff,#8b5cf6);border:none;color:#fff;border-radius:999px;padding:10px 20px;cursor:pointer;font-weight:700;box-shadow:0 6px 18px rgba(110,90,255,.4)">Send 💬</button>
      </form>
    </div>
  </section>
  <aside class="panel side"><h2>🧠 What it believes</h2><div id="probes"></div>
    <div class="row"><span>Probe accuracy</span><b id="acc"></b></div>
    <div class="row"><span>Mean confidence</span><b id="conf"></b></div>
    <h2 style="margin-top:18px">💤 Dreaming — idle self-learning</h2>
    <div class="big"><span id="cycles">0</span> <span class="muted" style="font-size:15px">dream cycles</span></div>
    <div id="voice" style="font-size:17px; font-style:italic; margin:6px 0"></div>
    <div id="last"></div>
    <div class="muted" style="margin-top:8px">While idle, the robot dreams variations of what it knows,
    retrains itself, and keeps the new model only if the probes do not regress.</div>
    <h2 style="margin-top:16px">💾 Memory</h2>
    <div class="row"><span>Labeled samples on device</span><b id="total"></b></div>
    <div class="row"><span>Seed · taught by a human</span><b><span id="base"></span> · <span id="taught"></span></b></div>
    <div class="row"><span>Pose model</span><b id="msize"></b></div>
    <h2 style="margin-top:18px">🪞 Mirror self-test</h2><div id="selftest"><div class="muted">Not run yet.
    The robot will command itself, watch itself, and grade what its vision reports.</div></div>
  </aside>
</div>
<div class="panel ticker"><span class="ticker-title">📜 Learning timeline</span><div id="events"></div></div>
<div class="foot"><img src="/logo.png" alt=""><span>REM PhysicalAI · robots that dream themselves better · <a href="https://github.com/RemPhysicalAI">github.com/RemPhysicalAI</a></span></div>
<script>
async function tick() {
  try {
    const s = await (await fetch('/state.json')).json();
    document.getElementById('updated').textContent = 'updated ' + (s.updated || '');
    const v = s.vision || {};
    if (v.zone) {
      document.getElementById('cam').src = '/latest.jpg?t=' + Date.now();
      document.getElementById('zone').textContent = v.zone === 'watching' ? '👀 watching' : 'ODC is: ' + v.zone;
      document.getElementById('zconf').textContent = v.confidence != null ?
        Math.round(v.confidence * 100) + '% · ' + (v.infer_ms ?? '') + ' ms' : 'camera live';
      document.getElementById('zprobs').textContent = v.note || (v.probs ?
        Object.entries(v.probs).map(([k, p]) => k + ' ' + Math.round(p * 100) + '%').join(' · ') : '');
    }
    if (s.projects) {
      document.getElementById('projects').innerHTML =
        (s.projects.projects || []).map(p => `
        <div class="proj ${p.status === 'in view now' ? 'inview' : ''}">
          <div class="proj-top"><b>${p.name}</b>
          <span class="chip ${p.control === 'full' ? 'ctl' : 'drm'}">${p.control === 'full' ? '⚙️ full control' : '🌙 dream only'}</span></div>
          <div class="muted">${p.what}</div>
          <div class="proj-status">${p.status === 'in view now' ? '📷 in view now — preparing to dream about it' : (p.status === 'on this board' ? '🏠 on this board' : '📷 not in view')}</div>
        </div>`).join('');
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
    ? 'align-self:flex-end;background:rgba(76,110,255,.2);border:1px solid rgba(124,140,255,.5);padding:8px 13px;border-radius:18px 18px 6px 18px;max-width:92%'
    : 'align-self:flex-start;background:rgba(255,255,255,.06);border:1px solid rgba(130,150,255,.25);padding:8px 13px;border-radius:18px 18px 18px 6px;max-width:92%';
  chatLog.appendChild(d); chatLog.scrollTop = chatLog.scrollHeight;
}
chatAdd('robot', 'Tell me what to do: walk, stand, fall, flip, dream, lights on, lights off, speak, status.');
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
  } catch (err) { chatAdd('robot', 'No connection to the robot right now.'); }
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
  const fsBtn = document.getElementById('fsBtn');
  const dreamWrap = document.getElementById('dreamWrap');
  if (fsBtn && dreamWrap) {
    fsBtn.addEventListener('click', () => {
      if (document.fullscreenElement) document.exitFullscreen();
      else if (dreamWrap.requestFullscreen) dreamWrap.requestFullscreen();
    });
    document.addEventListener('fullscreenchange', () => setTimeout(resize, 80));
  }
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
    ("slide1.jpg", "REM PhysicalAI",
     "A system that lets any robot learn by itself. It watches, it learns — "
     "and while it sleeps it dreams, practices in its own little world, and "
     "wakes up better."),
    ("slide2.jpg", "The problem",
     "Robots leave the factory and never learn again. The smart ones cost a "
     "fortune, and their brains live far away, in the cloud. The affordable "
     "ones cannot learn at all."),
    ("slide3.jpg", "How it works",
     "It watches itself and learns from what it sees. People can teach it — "
     "show it once, and it remembers. And it dreams: it practices in a little "
     "simulated world, and only keeps a change if it truly got better."),
    ("slide4.jpg", "It is already alive",
     "All of this is already running, live, inside one small robot — no "
     "internet, no cloud. Tonight it dreamed and improved by itself, again "
     "and again. A person taught it something new, and it learned on the "
     "spot. The robot in this photo is real — it is right here at this "
     "event."),
    ("slide5.jpg", "The vision",
     "Any robot can have it: a one-dollar walker, this PuppyPi, any body "
     "at all. One system, many bodies. The intelligence lives inside the "
     "robot — where it belongs. Robots that dream themselves better."),
]

_ABOUT_CSS = """
  body { background: radial-gradient(1100px 650px at 75% -10%, #1b2350 0%, transparent 60%),
         radial-gradient(900px 550px at 10% 0%, #251b4d 0%, transparent 55%),
         linear-gradient(180deg, #05070f, #0a0f22 60%, #0d1130);
         background-attachment: fixed; color:#e9edff; font-family: system-ui, sans-serif; margin:0; }
  .slide { display:none; min-height:100vh; box-sizing:border-box; padding:24px 3vw 76px;
           flex-direction:column; align-items:center; justify-content:center; text-align:center; }
  .slide.on { display:flex; }
  .slide img { max-width:min(1240px, 95vw); max-height:84vh; border-radius:24px;
               border:1px solid rgba(245,197,107,.35); object-fit:contain;
               box-shadow: 0 24px 60px rgba(2,4,18,.65), 0 0 40px rgba(96,120,255,.16); }
  .pup { position:fixed; top:16px; right:16px; width:64px; height:64px; object-fit:cover; border-radius:20px;
         border:2px solid rgba(255,222,150,.55); box-shadow: 0 0 26px rgba(255,206,110,.35); z-index:5;
         animation: pupFloat 5.2s ease-in-out infinite; }
  @keyframes pupFloat { 0%,100% { transform: translateY(0) rotate(-1.6deg); } 50% { transform: translateY(-7px) rotate(1.6deg); } }
  .nav { position:fixed; bottom:18px; left:0; right:0; display:flex; gap:14px;
         justify-content:center; align-items:center; }
  .nav button { background:linear-gradient(135deg,#4c6fff,#8b5cf6); color:#fff; border:none; border-radius:999px;
                padding:10px 22px; font-size:15px; cursor:pointer; font-weight:600;
                box-shadow: 0 6px 20px rgba(80,90,255,.35); }
  .nav span { color:#9aa7d4; font-size:14px; }
  a { color:#58a6ff; }
"""

ABOUT_PAGE = ("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
              "<meta name='viewport' content='width=device-width, initial-scale=1'>"
              "<title>REM PhysicalAI — about</title><link rel='icon' href='/logo.png'><style>" + _ABOUT_CSS + "</style></head><body>"
              "<img class='pup' src='/logo.png' alt='REM PhysicalAI'>"
              + "".join(
                  f"<section class='slide'><img src='/about/{img}' alt='{title}'></section>"
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
    """Chat commands (keywords PT/EN; replies always in English)."""
    t = _norm(text)
    scenes = [
        (("caminh", "anda", "walk"), "walking", "Walking in the dream."),
        (("levanta", "stand", "de pe", "acorda", "get up"), "standing",
         "Standing in the dream."),
        (("cai", "deita", "fall"), "fallen", "Fallen — dreaming it fell."),
        (("vira", "flip", "capota"), "flipped", "Flipped on its back in the dream."),
    ]
    for words, scene, reply in scenes:
        if any(w in t for w in words):
            return reply, {"scene": scene}
    if "sonha" in t or "dorme" in t or "dream" in t:
        subprocess.Popen([sys.executable, os.path.join(
            HERE, "..", "dreamworld", "dream_replay.py")])
        return "Dreaming again — fresh dream data on the way.", \
            {"scene": None, "reload": True}
    if "apaga" in t or "lights off" in t or "turn off" in t:
        ok = _matrix(False)
        return ("Lights off." if ok
                else "I can't reach the body right now."), {}
    if "acende" in t or "luz" in t or "lights on" in t or "turn on" in t or "light" in t:
        ok = _matrix(True)
        return ("Lights on." if ok
                else "I can't reach the body right now."), {}
    if "fala" in t or "diz" in t or "voz" in t or "speak" in t or "say" in t or "voice" in t:
        subprocess.Popen([sys.executable,
                          os.path.join(HERE, "qwen3", "voice.py")])
        return "Thinking out loud… my words appear in the Dreaming card.", {}
    if "estado" in t or "status" in t or "how are you" in t:
        s = read_json("state.json") or {}
        idle = s.get("idle", {})
        acc = round(100 * (s.get("probe_accuracy") or 0))
        return (f"I have dreamed {idle.get('cycles', 0)} cycles. "
                f"On the probe poses I score {acc}%."), {}
    if "ajuda" in t or "help" in t:
        return ("Commands: walk · stand · fall · flip · dream · "
                "lights on · lights off · speak · status"), {}
    return ("I don't know that one yet. Try: walk · stand · fall · "
            "flip · dream · lights on · lights off · speak · status"), {}


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
            projects = read_json("projects.json")
            if projects:
                vz = (vision or {}).get("zone")
                for p in projects.get("projects", []):
                    if p.get("control") == "full":
                        p["status"] = "on this board"
                    elif vz and vz not in ("absent", "watching"):
                        p["status"] = "in view now"
                    else:
                        p["status"] = "not in view"
                state["projects"] = projects
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
        elif path == "/logo.png":
            fpath = os.path.join(HERE, "logo.png")
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    self._send(f.read(), "image/png")
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
