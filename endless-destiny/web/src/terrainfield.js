// The shape of the land: an analytic height function plus a sampled grid.
// Pure JS so it can be previewed outside the browser.
import {
  PATH, PATH_S, PLATEAU, BRIDGE_X, RIM_SOUTH_Z, RIM_NORTH_Z, PLATFORM, COAST,
  S_RIM_SOUTH, S_RIM_NORTH, S_PLATFORM, S_END, START, END,
} from './config.js';
import { makeNoise2D, fbm, ridged, clamp, lerp, smoothstep } from './noise.js';

const nA = makeNoise2D(7);
const nB = makeNoise2D(19);
const nC = makeNoise2D(31);

export const BOUNDS = { x0: -150, z0: -470, x1: 230, z1: 70 };

// Nearest point on the route: distance d and arc length s.
// s is blended across nearby segments so heights never jump at bends.
export function pathInfo(x, z) {
  let best = 1e9, bestI = 0;
  const ds = new Float64Array(PATH.length - 1);
  const ss = new Float64Array(PATH.length - 1);
  for (let i = 0; i < PATH.length - 1; i++) {
    const ax = PATH[i][0], az = PATH[i][1];
    const bx = PATH[i + 1][0], bz = PATH[i + 1][1];
    const vx = bx - ax, vz = bz - az;
    const len2 = vx * vx + vz * vz;
    const t = clamp(((x - ax) * vx + (z - az) * vz) / len2, 0, 1);
    const d = Math.hypot(x - (ax + vx * t), z - (az + vz * t));
    ds[i] = d;
    ss[i] = PATH_S[i] + t * Math.sqrt(len2);
    if (d < best) { best = d; bestI = i; }
  }
  let wsum = 0, s = 0;
  for (let i = 0; i < ds.length; i++) {
    const w = Math.exp(-(ds[i] - best) * 0.35);
    if (w < 1e-4) continue;
    wsum += w;
    s += w * ss[i];
  }
  return { d: best, s: s / wsum, seg: bestI };
}

// Walkable height of the route itself at arc length s.
export function routeHeight(s) {
  if (s <= S_RIM_SOUTH) return lerp(0.5, PLATEAU, smoothstep(14, S_RIM_SOUTH - 14, s));
  if (s <= S_PLATFORM + 12) return PLATEAU;
  return lerp(PLATEAU, 0.5, smoothstep(S_PLATFORM + 12, S_END - 8, s));
}

// How tall the valley walls stand beside the route (0 = open, 1 = deep gorge).
function wallAmount(s) {
  if (s < S_RIM_SOUTH) return smoothstep(10, 44, s) * (1 - 0.65 * smoothstep(S_RIM_SOUTH - 24, S_RIM_SOUTH - 4, s));
  if (s < S_PLATFORM + 10) return 0.18;
  return lerp(0.18, 0.75, smoothstep(S_PLATFORM + 10, S_PLATFORM + 40, s)) * (1 - smoothstep(S_END - 60, S_END - 18, s));
}

// Signed distance to the coastline polygon: + inside land, - over water.
function coastDistance(x, z) {
  let dmin = 1e9;
  let inside = false;
  for (let i = 0, j = COAST.length - 1; i < COAST.length; j = i++) {
    const [xi, zi] = COAST[i];
    const [xj, zj] = COAST[j];
    if ((zi > z) !== (zj > z) && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) inside = !inside;
    const vx = xj - xi, vz = zj - zi;
    const t = clamp(((x - xi) * vx + (z - zi) * vz) / (vx * vx + vz * vz), 0, 1);
    const d = Math.hypot(x - (xi + vx * t), z - (zi + vz * t));
    if (d < dmin) dmin = d;
  }
  return inside ? dmin : -dmin;
}

export function heightAt(x, z) {
  // Wild land: eroded ridges over the plateau.
  const r = ridged(nA, x * 0.011, z * 0.011, 5);
  const f = fbm(nB, x * 0.004 + 3.1, z * 0.004 - 7.7, 4);
  let wild = PLATEAU + 3 + r * 24 + f * 9;
  // Mountains close the world in to the east and south.
  const edge = Math.max(smoothstep(120, 215, x), smoothstep(10, 65, z), smoothstep(-400, -455, z) * smoothstep(20, 80, x));
  wild += edge * (18 + r * 22);

  // Coast: beaches near the start and end, low cliffs elsewhere.
  const lowland = Math.max(
    1 - smoothstep(22, 75, Math.hypot(x - START.x + 6, z - START.z + 4)),
    1 - smoothstep(22, 75, Math.hypot(x - END.x + 4, z - END.z + 4)),
  );
  const coastNoise = fbm(nC, x * 0.02, z * 0.02, 3) * 7 * (1 - 0.75 * lowland);
  const dc = coastDistance(x, z) + coastNoise;
  const shoreH = 0.35 + (fbm(nB, x * 0.05, z * 0.05, 3) * 0.5 + 0.5) * 1.1;
  const beachW = lerp(16, 70, lowland);
  let land = lerp(shoreH, wild, smoothstep(0, beachW, dc));
  if (dc < 0) land = lerp(shoreH, -16, smoothstep(0, 55, -dc));

  // North plateau between the canyon and the platform stays open and misty.
  const plateauMask =
    smoothstep(-226, -236, z) * smoothstep(-320, -300, z) * (1 - smoothstep(55, 90, Math.abs(x - 12)));
  land = lerp(land, PLATEAU + f * 3 + r * 4, plateauMask * smoothstep(2, 24, dc));

  // Carve the route: a walkable floor with walls rising either side.
  const { d, s } = pathInfo(x, z);
  const ph = routeHeight(s);
  const wall = wallAmount(s);
  const floorHalf = 4.5;
  const ramp = lerp(16, 13, wall);
  // Gorge walls are a local feature: far from the route the land takes over again.
  const local = 1 - smoothstep(floorHalf + ramp, floorHalf + ramp + 30, d);
  const away = lerp(land, Math.max(land, ph + 12 + r * 18), local * wall);
  const floorNoise = fbm(nC, x * 0.35, z * 0.35, 2) * 0.12;
  let h = lerp(ph + floorNoise, away, smoothstep(floorHalf, floorHalf + ramp, d));

  // The platform sits on a level shelf.
  const dp = Math.hypot(x - PLATFORM.x, z - PLATFORM.z);
  h = lerp(PLATEAU, h, smoothstep(15, 26, dp));

  // The canyon: an east-west chasm full of fog, open to the river in the west.
  const nearBridge = 1 - smoothstep(3, 18, Math.abs(x - BRIDGE_X));
  const rimS = RIM_SOUTH_Z + fbm(nA, x * 0.03, 11.3, 3) * 9 * (1 - nearBridge);
  const rimN = RIM_NORTH_Z + fbm(nB, x * 0.03, 4.7, 3) * 9 * (1 - nearBridge);
  // Near the bridge the rims stay level a little further out, so the planks start and end on solid ground.
  const landing = (1 - smoothstep(2.5, 6, Math.abs(x - BRIDGE_X))) * 1.8;
  const into = Math.min(rimS - z, z - rimN) - smoothstep(110, 190, x) * 60 - landing;
  if (into > -2) {
    const floor = -30 + fbm(nC, x * 0.02, z * 0.02, 3) * 6;
    h = lerp(h, floor, smoothstep(0.3, 7, into));
  }
  return h;
}

// Sample the height function onto a grid. res = metres per sample.
export function buildField(res = 1.0) {
  const nx = Math.round((BOUNDS.x1 - BOUNDS.x0) / res) + 1;
  const nz = Math.round((BOUNDS.z1 - BOUNDS.z0) / res) + 1;
  const dx = (BOUNDS.x1 - BOUNDS.x0) / (nx - 1);
  const dz = (BOUNDS.z1 - BOUNDS.z0) / (nz - 1);
  const h = new Float32Array(nx * nz);
  for (let j = 0; j < nz; j++) {
    const z = BOUNDS.z0 + j * dz;
    for (let i = 0; i < nx; i++) h[j * nx + i] = heightAt(BOUNDS.x0 + i * dx, z);
  }
  return makeField(h, nx, nz, dx, dz);
}

export function makeField(h, nx, nz, dx, dz) {
  const field = {
    h, nx, nz, dx, dz, ...BOUNDS,
    // Height on the rendered surface (matches the mesh triangles closely).
    sample(x, z) {
      const fx = clamp((x - BOUNDS.x0) / dx, 0, nx - 1.001);
      const fz = clamp((z - BOUNDS.z0) / dz, 0, nz - 1.001);
      const i = Math.floor(fx), j = Math.floor(fz);
      const u = fx - i, v = fz - j;
      const a = h[j * nx + i], b = h[j * nx + i + 1];
      const c = h[(j + 1) * nx + i], d = h[(j + 1) * nx + i + 1];
      // Same diagonal split as the mesh triangles (a,c,b) and (b,c,d).
      if (u + v <= 1) return a + (b - a) * u + (c - a) * v;
      return d + (c - d) * (1 - u) + (b - d) * (1 - v);
    },
    normal(x, z) {
      const e = Math.max(dx, dz);
      const hl = field.sample(x - e, z), hr = field.sample(x + e, z);
      const hd = field.sample(x, z - e), hu = field.sample(x, z + e);
      const nxv = hl - hr, nyv = 2 * e, nzv = hd - hu;
      const len = Math.hypot(nxv, nyv, nzv);
      return [nxv / len, nyv / len, nzv / len];
    },
  };
  return field;
}
