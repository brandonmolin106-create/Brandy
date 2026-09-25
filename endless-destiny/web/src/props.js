// Photoscanned rocks, cliffs and dead trees (Poly Haven, CC0), scattered along the journey.
import * as THREE from 'three';
import { mulberry32, smoothstep } from './noise.js';
import { pathInfo } from './terrainfield.js';
import { PATH, PATH_S, S_RIM_SOUTH, S_RIM_NORTH, S_PLATFORM, S_END, BRIDGE_X, RIM_SOUTH_Z, RIM_NORTH_Z, PLATFORM } from './config.js';
import { patchMaterial } from './shaders.js';

const CELL = 48;

// size = target largest dimension in metres (min..max), sink = fraction pushed into the ground.
const TYPES = {
  pebble1: { file: 'moon_rock_01', size: [0.5, 2.4], sink: 0.25 },
  pebble3: { file: 'moon_rock_03', size: [0.6, 3.0], sink: 0.25 },
  pebble5: { file: 'moon_rock_05', size: [0.8, 4.2], sink: 0.3 },
  boulder2: { file: 'namaqualand_boulder_02', size: [3.5, 8.0], sink: 0.18 },
  boulder4: { file: 'namaqualand_boulder_04', size: [2.5, 6.0], sink: 0.2 },
  cliff: { file: 'namaqualand_cliff_02', size: [10, 26], sink: 0.3, maxSlope: 60 },
  tree: { file: 'dead_quiver_trunk', size: [2.6, 5.2], sink: 0.02, upright: true, maxSlope: 22 },
};

export async function loadProps(loader, field, quality) {
  const files = [...new Set(Object.values(TYPES).map((t) => t.file))];
  const loaded = {};
  await Promise.all(files.map(async (f) => {
    const gltf = await loader.loadAsync(`assets/models/${f}.glb`);
    let mesh = null;
    gltf.scene.traverse((o) => { if (o.isMesh && !mesh) mesh = o; });
    mesh.updateWorldMatrix(true, false);
    // Positions arrive quantized (normalized int16); expand to float before moving them,
    // otherwise the transform would clamp them back into [-1, 1].
    const geo = new THREE.BufferGeometry();
    for (const name of ['position', 'normal', 'uv']) {
      const a = mesh.geometry.getAttribute(name);
      if (!a) continue;
      const n = a.itemSize >= 3 && name !== 'uv' ? 3 : 2;
      const arr = new Float32Array(a.count * n);
      for (let i = 0; i < a.count; i++) {
        arr[i * n] = a.getX(i);
        arr[i * n + 1] = a.getY(i);
        if (n === 3) arr[i * n + 2] = a.getZ(i);
      }
      geo.setAttribute(name, new THREE.BufferAttribute(arr, n));
    }
    geo.setIndex(mesh.geometry.index);
    geo.applyMatrix4(mesh.matrixWorld);
    geo.computeBoundingBox();
    const bb = geo.boundingBox;
    // Base of the model at y = 0, centred in x/z.
    geo.translate(-(bb.min.x + bb.max.x) / 2, -bb.min.y, -(bb.min.z + bb.max.z) / 2);
    geo.computeBoundingBox();
    const size = new THREE.Vector3();
    geo.boundingBox.getSize(size);
    const mat = mesh.material;
    mat.envMapIntensity = 1.0;
    // Bleached dead wood reads as white poles at night; weather it down.
    if (f === 'dead_quiver_trunk') mat.color.multiplyScalar(0.5);
    patchMaterial(mat, 'prop-' + f);
    loaded[f] = { geo, mat, size, maxDim: Math.max(size.x, size.y, size.z) };
  }));

  const rand = mulberry32(2026);
  const placements = Object.fromEntries(Object.keys(TYPES).map((k) => [k, []]));
  const colliders = [];
  const density = quality.props;

  const pointOnPath = (s) => {
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
  };

  const inCanyon = (x, z) => z < RIM_SOUTH_Z + 1 && z > RIM_NORTH_Z - 1;
  const onPlatform = (x, z) => Math.hypot(x - PLATFORM.x, z - PLATFORM.z) < 17;

  function place(type, x, z, opts = {}) {
    const T = TYPES[type];
    if (inCanyon(x, z) && !opts.allowCanyon) return false;
    if (onPlatform(x, z)) return false;
    const { d } = pathInfo(x, z);
    const minD = opts.minD ?? 4.2;
    if (d < minD) return false;
    const h = field.sample(x, z);
    if (h < (opts.minH ?? -0.2)) return false;
    // Stay on ground that can hold it: not too steep, and never hanging over a drop.
    const n = field.normal(x, z);
    const slopeDeg = Math.acos(n[1]) * 57.3;
    if (slopeDeg > (T.maxSlope ?? 38)) return false;
    const foot = (T.size[1] + T.size[0]) * 0.22;
    let low = h;
    for (let a = 0; a < 6; a++) low = Math.min(low, field.sample(x + Math.cos(a) * foot, z + Math.sin(a) * foot));
    const embed = (T.maxSlope ?? 38) >= 60;   // big cliffs sink into slopes instead
    if (!embed && h - low > foot * 0.9) return false;
    const size = T.size[0] + (T.size[1] - T.size[0]) * Math.pow(rand(), opts.bias ?? 1.6);
    placements[type].push({ x, z, h: embed ? low : h, size, rotY: rand() * Math.PI * 2, tilt: T.upright ? 0.06 : 0.35, seed: rand() });
    if (size > 1.4 && d < 30) colliders.push({ x, z, r: size * (type === 'tree' ? 0.12 : 0.36) });
    return true;
  }

  // Beside the route: rocks and dead trees that crowd the dark.
  const scatterAlong = (type, s0, s1, count, dMin, dMax, opts) => {
    const n = Math.round(count * density);
    let tries = 0, made = 0;
    while (made < n && tries < n * 12) {
      tries++;
      const s = s0 + rand() * (s1 - s0);
      const p = pointOnPath(s);
      const side = rand() < 0.5 ? -1 : 1;
      const dist = dMin + rand() * (dMax - dMin);
      const x = p.x - p.tz * side * dist + (rand() - 0.5) * 3;
      const z = p.z + p.tx * side * dist + (rand() - 0.5) * 3;
      if (place(type, x, z, { minD: dMin * 0.9, ...opts })) made++;
    }
  };

  scatterAlong('pebble1', 0, S_END, 70, 3.5, 16);
  scatterAlong('pebble3', 0, S_END, 60, 3.5, 18);
  scatterAlong('pebble5', 0, S_END, 60, 4.5, 20);
  scatterAlong('boulder2', 18, S_RIM_SOUTH - 6, 16, 6.5, 18);
  scatterAlong('boulder4', 12, S_RIM_SOUTH - 4, 18, 5.5, 16);
  scatterAlong('boulder4', S_RIM_NORTH + 4, S_PLATFORM - 16, 10, 7, 30);
  scatterAlong('boulder2', S_PLATFORM + 18, S_END - 12, 12, 6, 17);
  scatterAlong('tree', 22, S_RIM_SOUTH - 10, 22, 5.2, 11, { bias: 1.0 });
  scatterAlong('tree', S_RIM_NORTH + 6, S_PLATFORM - 18, 8, 6, 26, { bias: 1.0 });
  scatterAlong('tree', S_PLATFORM + 20, S_END - 20, 8, 5.5, 12, { bias: 1.0 });
  scatterAlong('cliff', 30, S_RIM_SOUTH - 14, 16, 14, 28);
  scatterAlong('cliff', S_PLATFORM + 24, S_END - 26, 10, 13, 26);

  // Boulders set back from both canyon rims (kept clear of the bridge line).
  for (const rimZ of [RIM_SOUTH_Z, RIM_NORTH_Z]) {
    const inward = rimZ === RIM_SOUTH_Z ? 1 : -1;
    for (let x = -20; x < 120; x += 7 + rand() * 9) {
      if (Math.abs(x - BRIDGE_X) < 10) continue;
      if (rand() > density + 0.1) continue;
      const type = rand() < 0.5 ? 'boulder2' : 'boulder4';
      place(type, x, rimZ + inward * (7 + rand() * 12), { minD: 7, minH: 12, bias: 1.2 });
    }
  }
  // Shore stones at the start and the end: the river's edge.
  for (const [cx, cz, n] of [[PATH[0][0] - 6, PATH[0][1] - 4, 40], [PATH[16][0] - 4, PATH[16][1] - 2, 36]]) {
    for (let i = 0; i < n * density; i++) {
      const a = rand() * Math.PI * 2, r = 4 + rand() * 30;
      const type = ['pebble1', 'pebble3', 'pebble5'][Math.floor(rand() * 3)];
      place(type, cx + Math.cos(a) * r, cz + Math.sin(a) * r, { minD: 2.8, minH: -0.6, bias: 2.4 });
    }
  }
  // The rock the torchbearer sits on at the start.
  placements.pebble5.push({ x: PATH[0][0] + 0.15, z: PATH[0][1] + 0.35, h: field.sample(PATH[0][0], PATH[0][1]), size: 1.25, rotY: 0.8, tilt: 0, seed: 0.5, fixed: true });
  placements.pebble5.push({ x: PATH[16][0] - 0.1, z: PATH[16][1] + 0.3, h: field.sample(PATH[16][0], PATH[16][1]), size: 1.25, rotY: 2.1, tilt: 0, seed: 0.3, fixed: true });

  // Build chunked instanced meshes so culling (and the torch shadow) only touch nearby rocks.
  const group = new THREE.Group();
  group.name = 'props';
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), s3 = new THREE.Vector3(), p3 = new THREE.Vector3();
  const up = new THREE.Vector3(0, 1, 0), nrm = new THREE.Vector3(), qTilt = new THREE.Quaternion();
  for (const [type, list] of Object.entries(placements)) {
    const T = TYPES[type];
    const L = loaded[T.file];
    const cells = new Map();
    for (const p of list) {
      const key = Math.floor(p.x / CELL) + ',' + Math.floor(p.z / CELL);
      if (!cells.has(key)) cells.set(key, []);
      cells.get(key).push(p);
    }
    for (const items of cells.values()) {
      const im = new THREE.InstancedMesh(L.geo, L.mat, items.length);
      items.forEach((p, i) => {
        const k = p.size / L.maxDim;
        const n = field.normal(p.x, p.z);
        nrm.set(n[0], n[1], n[2]);
        qTilt.setFromUnitVectors(up, nrm);
        qTilt.slerp(new THREE.Quaternion(), 1 - p.tilt);
        e.set((p.seed - 0.5) * p.tilt * 0.6, p.rotY, (p.seed * 7 % 1 - 0.5) * p.tilt * 0.6);
        q.setFromEuler(e).premultiply(qTilt);
        const sink = p.fixed ? 0.25 : T.sink;
        p3.set(p.x, p.h - L.size.y * k * sink, p.z);
        s3.set(k, k * (0.85 + p.seed * 0.3), k);
        m4.compose(p3, q, s3);
        im.setMatrixAt(i, m4);
      });
      im.instanceMatrix.needsUpdate = true;
      im.computeBoundingSphere();
      im.castShadow = true;
      im.receiveShadow = true;
      group.add(im);
    }
  }
  return { group, colliders, placements, loaded };
}
