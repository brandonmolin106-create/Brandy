// The Torchbearer: a tall hooded figure in charcoal-black wool, a line of gold thread
// at the hem and cuffs, dark leather gloves, a slim bronze torch with a leaf-shaped head.
// Always seen from behind. A small procedural rig drives shoulders, elbows, hood and body
// through poses: walk, idle, raise, lower (kneel), sit.
import * as THREE from 'three';
import { patchMaterial } from './shaders.js';
import { createFlame, createGlow, createParticles } from './fx.js';

function fabricNormalMap() {
  const n = 256;
  const data = new Uint8Array(n * n * 4);
  const hgt = new Float32Array(n * n);
  for (let y = 0; y < n; y++) {
    for (let x = 0; x < n; x++) {
      const twill = Math.sin((x + y) * 0.9) * 0.5 + Math.sin(y * 2.2) * 0.25;
      hgt[y * n + x] = twill + (Math.random() - 0.5) * 0.9;
    }
  }
  for (let y = 0; y < n; y++) {
    for (let x = 0; x < n; x++) {
      const l = hgt[y * n + ((x - 1 + n) % n)], r = hgt[y * n + ((x + 1) % n)];
      const d = hgt[((y - 1 + n) % n) * n + x], u = hgt[((y + 1) % n) * n + x];
      const nx = (l - r) * 0.5, ny = (d - u) * 0.5, nz = 1;
      const len = Math.hypot(nx, ny, nz);
      const k = (y * n + x) * 4;
      data[k] = (nx / len * 0.5 + 0.5) * 255;
      data[k + 1] = (ny / len * 0.5 + 0.5) * 255;
      data[k + 2] = (nz / len * 0.5 + 0.5) * 255;
      data[k + 3] = 255;
    }
  }
  const tex = new THREE.DataTexture(data, n, n);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(10, 10);
  tex.generateMipmaps = true;
  tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.needsUpdate = true;
  return tex;
}

// Joint targets for each pose. Angles in radians.
const POSES = {
  // Shoulder/elbow x > 0 swings the arm forward (toward -Z, where the figure faces).
  // compress: how far the robe folds down (kneeling, sitting). lean: upper body bows forward.
  idle:  { compress: 0, lean: 0.02, rSh: [0.62, 0.0, -0.08], rEl: 1.05, lSh: [0.05, 0, 0.12], lEl: 0.25, hood: [0.05, 0], torchTilt: -0.12 },
  walk:  { compress: 0, lean: 0.07, rSh: [0.7, 0.0, -0.08], rEl: 1.0, lSh: [0.0, 0, 0.12], lEl: 0.3, hood: [0.08, 0], torchTilt: -0.18 },
  raise: { compress: 0, lean: -0.05, rSh: [2.75, 0.0, -0.1], rEl: 0.18, lSh: [0.1, 0, 0.15], lEl: 0.25, hood: [-0.2, 0], torchTilt: 0 },
  lower: { compress: 0.4, lean: 0.5, rSh: [0.75, 0.0, -0.05], rEl: 0.1, lSh: [0.5, 0, 0.2], lEl: 0.6, hood: [0.25, 0], torchTilt: -1.35 },
  sit:   { compress: 0.43, lean: 0.12, rSh: [0.35, 0.0, 0.05], rEl: 1.25, lSh: [0.35, 0, -0.05], lEl: 1.3, hood: [0.12, 0], torchTilt: 0.05 },
};

export function createTorchbearer(quality) {
  const root = new THREE.Group();
  root.name = 'torchbearer';
  const body = new THREE.Group();
  root.add(body);

  const robeUniforms = { uWalk: { value: 0 }, uPhase: { value: 0 }, uSit: { value: 0 }, uKneel: { value: 0 } };
  const robeMat = patchMaterial(new THREE.MeshPhysicalMaterial({
    color: 0x1b1a20, roughness: 0.9, metalness: 0,
    sheen: 1, sheenColor: new THREE.Color(0x35314a), sheenRoughness: 0.7,
    normalMap: fabricNormalMap(), normalScale: new THREE.Vector2(0.35, 0.35),
  }), 'robe', {
    uniforms: robeUniforms,
    vertexPars: 'uniform float uWalk, uPhase, uSit, uKneel;',
    beginNormal: /* glsl */`
      float angN = atan(position.z, position.x);
      float dF = cos(angN * 9.0 + sin(angN * 3.0) * 1.5) * (9.0 + cos(angN * 3.0) * 4.5) * 0.5 + cos(angN * 17.0 + 1.3) * 4.25;
      float fAmt = (1.0 - smoothstep(0.25, 1.35, position.y)) * 0.022;
      vec3 tangN = vec3(-sin(angN), 0.0, cos(angN));
      objectNormal = normalize(objectNormal - tangN * dF * fAmt / max(length(position.xz), 0.12));
    `,
    beginVertex: /* glsl */`
      float angV = atan(position.z, position.x);
      float folds = sin(angV * 9.0 + sin(angV * 3.0) * 1.5) * 0.5 + sin(angV * 17.0 + 1.3) * 0.25;
      transformed.xz += normalize(position.xz + 1e-4) * folds * (1.0 - smoothstep(0.25, 1.35, position.y)) * 0.022;
      float low = 1.0 - smoothstep(0.0, 1.05, position.y);
      low *= low;
      // Walking: the hem swings with each step and trails behind.
      transformed.x += sin(uPhase * 2.0 + angV * 2.0) * 0.024 * low * uWalk;
      transformed.z += low * uWalk * 0.08 + sin(uPhase * 2.0 + angV) * 0.014 * low * uWalk;
      // Night air moves the hem even at rest.
      transformed.x += sin(uTime * 0.8 + position.y * 3.0 + angV) * 0.005 * low;
      // Sitting or kneeling: the robe pools out over the ground.
      float pool = max(uSit, uKneel * 0.8);
      transformed.xz *= 1.0 + pool * low * 0.45;
      transformed.z -= pool * low * 0.12;
    `,
  });
  const woolMat = patchMaterial(new THREE.MeshPhysicalMaterial({
    color: 0x1b1a20, roughness: 0.9, metalness: 0,
    sheen: 1, sheenColor: new THREE.Color(0x35314a), sheenRoughness: 0.7,
    normalMap: robeMat.normalMap, normalScale: new THREE.Vector2(0.3, 0.3),
  }), 'wool');
  const goldMat = patchMaterial(new THREE.MeshStandardMaterial({
    color: 0x5a3c12, emissive: 0xffa640, emissiveIntensity: 0.55, metalness: 1, roughness: 0.3,
  }), 'gold-thread');
  const gloveMat = patchMaterial(new THREE.MeshStandardMaterial({ color: 0x1a1411, roughness: 0.48, metalness: 0 }), 'glove');
  const bronzeMat = patchMaterial(new THREE.MeshStandardMaterial({
    color: 0x6c5a34, metalness: 0.88, roughness: 0.42, emissive: 0xffb050, emissiveIntensity: 0,
  }), 'bronze');
  const voidMat = new THREE.MeshBasicMaterial({ color: 0x000000 });

  // Robe: floor length, broad across the shoulders.
  const robeProfile = [
    [0.405, 0.0], [0.395, 0.08], [0.355, 0.38], [0.305, 0.74], [0.268, 1.0], [0.272, 1.2],
    [0.288, 1.37], [0.272, 1.47], [0.2, 1.53], [0.1, 1.575], [0.05, 1.6],
  ].map(([r, y]) => new THREE.Vector2(r, y));
  const skirtGeo = new THREE.LatheGeometry(robeProfile.filter((v) => v.y <= 1.2), 56);
  skirtGeo.scale(1.16, 1, 0.9);
  const robe = new THREE.Mesh(skirtGeo, robeMat);
  robe.castShadow = true;
  body.add(robe);
  // Everything above the waist hangs from here, so the figure can bow, kneel and sit.
  const upper = new THREE.Group();
  upper.position.y = 1.0;
  body.add(upper);
  const torsoGeo = new THREE.LatheGeometry(robeProfile.filter((v) => v.y >= 1.0), 56);
  torsoGeo.scale(1.16, 1, 0.9);
  const torso = new THREE.Mesh(torsoGeo, woolMat);
  torso.position.y = -1.0;
  torso.castShadow = true;
  upper.add(torso);
  const hem = new THREE.Mesh(new THREE.TorusGeometry(0.4, 0.006, 6, 64), goldMat);
  hem.rotation.x = Math.PI / 2;
  hem.scale.set(1.16, 0.9, 1);
  hem.position.y = 0.035;
  body.add(hem);
  // A cord belt, knotted, with its ends hanging.
  const belt = new THREE.Mesh(new THREE.TorusGeometry(0.272, 0.011, 8, 48), gloveMat);
  belt.rotation.x = Math.PI / 2;
  belt.scale.set(1.16, 0.9, 1);
  belt.position.y = 0.05;
  upper.add(belt);
  const cordEnds = new THREE.Group();
  cordEnds.position.set(0.12, 0.04, -0.23);
  upper.add(cordEnds);
  for (const [dx, len] of [[0, 0.34], [0.035, 0.28]]) {
    const c = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, len, 6), gloveMat);
    c.position.set(dx, -len / 2, 0);
    cordEnds.add(c);
  }

  // Hood: pivots at the neck so it can bow, lift and turn.
  const hoodPivot = new THREE.Group();
  hoodPivot.position.set(0, 0.52, 0.02);
  upper.add(hoodPivot);
  const hoodProfile = [
    [0.0, -0.05], [0.15, -0.02], [0.185, 0.08], [0.18, 0.2], [0.155, 0.3], [0.1, 0.38], [0.04, 0.43], [0.0, 0.445],
  ].map(([r, y]) => new THREE.Vector2(r, y));
  const hood = new THREE.Mesh(new THREE.LatheGeometry(hoodProfile, 36), woolMat);
  hood.position.set(0, 0, 0.02);
  hood.rotation.x = -0.12;
  hood.scale.set(1.05, 1, 1.12);
  hood.castShadow = true;
  hoodPivot.add(hood);
  const face = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 12), voidMat);
  face.scale.set(0.95, 1.1, 0.45);
  face.position.set(0, 0.15, -0.125);
  hoodPivot.add(face);
  // The hood's drape over the shoulders.
  const mantle = new THREE.Mesh(new THREE.LatheGeometry([
    [0.3, 1.26], [0.3, 1.36], [0.27, 1.45], [0.2, 1.51], [0.13, 1.55],
  ].map(([r, y]) => new THREE.Vector2(r, y)), 48), woolMat);
  mantle.scale.set(1.2, 1, 0.95);
  mantle.position.y = -1.0;
  mantle.castShadow = true;
  upper.add(mantle);

  // Arms: shoulder -> elbow -> hand, wide sleeves flaring at the cuff.
  const sleeveMat = woolMat.clone();
  sleeveMat.side = THREE.DoubleSide;
  sleeveMat.onBeforeCompile = woolMat.onBeforeCompile;
  sleeveMat.customProgramCacheKey = () => 'ed-wool-sleeve';
  const cuffMat = goldMat.clone();
  cuffMat.emissiveIntensity = 0.18;
  cuffMat.onBeforeCompile = goldMat.onBeforeCompile;
  cuffMat.customProgramCacheKey = goldMat.customProgramCacheKey;
  const sleeve = (len, r0, r1) => {
    const g = new THREE.CylinderGeometry(r1, r0, len, 16, 1, true);
    g.translate(0, -len / 2, 0);
    const m = new THREE.Mesh(g, sleeveMat);
    m.castShadow = true;
    return m;
  };
  function makeArm(side) {
    const shoulder = new THREE.Group();
    shoulder.position.set(0.27 * side, 0.42, 0.02);
    upper.add(shoulder);
    shoulder.add(sleeve(0.3, 0.085, 0.1));
    const elbow = new THREE.Group();
    elbow.position.y = -0.3;
    shoulder.add(elbow);
    elbow.add(sleeve(0.28, 0.1, 0.135));
    const cuff = new THREE.Mesh(new THREE.TorusGeometry(0.133, 0.0035, 6, 32), cuffMat);
    cuff.rotation.x = Math.PI / 2;
    cuff.position.y = -0.275;
    elbow.add(cuff);
    const hand = new THREE.Group();
    hand.position.y = -0.33;
    elbow.add(hand);
    const glove = new THREE.Mesh(new THREE.SphereGeometry(0.052, 14, 10), gloveMat);
    glove.scale.set(0.85, 1.25, 0.75);
    glove.castShadow = true;
    hand.add(glove);
    return { shoulder, elbow, hand };
  }
  const R = makeArm(1);
  const L = makeArm(-1);

  // The torch, held in the right hand.
  const torch = new THREE.Group();
  R.hand.add(torch);
  const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.018, 0.7, 10), bronzeMat);
  rod.position.y = 0.2;
  rod.castShadow = true;
  torch.add(rod);
  const leafProfile = [[0.0, 0.0], [0.03, 0.025], [0.046, 0.06], [0.04, 0.1], [0.022, 0.13], [0.0, 0.15]]
    .map(([r, y]) => new THREE.Vector2(r, y));
  const leafGeo = new THREE.LatheGeometry(leafProfile, 16);
  leafGeo.scale(1, 1, 0.38);
  const leafHead = new THREE.Mesh(leafGeo, bronzeMat);
  leafHead.position.y = 0.54;
  torch.add(leafHead);
  const flameAnchor = new THREE.Group();
  flameAnchor.position.y = 0.65;
  torch.add(flameAnchor);
  const flame = createFlame({ intensity: 7, turbulence: 0.22 });
  flame.scale.set(0.15, 0.44, 1);
  flameAnchor.add(flame);
  const glow = createGlow(0xffa648, 1.6, 0.35);
  glow.position.y = 0.12;
  flameAnchor.add(glow);
  const streak = createGlow(0xffb060, 1.0, 0.16, true);
  streak.position.y = 0.12;
  flameAnchor.add(streak);
  // Gold climbing the torch head when the flame is gathered.
  const climb = createGlow(0xffc060, 0.5, 0);
  climb.position.y = 0.55;
  torch.add(climb);

  const light = new THREE.PointLight(0xffa24c, 0, 45, 2);
  light.position.y = 0.16;
  if (quality.shadows > 0) {
    light.castShadow = true;
    light.shadow.mapSize.set(quality.shadows, quality.shadows);
    light.shadow.camera.near = 0.15;
    light.shadow.camera.far = 30;
    light.shadow.bias = -0.004;
    light.shadow.normalBias = 0.03;
    light.shadow.radius = 3;
  }
  flameAnchor.add(light);

  const embers = createParticles({ count: 110, color: 0xffb35a, size: 0.035 });

  // Current joint angles (blended toward the pose weights each frame).
  const cur = JSON.parse(JSON.stringify(POSES.idle));
  const tmp = new THREE.Vector3();

  const tb = {
    root, body, robe, flame, glow, streak, light, embers, flameAnchor, bronzeMat, torch,
    lit: 0,             // 0..1 flame strength
    climb: 0,           // 0..1 gold climbing the torch head (ignition)
    power: 1,           // grows with each echo gathered
    walk: 0, phase: 0,
    sit: 0,             // photo mode shortcut for the sitting pose
    pose: 'idle',       // idle | walk | raise | lower | sit
    lookYaw: 0,         // hood turn toward something interesting
    flameWorld: new THREE.Vector3(),
    onStep: null,
    update(dt, t, { speed = 0 } = {}) {
      tb.walk += (Math.min(speed / 3, 1) - tb.walk) * Math.min(1, dt * 6);
      const prevPhase = tb.phase;
      tb.phase += dt * (2.2 + speed * 1.1) * (tb.walk > 0.05 ? 1 : 0.3);
      // Footfalls twice per cycle.
      if (tb.walk > 0.2 && Math.floor(prevPhase / Math.PI) !== Math.floor(tb.phase / Math.PI)) tb.onStep?.();

      let key = tb.pose;
      if (key === 'idle' && tb.walk > 0.15) key = 'walk';
      if (tb.sit > 0.5) key = 'sit';
      const target = POSES[key];
      const k = Math.min(1, dt * (key === 'sit' || key === 'lower' ? 2.2 : 4));
      cur.compress += (target.compress - cur.compress) * k;
      cur.lean += (target.lean - cur.lean) * k;
      cur.rEl += (target.rEl - cur.rEl) * k;
      cur.lEl += (target.lEl - cur.lEl) * k;
      cur.torchTilt += (target.torchTilt - cur.torchTilt) * k;
      for (let i = 0; i < 3; i++) {
        cur.rSh[i] += (target.rSh[i] - cur.rSh[i]) * k;
        cur.lSh[i] += (target.lSh[i] - cur.lSh[i]) * k;
      }
      cur.hood[0] += (target.hood[0] - cur.hood[0]) * k;
      cur.hood[1] += (tb.lookYaw - cur.hood[1]) * Math.min(1, dt * 2);

      // Breathing and stride.
      const breath = Math.sin(t * 1.7) * 0.5 + 0.5;
      const w = tb.walk;
      const bob = Math.abs(Math.sin(tb.phase)) * 0.03 * w;
      body.position.y = bob;
      body.rotation.z = Math.sin(tb.phase) * 0.02 * w;
      body.rotation.y = Math.sin(tb.phase) * 0.025 * w;
      robe.scale.y = 1 - cur.compress;
      upper.position.y = 1.0 * (1 - cur.compress) + breath * 0.004;
      upper.rotation.x = -(cur.lean + w * 0.03 * Math.sin(tb.phase * 2));
      robeUniforms.uWalk.value = w;
      robeUniforms.uPhase.value = tb.phase;
      robeUniforms.uSit.value = key === 'sit' ? Math.min(1, cur.compress / 0.43) : 0;
      robeUniforms.uKneel.value = key === 'lower' ? Math.min(1, cur.compress / 0.4) : 0;

      const swing = Math.sin(tb.phase) * 0.28 * w;
      R.shoulder.rotation.set(cur.rSh[0] + swing * 0.12 + breath * 0.01, cur.rSh[1], cur.rSh[2]);
      R.elbow.rotation.x = cur.rEl;
      L.shoulder.rotation.set(cur.lSh[0] - swing, cur.lSh[1], cur.lSh[2]);
      L.elbow.rotation.x = cur.lEl + Math.max(0, -swing) * 0.4;
      // Keep the torch near upright whatever the arm does.
      torch.rotation.x = -(R.shoulder.rotation.x + R.elbow.rotation.x) + cur.torchTilt;
      torch.rotation.z = -R.shoulder.rotation.z;
      hoodPivot.rotation.set(cur.hood[0] + breath * 0.01, cur.hood[1], Math.sin(tb.phase) * 0.02 * w);

      const on = tb.lit;
      const flick = 1 + Math.sin(t * 7.3) * 0.025 + Math.sin(t * 13.1) * 0.015;
      flame.visible = on > 0.01;
      flame.material.uniforms.uTime.value = t;
      flame.material.uniforms.uLife.value = on;
      flame.scale.set(0.15, 0.44 * (0.6 + 0.4 * on) * (1 + (tb.power - 1) * 0.4), 1);
      glow.material.opacity = 0.35 * on;
      streak.material.opacity = 0.16 * on;
      climb.material.opacity = tb.climb * (1 - on) * 0.9;
      light.intensity = on * 14 * flick * tb.power;
      bronzeMat.emissiveIntensity = on * 0.05 + tb.climb * 0.8 * (1 - on * 0.9);
      flameAnchor.getWorldPosition(tb.flameWorld);
      tb.flameWorld.y += 0.16;
      if (on > 0.2 && Math.random() < dt * 9) {
        const p = tb.flameWorld;
        embers.emit(p.x + (Math.random() - 0.5) * 0.05, p.y + 0.15, p.z + (Math.random() - 0.5) * 0.05,
          (Math.random() - 0.5) * 0.12, 0.25 + Math.random() * 0.25, (Math.random() - 0.5) * 0.12, 2.5 + Math.random() * 2.5);
      }
      embers.update(dt, { drag: 0.3, lift: 0.05, swirl: 0.15, time: t });
    },
    handWorld(out = tmp) { return R.hand.getWorldPosition(out); },
    snapPose(name) {
      Object.assign(cur, JSON.parse(JSON.stringify(POSES[name])));
      tb.pose = name;
    },
  };
  return tb;
}
