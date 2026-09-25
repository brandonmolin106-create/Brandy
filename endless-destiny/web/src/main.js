// ENDLESS DESTINY — an Echoes in the Dark production.
// Based on the song Endless Destiny, written and sung by Sonny Molina.
import * as THREE from 'three';
import { QUALITY, STAR_YAW, START, END, PLATFORM, PLATEAU, BRIDGE_X, RIM_SOUTH_Z, RIM_NORTH_Z, ECHOES } from './config.js';
import { U } from './shaders.js';
import { buildWorld } from './world.js';
import { createTorchbearer } from './torchbearer.js';
import { createPost } from './post.js';
import { createBridge } from './bridge.js';
import { createPlatform } from './platform.js';
import { createEchoes } from './echoes.js';
import { createDetails } from './details.js';
import { createPlayer } from './player.js';
import { createInput } from './input.js';
import { createAudio } from './audio.js';
import { createNarrator } from './narrator.js';
import { createUI } from './ui.js';
import { createStory } from './story.js';

// ---- saved settings and progress (per browser) ---------------------------------------
const save = {
  data: { heard: [], loops: 0, quality: null, volume: 0.9, voice: true, sens: 1 },
  read() {
    try {
      const raw = localStorage.getItem('endless-destiny');
      if (raw) Object.assign(save.data, JSON.parse(raw));
    } catch { /* storage unavailable: play without saving */ }
  },
  write() {
    try { localStorage.setItem('endless-destiny', JSON.stringify(save.data)); } catch { /* ignore */ }
  },
};
save.read();

const params = new URLSearchParams(location.search);
const shot = params.get('shot');
const isTouch = matchMedia('(pointer: coarse)').matches;
const qualityKey = params.get('q') || save.data.quality || (isTouch ? 'low' : 'medium');
const quality = QUALITY[qualityKey] || QUALITY.medium;

const ui = createUI();
const stage = document.getElementById('stage');
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance', preserveDrawingBuffer: !!shot });
} catch (err) {
  ui.error('This device could not start WebGL, so the world cannot be drawn here. Try a recent Chrome, Edge, Safari or Firefox.');
  throw err;
}
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, quality.pixelRatio));
renderer.setSize(stage.clientWidth, stage.clientHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.8;
renderer.shadowMap.enabled = quality.shadows > 0;
renderer.shadowMap.type = THREE.PCFShadowMap;
stage.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x000000, 0.0001); // switches on the height-fog chunk
const camera = new THREE.PerspectiveCamera(52, stage.clientWidth / stage.clientHeight, 0.15, 6000);
scene.add(camera);
const post = createPost(renderer, scene, camera, quality);
post.setSize(stage.clientWidth, stage.clientHeight);

function resize() {
  const w = stage.clientWidth, h = stage.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.fov = w / h < 0.8 ? 64 : 52;   // phones held upright see a little more
  camera.updateProjectionMatrix();
  post.setSize(w, h);
}
addEventListener('resize', resize);
resize();

const G = { renderer, scene, camera, post, ui, save, quality, time: 0 };
window.ED = G;

async function boot() {
  let done = 0;
  const tick = () => { done++; ui.progress(done / 19); };
  const world = await buildWorld(renderer, scene, quality, tick);
  G.world = world;

  const tb = createTorchbearer(quality);
  scene.add(tb.root, tb.embers.points);
  G.tb = tb;

  const bridge = createBridge(world.textures);
  scene.add(bridge.mesh, bridge.dust.points);
  G.bridge = bridge;

  const platform = createPlatform(world.textures);
  scene.add(platform.group, platform.embers.points);
  G.platform = platform;

  const colliders = world.props.colliders;
  const details = createDetails({ field: world.terrain.field, textures: world.textures, stoneMat: platform.stoneMat, quality, colliders });
  scene.add(details.group, details.motes.points);
  // Gravel along the way, from the smallest scanned rock.
  const pebble = world.props.loaded.moon_rock_03;
  let seed = 7;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const q4 = new THREE.Quaternion(), e4 = new THREE.Euler(), p4 = new THREE.Vector3(), s4 = new THREE.Vector3();
  details.instanceCells(details.gravelSeeds.map(([x, z]) => [x, world.terrain.field.sample(x, z), z]), pebble.geo, pebble.mat, ([x, h, z], out) => {
    const k = (0.06 + Math.pow(rnd(), 2.2) * 0.3) / pebble.maxDim;
    e4.set(rnd() * 6, rnd() * 6, rnd() * 6);
    q4.setFromEuler(e4);
    out.compose(p4.set(x, h - 0.02, z), q4, s4.set(k, k * 0.8, k));
  }, false);
  G.details = details;

  const echoes = createEchoes(world.terrain.field);
  scene.add(echoes.group, echoes.motes.points);
  G.echoes = echoes;

  const player = createPlayer({ field: world.terrain.field, colliders, platform, bridge, camera });
  G.player = player;

  const input = createInput(renderer.domElement, {
    joy: document.getElementById('joy'), knob: document.getElementById('knob'),
    listenBtn: document.getElementById('btn-listen'), actBtn: document.getElementById('btn-act'),
  });
  input.sensitivity = save.data.sens;
  G.input = input;

  const audio = createAudio();
  audio.setVolume(save.data.volume);
  G.audio = audio;
  const narrator = createNarrator(ui.subtitle);
  narrator.setEnabled(save.data.voice);
  G.narrator = narrator;

  tb.onStep = () => audio.step(player.surface, player.onBridge ? 1.3 : 1);
  bridge.onPlank = (i) => audio.plank(i);
  details.onIgnite = () => audio.shimmer(0.03, 1.6, 660);

  const story = createStory({ ...G, world, tb, bridge, platform, details, echoes, player, input, audio, narrator });
  G.story = story;

  wireMenus();
  ui.loaded();

  if (shot) { runPhoto(shot); return; }

  story.toTitle();
  let last = performance.now();
  renderer.setAnimationLoop(() => {
    const now = performance.now();
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    input.update();
    if (input.pause && story.beat !== 'title' && story.beat !== 'ended') togglePause();
    if (!story.paused) step(dt);
    else input.consumeLook();
    post.render(G.time);
  });
}

const fwd = new THREE.Vector3();
// One simulation step: story, animation, world uniforms, audio mix.
function step(dt) {
  const { story, tb, player, platform, bridge, details, audio, narrator, world } = G;
  G.time += dt;
  U.uTime.value = G.time;
  story.update(dt, G.input);
  tb.root.position.copy(player.pos);
  tb.root.rotation.y = player.yaw;
  tb.update(dt, G.time, { speed: player.control || story.beat === 'crane' ? player.speed : 0 });
  U.uTorchPos.value.copy(tb.flameWorld);
  U.uTorchCol.value.set(1.0, 0.62, 0.26).multiplyScalar(tb.lit * tb.power);
  bridge.update(dt, G.time);
  platform.update(dt, G.time);
  details.update(dt, G.time, { torchPos: tb.flameWorld, torchLit: tb.lit, listening: G.input.listen, playerPos: player.pos });
  world.sky.position.copy(camera.position);
  // Eyes adapt: once the world turns gold the exposure comes down so the fire still reads as fire.
  renderer.toneMappingExposure = 1.8 - 0.75 * U.uGold.value;
  // Mix the soundscape from where you are.
  const dPlat = Math.hypot(player.pos.x - PLATFORM.x, player.pos.z - PLATFORM.z);
  const canyon = 1 - Math.min(1, Math.max(0, (Math.abs(player.pos.z - (RIM_SOUTH_Z + RIM_NORTH_Z) / 2) - 45) / 40));
  audio.setLayers({
    river: 1 - Math.min(1, Math.max(0, (player.pos.y - 0.5) / 10)),
    wind: Math.max(canyon * 0.8, player.onBridge ? 1 : 0),
    flame: tb.lit,
    roar: platform.blaze * (1 - Math.min(1, Math.max(0, (dPlat - 15) / 200))),
    duck: narrator.speaking ? 1 : 0,
  });
  camera.getWorldDirection(fwd);
  audio.setListener(camera.position, fwd);
}

function togglePause(force) {
  const { story, input } = G;
  const open = force ?? !story.paused;
  story.paused = open;
  if (open) { ui.pause.show(); input.releasePointer(); G.narrator.stop(); }
  else ui.pause.hide();
}

function wireMenus() {
  const $ = (id) => document.getElementById(id);
  $('btn-begin').addEventListener('click', () => G.story.begin());
  $('btn-settings').addEventListener('click', () => togglePause(true));
  $('hud-pause').addEventListener('click', () => togglePause(true));
  $('btn-resume').addEventListener('click', () => togglePause(false));
  $('btn-restart').addEventListener('click', () => { togglePause(false); G.story.begin(); });
  $('btn-again').addEventListener('click', () => { ui.ending.hide(); G.story.begin(); });
  $('btn-title').addEventListener('click', () => { ui.ending.hide(); G.story.toTitle(); });
  const voice = $('opt-voice');
  const setVoiceBtn = () => { voice.setAttribute('aria-pressed', String(save.data.voice)); voice.textContent = save.data.voice ? 'On' : 'Off'; };
  setVoiceBtn();
  voice.addEventListener('click', () => { save.data.voice = !save.data.voice; G.narrator.setEnabled(save.data.voice); setVoiceBtn(); save.write(); });
  const vol = $('opt-volume');
  vol.value = save.data.volume;
  vol.addEventListener('input', () => {
    save.data.volume = +vol.value;
    G.audio.setVolume(save.data.volume);
    G.narrator.setVolume(Math.min(1, save.data.volume + 0.1));
    save.write();
  });
  const sens = $('opt-sens');
  sens.value = save.data.sens;
  sens.addEventListener('input', () => { save.data.sens = +sens.value; G.input.sensitivity = save.data.sens; save.write(); });
  const q = $('opt-quality');
  q.value = qualityKey;
  q.addEventListener('change', () => { save.data.quality = q.value; save.write(); location.reload(); });
}

// ---- photo mode: fixed views of the journey for screenshots --------------------------
function runPhoto(name) {
  const { story, tb, player, platform, bridge, echoes, world } = G;
  const set = (x, z, yaw, opts = {}) => {
    player.place(x, z, yaw);
    tb.lit = opts.lit ?? 1;
    tb.sit = opts.sit ?? 0;
    tb.snapPose(opts.pose || (tb.sit ? 'sit' : 'idle'));
    if (opts.y !== undefined) player.pos.y = opts.y;
  };
  const cam = (px, py, pz, tx, ty, tz) => { camera.position.set(px, py, pz); camera.lookAt(tx, ty, tz); };
  const behind = (yaw, dist, h, lookUp = 0) => {
    const p = player.pos;
    cam(p.x + Math.sin(yaw) * dist, p.y + h, p.z + Math.cos(yaw) * dist,
      p.x - Math.sin(yaw) * 20, p.y + h + lookUp * 20, p.z - Math.cos(yaw) * 20);
  };
  const gold = (on) => {
    U.uGold.value = on ? 1 : 0;
    U.uGoldRadius.value = on ? 900 : 0;
    platform.lit = on ? 1 : 0;
    platform.blaze = on ? 1 : 0;
    world.starlight.color.set(on ? 0xffc27a : 0x8796ff);
    world.hemi.color.set(on ? 0xa87a48 : 0x33407a);
    if (on) world.env.setWarm(true);
  };
  story.beat = 'photo';
  const views = {
    river() { set(START.x, START.z, STAR_YAW, { lit: 0, sit: 1 }); behind(STAR_YAW + 0.12, 3.8, 1.6, 0.12); },
    flame() {
      // Walk from the start toward the star until the water is just ahead.
      let wx = START.x, wz = START.z;
      for (let i = 0; i < 400; i++) {
        const nx = wx - Math.sin(STAR_YAW) * 0.25, nz = wz - Math.cos(STAR_YAW) * 0.25;
        if (world.terrain.field.sample(nx - Math.sin(STAR_YAW) * 1.6, nz - Math.cos(STAR_YAW) * 1.6) < 0.03) break;
        wx = nx; wz = nz;
      }
      set(wx, wz, STAR_YAW, { lit: 1, pose: 'lower' });
      const p = player.pos;
      const fx = -Math.sin(STAR_YAW), fz = -Math.cos(STAR_YAW);
      const side = STAR_YAW + Math.PI * 0.72;
      cam(p.x + fx * 1.2 + Math.sin(side) * 3.0, 1.45, p.z + fz * 1.2 + Math.cos(side) * 3.0, p.x + fx * 1.2, 0.35, p.z + fz * 1.2);
    },
    dark() { set(6.5, -58, 0.1, { lit: 1 }); behind(0.35, 4.4, 1.9, -0.06); },
    gorge() { set(9.5, -104, 0.1, { lit: 1 }); behind(3.0, 11, 5.5, -0.22); },
    rim() { set(BRIDGE_X, RIM_SOUTH_Z + 2.5, 0, { lit: 1 }); behind(-0.3, 4.2, 1.8, 0.06); },
    bridge() { bridge.bornUpTo(RIM_SOUTH_Z - 42, -30); set(BRIDGE_X, RIM_SOUTH_Z - 40, 0, { lit: 1 }); cam(BRIDGE_X + 55, PLATEAU + 26, RIM_SOUTH_Z - 10, BRIDGE_X, PLATEAU - 2, RIM_SOUTH_Z - 50); },
    onBridge() { bridge.bornUpTo(RIM_SOUTH_Z - 30, -30); bridge.bornUpTo(RIM_SOUTH_Z - 32, G.time + 1.2); set(BRIDGE_X, RIM_SOUTH_Z - 30, 0, { lit: 1 }); behind(-0.45, 4.6, 1.7, -0.05); },
    platform() { bridge.completeInstantly(0); set(PLATFORM.x - 1.5, PLATFORM.z + 16, -0.1, { lit: 1 }); behind(0.25, 5, 2.2, 0.08); },
    lighting() { bridge.completeInstantly(0); gold(true); set(PLATFORM.x, PLATFORM.z + 1.7, 0, { lit: 1, y: platform.topY, pose: 'raise' }); cam(PLATFORM.x + 4.5, PLATEAU + 2.2, PLATFORM.z + 14, PLATFORM.x, platform.topY + 2.4, PLATFORM.z); },
    goldWide() { bridge.completeInstantly(0); gold(true); set(PLATFORM.x, PLATFORM.z + 1.7, 0, { lit: 1, y: platform.topY }); cam(PLATFORM.x + 14, PLATEAU + 22, PLATFORM.z + 70, PLATFORM.x, platform.topY + 8, PLATFORM.z); },
    road() { bridge.completeInstantly(0); gold(true); set(-8, -338, 2.6, { lit: 1 }); behind(2.8, 4.6, 1.9, -0.04); },
    end() { bridge.completeInstantly(0); gold(true); set(END.x, END.z, STAR_YAW, { lit: 1, sit: 1 }); behind(STAR_YAW + 0.1, 3.6, 1.5, 0.12); },
    leafClose() { bridge.completeInstantly(0); platform.lit = 0.55; set(PLATFORM.x + 1.2, PLATFORM.z + 2.2, -0.3, { lit: 1, y: platform.topY }); cam(PLATFORM.x + 2.2, platform.topY + 1.7, PLATFORM.z + 6.2, PLATFORM.x, platform.topY + 2.2, PLATFORM.z); },
    echo() { set(ECHOES[2].pos[0] + 0.5, ECHOES[2].pos[1] + 5, 0.05, { lit: 1 }); behind(0.05, 4, 1.8, -0.02); },
  };
  (views[name] || views.river)();
  const cameraPos = camera.position.clone(), cameraQuat = camera.quaternion.clone();
  // Let particles, flames and the listen glow settle, then render.
  for (let i = 0; i < 60; i++) {
    G.time += 1 / 30;
    U.uTime.value = G.time;
    tb.root.position.copy(player.pos);
    tb.root.rotation.y = player.yaw;
    tb.update(1 / 30, G.time, { speed: 0 });
    U.uTorchPos.value.copy(tb.flameWorld);
    U.uTorchCol.value.set(1.0, 0.62, 0.26).multiplyScalar(tb.lit * tb.power);
    bridge.update(1 / 30, G.time);
    platform.update(1 / 30, G.time);
    G.details.update(1 / 30, G.time, { torchPos: tb.flameWorld, torchLit: tb.lit, listening: name === 'echo', playerPos: player.pos });
    echoes.update(1 / 30, G.time, { playerPos: player.pos, listening: name === 'echo', torchPos: tb.flameWorld, pulseRadius: 0 });
  }
  camera.position.copy(cameraPos);
  camera.quaternion.copy(cameraQuat);
  world.sky.position.copy(camera.position);
  renderer.toneMappingExposure = 1.8 - 0.75 * U.uGold.value;
  post.render(G.time);
  post.render(G.time);
  window.__ED_READY = true;
}

// Test hooks for automated play-throughs.
G.debug = {
  teleport(x, z, yaw = 0) { G.player.place(x, z, yaw); },
  step,
};

boot().catch((err) => {
  console.error(err);
  ui.error('The world could not load: ' + err.message);
});
