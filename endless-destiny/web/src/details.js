// The small things that make the world feel lived in and meant: leaf braziers that
// catch your flame as you pass, standing stones carved with the leaf, the two stones
// that mark where the bridge will be, the microphone stands of the song, gravel, dry
// river grass and drifting motes in the dark.
import * as THREE from 'three';
import { patchMaterial } from './shaders.js';
import { mulberry32 } from './noise.js';
import { pathInfo } from './terrainfield.js';
import { PATH, PATH_S, S_RIM_SOUTH, S_RIM_NORTH, S_PLATFORM, S_END, BRIDGE_X, RIM_SOUTH_Z, RIM_NORTH_Z, PLATFORM, END, START } from './config.js';
import { drawEmblem } from './emblem.js';
import { createFlame, createGlow, createParticles } from './fx.js';

function pointOnPath(s) {
  for (let i = 0; i < PATH.length - 1; i++) {
    if (s <= PATH_S[i + 1]) {
      const t = (s - PATH_S[i]) / (PATH_S[i + 1] - PATH_S[i]);
      const [ax, az] = PATH[i], [bx, bz] = PATH[i + 1];
      const len = PATH_S[i + 1] - PATH_S[i];
      return { x: ax + (bx - ax) * t, z: az + (bz - az) * t, tx: (bx - ax) / len, tz: (bz - az) / len };
    }
  }
  const n = PATH.length - 1;
  return { x: PATH[n][0], z: PATH[n][1], tx: 0, tz: -1 };
}

function emblemTexture(color = '#fff', size = 256) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const g = c.getContext('2d');
  drawEmblem(g, size, { color, stroke: 12, star: true, starColor: color });
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export function createDetails({ field, textures, stoneMat, quality, colliders }) {
  const group = new THREE.Group();
  group.name = 'details';
  const rand = mulberry32(4242);
  const emblemTex = emblemTexture();

  const bronze = patchMaterial(new THREE.MeshStandardMaterial({ color: 0x6f5530, metalness: 0.85, roughness: 0.5 }), 'detail-bronze');
  const iron = patchMaterial(new THREE.MeshStandardMaterial({ color: 0x0c0c0e, metalness: 0.7, roughness: 0.35 }), 'detail-iron');

  // Leaf braziers along the route: they wake as the flame passes and stay burning behind you.
  const braziers = [];
  const bowlGeo = new THREE.LatheGeometry([[0.0, 0.0], [0.2, 0.02], [0.34, 0.12], [0.4, 0.26], [0.37, 0.28], [0.3, 0.16], [0.0, 0.12]].map(([r, y]) => new THREE.Vector2(r, y)), 28);
  const postGeo = new THREE.CylinderGeometry(0.16, 0.24, 1.05, 12);
  const brazierStations = [];
  for (let s = 34; s < S_RIM_SOUTH - 6; s += 19) brazierStations.push(s);
  for (let s = S_PLATFORM + 22; s < S_END - 14; s += 20) brazierStations.push(s);
  brazierStations.forEach((s, i) => {
    const p = pointOnPath(s);
    const side = i % 2 ? 1 : -1;
    const x = p.x - p.tz * side * 3.4, z = p.z + p.tx * side * 3.4;
    const y = field.sample(x, z);
    const g = new THREE.Group();
    g.position.set(x, y, z);
    const post = new THREE.Mesh(postGeo, stoneMat);
    post.position.y = 0.52;
    post.castShadow = true;
    const bowl = new THREE.Mesh(bowlGeo, bronze);
    bowl.position.y = 1.02;
    bowl.castShadow = true;
    g.add(post, bowl);
    const flame = createFlame({ intensity: 5, turbulence: 0.4, seed: rand() });
    flame.position.y = 1.2;
    flame.scale.set(0.34, 0.001, 1);
    flame.visible = false;
    const glow = createGlow(0xffa648, 2.2, 0);
    glow.position.y = 1.4;
    g.add(flame, glow);
    group.add(g);
    colliders.push({ x, z, r: 0.35 });
    braziers.push({ g, flame, glow, lit: 0, target: 0, pos: new THREE.Vector3(x, y + 1.3, z) });
  });

  // Standing stones carved with the leaf; the carving answers when you listen.
  const stones = [];
  const slabGeo = new THREE.BoxGeometry(0.95, 3.3, 0.42, 1, 6, 1);
  {
    const pa = slabGeo.attributes.position;
    for (let k = 0; k < pa.count; k++) {
      const y = pa.getY(k);
      const taper = 1 - (y + 1.65) / 3.3 * 0.22;
      pa.setX(k, pa.getX(k) * taper + Math.sin(y * 3 + k) * 0.01);
      pa.setZ(k, pa.getZ(k) * taper);
      if (y > 1.6) pa.setY(k, y + (pa.getX(k) > 0 ? -0.12 : 0.05));
    }
    slabGeo.computeVertexNormals();
  }
  const carveMat = new THREE.MeshBasicMaterial({ map: emblemTex, color: 0x000000, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });
  const stoneSpots = [
    [START.x + 4.5, START.z - 1.5, 0.9], [2, -20, -0.4], [13.5, -95, 0.2], [3.6, -137.5, 0.05], [16.4, -137.5, -0.05],
    [3.8, -233.5, Math.PI + 0.05], [16.2, -233.5, Math.PI - 0.05], [22, -270, 0.4], [-1, -330, 0.7], [END.x + 6, END.z + 3, 2.4],
  ];
  for (const [x, z, rotY] of stoneSpots) {
    const y = field.sample(x, z);
    const slab = new THREE.Mesh(slabGeo, stoneMat);
    slab.position.set(x, y + 1.45, z);
    slab.rotation.set((rand() - 0.5) * 0.06, rotY, (rand() - 0.5) * 0.08);
    slab.castShadow = true;
    slab.receiveShadow = true;
    const carve = new THREE.Mesh(new THREE.PlaneGeometry(0.72, 0.72), carveMat.clone());
    carve.position.set(0, 0.55, 0.215);
    slab.add(carve);
    const back = carve.clone();
    back.rotation.y = Math.PI;
    back.position.z = -0.215;
    slab.add(back);
    group.add(slab);
    colliders.push({ x, z, r: 0.6 });
    stones.push({ slab, carve, back, glow: 0 });
  }

  // The microphone stand: at the far end of the bridge, and alone at the river's edge at the end.
  function micStand() {
    const m = new THREE.Group();
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.19, 0.03, 24), iron);
    base.position.y = 0.015;
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.011, 0.013, 1.52, 10), iron);
    pole.position.y = 0.78;
    const clip = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.06, 10), iron);
    clip.position.set(0, 1.56, -0.02);
    clip.rotation.x = 0.5;
    const mic = new THREE.Group();
    mic.position.set(0, 1.6, -0.06);
    mic.rotation.x = 0.55;
    const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.014, 0.16, 12), iron);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.03, 16, 12), patchMaterial(new THREE.MeshStandardMaterial({ color: 0x2a2a2e, metalness: 0.9, roughness: 0.3 }), 'mic-grille'));
    head.position.y = 0.1;
    mic.add(handle, head);
    m.add(base, pole, clip, mic);
    m.traverse((o) => { if (o.isMesh) o.castShadow = true; });
    return m;
  }
  const micBridge = micStand();
  micBridge.position.set(BRIDGE_X + 1.6, field.sample(BRIDGE_X + 1.6, RIM_NORTH_Z - 3), RIM_NORTH_Z - 3);
  const micRiver = micStand();
  const mrx = END.x - 1.4, mrz = END.z - 1.6;
  micRiver.position.set(mrx, field.sample(mrx, mrz), mrz);
  micRiver.rotation.y = 0.6;
  group.add(micBridge, micRiver);
  colliders.push({ x: mrx, z: mrz, r: 0.25 });

  // Gravel and small stones spilling along the edges of the route.
  const gravelSeeds = [];
  const nGravel = Math.round(1500 * quality.props);
  for (let i = 0; i < nGravel; i++) {
    const s = rand() * S_END;
    if (s > S_RIM_SOUTH - 1 && s < S_RIM_NORTH + 1) continue;
    const p = pointOnPath(s);
    const side = rand() < 0.5 ? -1 : 1;
    const d = 1.3 + Math.pow(rand(), 1.3) * 5;
    const x = p.x - p.tz * side * d + (rand() - 0.5), z = p.z + p.tx * side * d + (rand() - 0.5);
    const r = Math.hypot(x - PLATFORM.x, z - PLATFORM.z);
    if (r < PLATFORM.radius + 0.5) continue;
    gravelSeeds.push([x, z]);
  }

  // Dry river grass: pale, wind-bent tufts on the shores and the open plateau.
  const bladeCanvas = document.createElement('canvas');
  bladeCanvas.width = 64; bladeCanvas.height = 128;
  {
    const g = bladeCanvas.getContext('2d');
    for (let b = 0; b < 9; b++) {
      const x0 = 10 + b * 5 + Math.random() * 4;
      const lean = (Math.random() - 0.5) * 26;
      const h = 70 + Math.random() * 55;
      const grd = g.createLinearGradient(0, 128, 0, 128 - h);
      grd.addColorStop(0, 'rgba(92,84,66,1)');
      grd.addColorStop(1, 'rgba(196,182,150,0.95)');
      g.strokeStyle = grd;
      g.lineWidth = 2 + Math.random() * 1.5;
      g.beginPath();
      g.moveTo(x0, 128);
      g.quadraticCurveTo(x0 + lean * 0.3, 128 - h * 0.6, x0 + lean, 128 - h);
      g.stroke();
    }
  }
  const bladeTex = new THREE.CanvasTexture(bladeCanvas);
  bladeTex.colorSpace = THREE.SRGBColorSpace;
  const tuftGeo = new THREE.PlaneGeometry(0.7, 0.9, 1, 3);
  tuftGeo.translate(0, 0.45, 0);
  const tuftGeo2 = tuftGeo.clone().rotateY(Math.PI / 2);
  const merged = new THREE.BufferGeometry();
  {
    const a = tuftGeo.toNonIndexed(), b = tuftGeo2.toNonIndexed();
    for (const name of ['position', 'normal', 'uv']) {
      const A = a.attributes[name].array, B = b.attributes[name].array;
      const arr = new Float32Array(A.length + B.length);
      arr.set(A); arr.set(B, A.length);
      merged.setAttribute(name, new THREE.BufferAttribute(arr, a.attributes[name].itemSize));
    }
    // Normals point up so the tufts light like the ground beneath them.
    const n = merged.attributes.normal;
    for (let i = 0; i < n.count; i++) n.setXYZ(i, 0, 1, 0);
  }
  const grassMat = patchMaterial(new THREE.MeshStandardMaterial({
    map: bladeTex, alphaTest: 0.35, side: THREE.DoubleSide, roughness: 0.95, color: 0x5e574b,
  }), 'grass', {
    beginVertex: /* glsl */`
      float gh = clamp(position.y / 0.9, 0.0, 1.0);
      vec4 gw = vec4(0.0, 0.0, 0.0, 1.0);
      #ifdef USE_INSTANCING
        gw = instanceMatrix * gw;
      #endif
      float gust = sin(uTime * 1.3 + gw.x * 0.35 + gw.z * 0.2) * 0.5 + sin(uTime * 2.7 + gw.z * 0.8) * 0.25;
      transformed.x += gust * 0.12 * gh * gh;
      transformed.z += gust * 0.05 * gh * gh;
    `,
  });
  const grassSpots = [];
  const nGrass = Math.round(1500 * quality.props);
  for (let i = 0; i < nGrass * 3 && grassSpots.length < nGrass; i++) {
    let x, z;
    const pick = rand();
    // River grass grows only on the two shores.
    if (pick < 0.5) { const a = rand() * Math.PI * 2, r = 3 + rand() * 34; x = START.x - 4 + Math.cos(a) * r; z = START.z - 4 + Math.sin(a) * r; }
    else { const a = rand() * Math.PI * 2, r = 3 + rand() * 34; x = END.x + Math.cos(a) * r; z = END.z + 6 + Math.sin(a) * r; }
    const h = field.sample(x, z);
    if (h < 0.85) continue;           // the wet sand at the waterline stays bare
    const n = field.normal(x, z);
    if (n[1] < 0.9) continue;
    if (pathInfo(x, z).d < 1.6) continue;
    if (Math.hypot(x - START.x, z - START.z) < 7 || Math.hypot(x - END.x, z - END.z) < 7) continue;
    if (Math.hypot(x - PLATFORM.x, z - PLATFORM.z) < PLATFORM.radius + 1) continue;
    grassSpots.push([x, h, z]);
  }

  // Build instanced ground cover in spatial cells so it culls with the view.
  const CELL = 40;
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), pv = new THREE.Vector3(), sv = new THREE.Vector3();
  function instanceCells(points, geo, mat, make, shadows) {
    const cells = new Map();
    for (const pt of points) {
      const key = Math.floor(pt[0] / CELL) + ',' + Math.floor(pt[pt.length - 1] / CELL);
      if (!cells.has(key)) cells.set(key, []);
      cells.get(key).push(pt);
    }
    for (const list of cells.values()) {
      const im = new THREE.InstancedMesh(geo, mat, list.length);
      list.forEach((pt, i) => { make(pt, m4); im.setMatrixAt(i, m4); });
      im.instanceMatrix.needsUpdate = true;
      im.computeBoundingSphere();
      im.castShadow = shadows;
      im.receiveShadow = true;
      group.add(im);
    }
  }
  instanceCells(grassSpots, merged, grassMat, ([x, h, z], out) => {
    e.set(0, rand() * Math.PI, 0);
    q.setFromEuler(e);
    const k = 0.35 + rand() * 0.45;
    out.compose(pv.set(x, h - 0.03, z), q, sv.set(k, k * (0.55 + rand() * 0.5), k));
  }, false);

  const api = {
    group, braziers, stones, micBridge, micRiver, gravelSeeds, instanceCells,
    motes: createParticles({ count: 320, color: 0xb9c6ff, size: 0.03 }),
    update(dt, t, { torchPos, torchLit, listening, playerPos }) {
      for (const b of braziers) {
        if (torchLit > 0.5 && b.target === 0 && b.pos.distanceTo(torchPos) < 4.2) {
          b.target = 1;
          api.onIgnite?.(b);
        }
        b.lit += (b.target - b.lit) * Math.min(1, dt * 2.5);
        b.flame.visible = b.lit > 0.02;
        b.flame.material.uniforms.uTime.value = t;
        b.flame.material.uniforms.uLife.value = b.lit;
        b.flame.scale.set(0.34, 0.75 * b.lit, 1);
        b.glow.material.opacity = 0.32 * b.lit;
      }
      for (const s of stones) {
        const near = s.slab.position.distanceTo(playerPos) < 30;
        const want = (listening && near ? 1 : 0) * 0.9 + 0.08;
        s.glow += (want - s.glow) * Math.min(1, dt * 2);
        const c = s.glow;
        s.carve.material.color.setRGB(0.95 * c, 0.62 * c, 0.26 * c);
        s.back.material.color.copy(s.carve.material.color);
      }
      // Drifting motes around the walker: the dark is never empty.
      if (Math.random() < dt * 30) {
        const a = Math.random() * Math.PI * 2, r = 3 + Math.random() * 16;
        api.motes.emit(playerPos.x + Math.cos(a) * r, playerPos.y + 0.3 + Math.random() * 3, playerPos.z + Math.sin(a) * r,
          (Math.random() - 0.5) * 0.12, (Math.random() - 0.3) * 0.08, (Math.random() - 0.5) * 0.12, 5 + Math.random() * 5);
      }
      api.motes.update(dt, { drag: 0.1, swirl: 0.06, time: t });
    },
    reset() {
      for (const b of braziers) { b.lit = 0; b.target = 0; b.flame.visible = false; b.glow.material.opacity = 0; }
    },
  };
  return api;
}
