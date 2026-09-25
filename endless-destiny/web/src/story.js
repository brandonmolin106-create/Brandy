// The journey, beat by beat: river -> flame -> the dark -> the bridge -> the other side
// -> the light -> the road -> the river again. It ends where it began, and begins again.
import * as THREE from 'three';
import { U } from './shaders.js';
import { pathInfo } from './terrainfield.js';
import {
  LINES, START, END, STAR_YAW, PLATFORM, PLATEAU, BRIDGE_X, RIM_SOUTH_Z, RIM_NORTH_Z,
  S_RIM_SOUTH, S_PLATFORM, S_END, PATH, PATH_S, ECHOES,
} from './config.js';
import { createParticles } from './fx.js';

const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const ease = (t) => t * t * (3 - 2 * t);

function pointOnPath(s) {
  for (let i = 0; i < PATH.length - 1; i++) {
    if (s <= PATH_S[i + 1]) {
      const t = (s - PATH_S[i]) / (PATH_S[i + 1] - PATH_S[i]);
      return { x: PATH[i][0] + (PATH[i + 1][0] - PATH[i][0]) * t, z: PATH[i][1] + (PATH[i + 1][1] - PATH[i][1]) * t };
    }
  }
  return { x: END.x, z: END.z };
}

export function createStory(G) {
  const { player, tb, camera, ui, narrator, audio, echoes, bridge, platform, details, world, post, save } = G;
  const S = {
    beat: 'title', t: 0, flags: {}, cine: null, paused: false,
    pulseT: 99, pulseR: 0,
  };
  const roadDust = createParticles({ count: 600, color: 0xffc46a, size: 0.06 });
  roadDust.points.material.uniforms.uBright.value = 3;
  G.scene.add(roadDust.points);
  const tmpA = new THREE.Vector3(), tmpB = new THREE.Vector3();
  const coldStar = new THREE.Color(0x8796ff), warmStar = new THREE.Color(0xffc27a);
  const coldSky = new THREE.Color(0x33407a), warmSky = new THREE.Color(0xa87a48);
  const coldFog = new THREE.Vector3(0.030, 0.030, 0.072);

  const setBeat = (b) => { S.beat = b; S.t = 0; };
  const bars = (on) => { S.barsTarget = on ? 1 : 0; };
  S.barsTarget = 0;

  // ---- world reset -------------------------------------------------------------------
  function resetWorld() {
    S.flags = {};
    bridge.reset();
    platform.lit = 0;
    platform.blaze = 0;
    platform.embers.clear();
    details.reset();
    roadDust.clear();
    U.uGold.value = 0;
    U.uGoldRadius.value = 0;
    U.uFogDensity.value = 0.010;
    U.uFogCol.value.copy(coldFog);
    world.starlight.color.copy(coldStar);
    world.hemi.color.copy(coldSky);
    world.hemi.intensity = 0.7;
    world.starlight.intensity = 0.5;
    if (S.warmEnv) { world.env.setWarm(false); S.warmEnv = false; }
    echoes.reset([]);
    tb.lit = 0;
    tb.climb = 0;
    tb.power = 1;
    tb.pose = 'idle';
    tb.lookYaw = 0;
    player.maxS = 24;
    player.bridgeActive = false;
    player.control = false;
    player.camFree = true;
    ui.setEchoes(0, ECHOES.length, false);
    ui.showHUD(false);
    ui.prompt(null);
    ui.hint(null);
  }

  function sitAt(x, z, yaw) {
    player.place(x, z, yaw);
    tb.sit = 1;
    tb.snapPose('sit');
  }

  // ---- public controls ---------------------------------------------------------------
  S.toTitle = () => {
    resetWorld();
    sitAt(START.x, START.z, STAR_YAW);
    setBeat('title');
    post.cinema.uniforms.uFade.value = 1;
    ui.title.show({ heard: save.data.heard.length, total: ECHOES.length, loops: save.data.loops });
  };
  S.begin = () => {
    audio.start();
    narrator.unlock();
    ui.title.hide();
    resetWorld();
    sitAt(START.x, START.z, STAR_YAW);
    post.cinema.uniforms.uFade.value = 0;
    setBeat('opening');
    document.body.classList.add('playing');
  };

  // ---- cinematic camera helpers --------------------------------------------------------
  function camLook(pos, target) {
    camera.position.copy(pos);
    camera.lookAt(target);
  }

  // ---- echoes & listening -------------------------------------------------------------
  function gatherEcho(e) {
    audio.shimmer(0.06, 3, 1174.7);
    narrator.sayAll(e.def.lines, { kind: 'echo', id: `echo-${e.def.id}` });
    const n = echoes.gatheredCount();
    tb.power = 1 + n * 0.045;
    ui.setEchoes(n, ECHOES.length, S.flags.lit);
    if (!save.data.heard.includes(e.def.id)) { save.data.heard.push(e.def.id); save.write(); }
    if (n === 1) ui.hint('Each echo lights another vein of the leaf.', 6);
  }

  function updateListen(dt, listening) {
    S.pulseT += dt;
    if (listening && S.pulseT > 1.9) {
      S.pulseT = 0;
      U.uPulseCenter.value.copy(player.pos);
      audio.listenSweep();
      for (const e of echoes.list) {
        if (e.state !== 'idle') continue;
        const d = e.home.distanceTo(player.pos);
        if (d < 80) audio.echoAt(e.home, d / 34);
      }
    }
    const age = S.pulseT;
    S.pulseR = age < 2.2 ? age * 34 : 0;
    U.uPulseRadius.value = S.pulseR;
    U.uPulseAmt.value = age < 2.2 ? (1 - age / 2.2) * 0.9 : 0;
    // The hood turns toward the nearest echo while listening.
    const near = echoes.nearestIdle(player.pos);
    if (listening && near && near.dist < 70) {
      const want = Math.atan2(-(near.echo.home.x - player.pos.x), -(near.echo.home.z - player.pos.z));
      let d = want - player.yaw;
      d = Math.atan2(Math.sin(d), Math.cos(d));
      tb.lookYaw = THREE.MathUtils.clamp(d, -0.9, 0.9);
    } else tb.lookYaw = 0;
  }

  // ---- per-frame --------------------------------------------------------------------
  S.update = (dt, input) => {
    S.t += dt;
    const t = S.t;
    const cin = post.cinema.uniforms;
    cin.uBars.value += (S.barsTarget - cin.uBars.value) * Math.min(1, dt * 2.5);
    const info = pathInfo(player.pos.x, player.pos.z);
    const act = input.act;
    let listening = input.listen && player.control;

    switch (S.beat) {
      case 'title': {
        // Slow drift behind the seated torchbearer, facing the river and the star.
        const a = STAR_YAW + 0.25 * Math.sin(G.time * 0.05);
        tmpA.set(START.x + Math.sin(a) * 6.2, player.pos.y + 1.9, START.z + Math.cos(a) * 6.2);
        tmpB.set(START.x - Math.sin(STAR_YAW) * 30, player.pos.y + 5, START.z - Math.cos(STAR_YAW) * 30);
        camLook(tmpA, tmpB);
        return;
      }
      case 'opening': {
        cin.uFade.value = smooth(0.6, 4.2, t);
        if (t > 0.2 && !S.flags.openLine) {
          S.flags.openLine = true;
          narrator.say(save.data.loops > 0 ? LINES.openLoop : LINES.openFirst, { id: save.data.loops > 0 ? 'open-loop' : 'open' });
        }
        if (t > 2.4 && !S.flags.ch0) { S.flags.ch0 = true; ui.chapter(0, 'THE RIVER'); }
        const k = ease(Math.min(1, t / 7));
        const a = STAR_YAW + 0.1;
        const dist = 7.5 - k * 3.6;
        tmpA.set(player.pos.x + Math.sin(a) * dist, player.pos.y + 1.2 + (1 - k) * 1.2, player.pos.z + Math.cos(a) * dist);
        tmpB.set(player.pos.x - Math.sin(STAR_YAW) * 25, player.pos.y + 4.5, player.pos.z - Math.cos(STAR_YAW) * 25);
        camLook(tmpA, tmpB);
        if (t > 6.5) {
          player.camYaw = a;
          player.camPitch = 0.12;
          player.camDist = 4.2;
          player.camPos.copy(camera.position);
          setBeat('sitting');
        }
        return;
      }
      case 'sitting': {
        player.updateCamera(dt);
        ui.prompt('Rise');
        if (act) {
          ui.prompt(null);
          setBeat('rising');
        }
        break;
      }
      case 'rising': {
        player.updateCamera(dt);
        tb.sit = 0;
        tb.pose = 'idle';
        if (t > 0.3 && !S.flags.riseLine) { S.flags.riseLine = true; narrator.say(LINES.rise, { id: 'rise' }); }
        if (t > 1.6) {
          player.control = true;
          setBeat('shore');
          ui.hint(ui.isTouch ? 'Hold LISTEN to hear what is still here.' : 'Hold Q (or right mouse) to listen for echoes.', 9);
        }
        break;
      }
      case 'shore': {
        player.update(dt, input);
        player.updateCamera(dt);
        // Water just ahead? Offer to gather the flame from the star's reflection.
        const fx = -Math.sin(player.yaw), fz = -Math.cos(player.yaw);
        const ahead = player.groundAt(player.pos.x + fx * 1.6, player.pos.z + fz * 1.6).h;
        const nearWater = ahead < 0.03 && player.pos.y < 0.9;
        ui.prompt(nearWater ? 'Gather the flame' : null);
        if (player.blockedReason === 'gate' && !S.flags.gateHint) {
          S.flags.gateHint = true;
          ui.hint('Too dark to walk on without a flame. The star waits in the water.', 8);
        }
        if (nearWater && act) { ui.prompt(null); setBeat('flame'); }
        break;
      }
      case 'flame': {
        player.control = false;
        listening = false;
        bars(true);
        if (t < 0.05) {
          tb.pose = 'lower';
          S.flags.flameStart = player.pos.clone();
        }
        // Water-level side angle, slow quarter-circle arc.
        const fx = -Math.sin(player.yaw), fz = -Math.cos(player.yaw);
        const side = player.yaw + Math.PI * 0.72 + ease(Math.min(1, t / 7)) * 0.35;
        tmpB.set(player.pos.x + fx * 1.1, 0.35, player.pos.z + fz * 1.1);
        tmpA.set(tmpB.x + Math.sin(side) * 2.8, 1.25 + t * 0.05, tmpB.z + Math.cos(side) * 2.8);
        camLook(tmpA, tmpB.setY(0.45 + ease(Math.min(1, t / 7)) * 0.7));
        if (t > 1.6 && !S.flags.ripple) {
          S.flags.ripple = true;
          world.water.material.uniforms.uRippleCenter.value.set(player.pos.x + fx * 1.2, 0, player.pos.z + fz * 1.2);
          world.water.material.uniforms.uRippleTime.value = U.uTime.value;
          audio.shimmer(0.07, 3.5, 1320);
        }
        tb.climb = smooth(1.6, 3.6, t);
        tb.lit = smooth(3.4, 4.8, t);
        if (t > 3.4 && !S.flags.flameLine) { S.flags.flameLine = true; narrator.say(LINES.flame, { id: 'flame' }); }
        if (t > 5.0) tb.pose = 'raise';
        if (t > 6.4) tb.pose = 'idle';
        if (t > 7.2) {
          bars(false);
          tb.climb = 0;
          player.control = true;
          player.maxS = S_PLATFORM + 5;
          player.camYaw = player.yaw + Math.PI;  // turn to face the way on
          player.snapCamera();
          ui.chapter(1, 'THE FLAME');
          ui.hint('The way on lies inland, through the dark.', 7);
          setBeat('journey');
        }
        break;
      }
      case 'crane': {
        // Auto-walk: the bridge keeps forming under each step while the camera rises away.
        player.control = false;
        listening = false;
        bars(true);
        player.pos.z -= 1.5 * dt;
        player.pos.x += (BRIDGE_X - player.pos.x) * Math.min(1, dt * 2);
        player.yaw = 0;
        player.speed = 1.5;
        bridge.bornUpTo(player.pos.z - 1.4, U.uTime.value);
        const k = ease(Math.min(1, t / 5.5));
        tmpA.set(player.pos.x + 6 + k * 70, player.pos.y + 2 + k * 30, player.pos.z + 6 + k * 40);
        tmpB.set(player.pos.x, player.pos.y + 1 - k * 4, player.pos.z - k * 20);
        camLook(tmpA, tmpB);
        if (t > 1.2 && !S.flags.midLine) { S.flags.midLine = true; narrator.say(LINES.midBridge, { id: 'mid-bridge' }); }
        if (t > 6.2) {
          bars(false);
          player.control = true;
          player.camYaw = 0;
          player.camPos.copy(camera.position);
          setBeat('journey');
        }
        break;
      }
      case 'lighting': {
        player.control = false;
        listening = false;
        bars(true);
        const P = PLATFORM;
        if (t < 0.05) {
          player.pos.set(P.x, platform.topY, P.z + 1.7);
          player.yaw = 0;
          tb.pose = 'raise';
        }
        // Low angle up the seven steps, then an immense pull back as the world turns gold.
        const k = ease(smooth(5.4, 11.5, t));
        tmpA.set(P.x + 4 + k * 10, PLATEAU + 1.9 + k * 20, P.z + 13.5 + k * 55);
        tmpB.set(P.x, platform.topY + 2.4 + k * 6, P.z);
        camLook(tmpA, tmpB);
        if (t > 0.7 && !S.flags.litLine) { S.flags.litLine = true; narrator.say(LINES.letItBeLit, { id: 'let-it-be-lit' }); }
        if (t > 2.6) tb.pose = 'lower';
        if (t > 4.0 && !S.flags.silence) { S.flags.silence = true; audio.silence(1.0); }
        platform.lit = smooth(4.2, 6.4, t);
        if (t > 5.0 && !S.flags.boom) { S.flags.boom = true; audio.boom(); }
        platform.blaze = smooth(5.0, 6.6, t);
        if (t > 6.0) tb.pose = 'idle';
        if (t > 7.5) tb.lookYaw = 0;
        // The ring of warm light rolls outward.
        U.uGoldRadius.value = t > 5.2 ? (t - 5.2) * 75 : 0;
        U.uGold.value = smooth(5.4, 11, t);
        const g = U.uGold.value;
        world.starlight.color.copy(coldStar).lerp(warmStar, g);
        world.hemi.color.copy(coldSky).lerp(warmSky, g);
        world.hemi.intensity = 0.7 + g * 0.2;
        world.starlight.intensity = 0.5 + g * 0.15;
        if (t > 8 && !S.warmEnv) { S.warmEnv = true; world.env.setWarm(true); }
        if (t > 10.2 && !S.flags.stepLine) {
          S.flags.stepLine = true;
          narrator.say(LINES.step, { id: 'step' });
          ui.chapter(4, 'THE LIGHT');
          ui.setEchoes(echoes.gatheredCount(), ECHOES.length, true);
        }
        if (t > 13.5) {
          bars(false);
          S.flags.lit = true;
          player.control = true;
          player.maxS = Infinity;
          player.camYaw = Math.PI;   // the road runs on beyond the leaf
          player.snapCamera();
          setBeat('journey');
        }
        break;
      }
      case 'endSit': {
        player.control = false;
        listening = false;
        bars(true);
        if (t < 0.05) {
          player.pos.set(END.x, player.groundAt(END.x, END.z).h, END.z);
          player.yaw = STAR_YAW;
          tb.sit = 1;
        }
        // The opening image again: the river, the star, and you beside it.
        const k = ease(Math.min(1, t / 8));
        const a = STAR_YAW + 0.15 - k * 0.1;
        const dist = 3.2 + k * 5;
        tmpA.set(player.pos.x + Math.sin(a) * dist, player.pos.y + 1.1 + k * 1.4, player.pos.z + Math.cos(a) * dist);
        tmpB.set(player.pos.x - Math.sin(STAR_YAW) * 25, player.pos.y + 4.5 + k * 3, player.pos.z - Math.cos(STAR_YAW) * 25);
        camLook(tmpA, tmpB);
        if (t > 1.8 && !S.flags.neverLine) { S.flags.neverLine = true; narrator.say(LINES.never, { id: 'never' }); }
        if (t > 6.5) cin.uFade.value = 1 - smooth(6.5, 8.5, t);
        if (t > 8.6 && !S.flags.endShown) {
          S.flags.endShown = true;
          save.data.loops += 1;
          save.write();
          document.body.classList.remove('playing');
          ui.showHUD(false);
          ui.ending.show({ heard: echoes.gatheredCount(), total: ECHOES.length, closing: LINES.closing });
          audio.tone(110, 7, 0.1);
          setTimeout(() => narrator.say('Endless Destiny. From Echoes in the Dark Studio.', { id: 'ident' }), 4400);
          setTimeout(() => narrator.say(LINES.closing, { id: 'closing' }), 11500);
          setBeat('ended');
        }
        break;
      }
      case 'ended':
        return;
      case 'journey':
      default: {
        player.update(dt, input);
        player.updateCamera(dt);
        const s = info.s;
        if (s > 30 && !S.flags.dark) { S.flags.dark = true; ui.chapter(2, 'THE DARK'); narrator.say(LINES.dark, { id: 'dark' }); }
        if (s > S_RIM_SOUTH - 12 && !S.flags.rim) {
          S.flags.rim = true;
          player.bridgeActive = true;
          narrator.say(LINES.rim, { id: 'rim' });
        }
        // Gold dust drifting where the bridge will be: a hint to step into nothing.
        if (S.flags.rim && bridge.born === 0 && Math.random() < dt * 25) {
          bridge.dust.emit(BRIDGE_X + (Math.random() - 0.5) * 1.6, PLATEAU - 0.3 - Math.random(), RIM_SOUTH_Z - Math.random() * 5,
            0, 0.25 + Math.random() * 0.3, 0, 1.5 + Math.random());
        }
        if (player.onBridge) {
          if (!S.flags.bridge) { S.flags.bridge = true; ui.chapter(3, 'THE BRIDGE'); }
          bridge.bornUpTo(player.pos.z - 1.4, U.uTime.value);
          if (player.pos.z < (RIM_SOUTH_Z + RIM_NORTH_Z) / 2 && !S.flags.mid) { S.flags.mid = true; setBeat('crane'); }
        }
        if (player.pos.z < RIM_NORTH_Z - 3 && !S.flags.far) { S.flags.far = true; narrator.say(LINES.otherSide, { id: 'other-side' }); }
        const dPlat = Math.hypot(player.pos.x - PLATFORM.x, player.pos.z - PLATFORM.z);
        if (dPlat < 42 && !S.flags.pull) { S.flags.pull = true; narrator.say(LINES.pull, { id: 'pull' }); }
        // Fog thickens on the far side; thins as the leaf pulls you in.
        const fogWant = S.flags.lit ? 0.007 : (player.pos.z < RIM_NORTH_Z && dPlat > 26 ? 0.03 : 0.010);
        U.uFogDensity.value += (fogWant - U.uFogDensity.value) * Math.min(1, dt * 0.6);
        // Before the fire, the leaf draws a faint glimmer up its veins.
        if (!S.flags.lit) platform.lit = dPlat < 40 ? 0.04 + Math.sin(G.time * 1.3) * 0.03 : 0;
        if (!S.flags.lit && dPlat < 3.6 && player.pos.y > platform.topY - 0.1) {
          ui.prompt('Lower the flame');
          if (act) { ui.prompt(null); setBeat('lighting'); }
        } else if (!S.flags.lit) ui.prompt(null);
        if (!S.flags.lit && player.blockedReason === 'gate' && !S.flags.leafHint) {
          S.flags.leafHint = true;
          ui.hint('The light pulls you to the leaf.', 6);
        }
        if (S.flags.lit) {
          if (s > S_PLATFORM + 20 && !S.flags.road) { S.flags.road = true; ui.chapter(5, 'THE ROAD'); narrator.say(LINES.road, { id: 'road' }); }
          if (s > S_END - 24 && !S.flags.back) { S.flags.back = true; ui.chapter(6, 'THE RIVER'); narrator.say(LINES.back, { id: 'back' }); }
          // A road of light down to the water.
          for (let k = 0; k < 3; k++) {
            const ss = Math.min(S_END, s + Math.random() * 45);
            const p = pointOnPath(ss);
            const h = player.groundAt(p.x, p.z).h;
            roadDust.emit(p.x + (Math.random() - 0.5) * 2, h + 0.2 + Math.random() * 1.2, p.z + (Math.random() - 0.5) * 2,
              (Math.random() - 0.5) * 0.1, 0.05 + Math.random() * 0.1, (Math.random() - 0.5) * 0.1, 3 + Math.random() * 3);
          }
          const dEnd = Math.hypot(player.pos.x - END.x, player.pos.z - END.z);
          if (dEnd < 2.4) {
            ui.prompt('Sit beside the river');
            if (act) { ui.prompt(null); setBeat('endSit'); }
          } else if (!(dPlat < 3.6)) ui.prompt(null);
        }
        break;
      }
    }

    // Systems that run during play and cinematics alike.
    const g = echoes.update(dt, G.time, { playerPos: player.pos, listening, torchPos: tb.flameWorld, pulseRadius: S.pulseR });
    if (g) gatherEcho(g);
    updateListen(dt, listening);
    roadDust.update(dt, { drag: 0.2, lift: 0.02, swirl: 0.1, time: G.time });
  };
  return S;
}
