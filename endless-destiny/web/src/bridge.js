// The bridge: each step into nothing gathers gold dust into a thick weathered oak
// plank that glows, then cools to warm timber. A hair-thin golden line across the canyon.
import * as THREE from 'three';
import { patchMaterial } from './shaders.js';
import { BRIDGE_X, RIM_SOUTH_Z, RIM_NORTH_Z, PLATEAU } from './config.js';
import { mulberry32 } from './noise.js';
import { createParticles } from './fx.js';

export const DECK_Y = PLATEAU + 0.02;
const PITCH = 0.74;
const DEPTH = 0.62;
const WIDTH = 2.0;

export function createBridge(textures) {
  // Runs from the south rim across the canyon and a little onto the far rim.
  const count = Math.ceil((RIM_SOUTH_Z - RIM_NORTH_Z + 1.6) / PITCH);
  const geo = new THREE.BoxGeometry(WIDTH, 0.11, DEPTH, 1, 1, 1);
  const born = new Float32Array(count).fill(1e6);
  const seeds = new Float32Array(count);
  const rand = mulberry32(99);
  for (let i = 0; i < count; i++) seeds[i] = rand();
  geo.setAttribute('aBorn', new THREE.InstancedBufferAttribute(born, 1));
  geo.setAttribute('aSeed', new THREE.InstancedBufferAttribute(seeds, 1));

  const mat = patchMaterial(new THREE.MeshStandardMaterial({
    map: textures.planks_diff, normalMap: textures.planks_nor, roughnessMap: textures.planks_arm,
    aoMap: textures.planks_arm, color: 0xb59a7c, roughness: 1, metalness: 0,
  }), 'plank', {
    vertexPars: 'attribute float aBorn; attribute float aSeed; varying float vBorn; varying float vSeed; varying vec2 vPUv;',
    beginVertex: /* glsl */`
      float grow = smoothstep(aBorn, aBorn + 0.28, uTime);
      transformed *= mix(0.2, 1.0, grow);
      transformed.y -= (1.0 - grow) * 0.6;
      vBorn = aBorn;
      vSeed = aSeed;
      vPUv = uv;
    `,
    fragPars: 'varying float vBorn; varying float vSeed; varying vec2 vPUv;',
    frag: (fs) => fs
      .replace('#include <map_fragment>', /* glsl */`
        vec2 puv = vec2(vPUv.x, vPUv.y * 0.22 + floor(vSeed * 4.0) * 0.23);
        vec4 texel = texture2D(map, puv);
        diffuseColor *= texel;
      `)
      .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = texture2D(roughnessMap, vec2(vPUv.x, vPUv.y * 0.22 + floor(vSeed * 4.0) * 0.23)).g;')
      .replace('#include <emissivemap_fragment>', /* glsl */`
        float age = uTime - vBorn;
        float hot = exp(-max(age, 0.0) * 0.85) * step(0.0, age);
        vec2 e = min(vPUv, 1.0 - vPUv);
        float rim = 1.0 - smoothstep(0.0, 0.08, min(e.x, e.y));
        totalEmissiveRadiance += vec3(1.0, 0.62, 0.22) * (hot * 3.2 + rim * 0.22 * step(0.0, age));
      `),
  });
  // The map/normal maps above need UVs; the per-instance born time drives the glow.
  const mesh = new THREE.InstancedMesh(geo, mat, count);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.frustumCulled = false;
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), p = new THREE.Vector3(), s = new THREE.Vector3();
  for (let i = 0; i < count; i++) {
    const z = RIM_SOUTH_Z + 0.2 - DEPTH / 2 - i * PITCH;
    e.set((seeds[i] - 0.5) * 0.02, (seeds[i] - 0.5) * 0.05, ((seeds[i] * 13) % 1 - 0.5) * 0.02);
    q.setFromEuler(e);
    p.set(BRIDGE_X + (seeds[i] - 0.5) * 0.12, DECK_Y - 0.055 + (seeds[i] - 0.5) * 0.02, z);
    s.set(1 + (seeds[i] - 0.5) * 0.1, 1, 1);
    m4.compose(p, q, s);
    mesh.setMatrixAt(i, m4);
  }
  mesh.instanceMatrix.needsUpdate = true;
  mesh.count = 0; // grows as planks are born

  const dust = createParticles({ count: 500, color: 0xffc46a, size: 0.05 });
  dust.points.material.uniforms.uBright.value = 4;

  const bridge = {
    mesh, dust, count, born: 0,
    startZ: RIM_SOUTH_Z + 0.2,
    endZ: RIM_NORTH_Z,
    onPlank: null,
    // Planks exist from the rim up to (and including) this z.
    frontierZ() { return bridge.born === 0 ? RIM_SOUTH_Z + 0.2 : RIM_SOUTH_Z + 0.2 - bridge.born * PITCH; },
    bornUpTo(z, t) {
      const want = Math.min(count, Math.ceil((RIM_SOUTH_Z + 0.2 - z) / PITCH));
      while (bridge.born < want) {
        const i = bridge.born++;
        born[i] = t + (i === 0 ? 0 : 0.02);
        const pz = RIM_SOUTH_Z + 0.2 - DEPTH / 2 - i * PITCH;
        for (let k = 0; k < 14; k++) {
          const a = Math.random() * Math.PI * 2, r = 0.6 + Math.random() * 0.9;
          dust.emit(BRIDGE_X + Math.cos(a) * r, DECK_Y - 0.4 - Math.random() * 0.8, pz + Math.sin(a) * r * 0.5,
            -Math.cos(a) * 1.4, 1.2 + Math.random(), -Math.sin(a) * 0.7, 0.9 + Math.random() * 0.6);
        }
        bridge.onPlank?.(i);
      }
      geo.attributes.aBorn.needsUpdate = true;
      mesh.count = bridge.born;
    },
    completeInstantly(t) {
      bridge.bornUpTo(RIM_NORTH_Z - 1.4, t - 30);
    },
    reset() {
      born.fill(1e6);
      bridge.born = 0;
      mesh.count = 0;
      geo.attributes.aBorn.needsUpdate = true;
      dust.clear();
    },
    update(dt, t) {
      dust.update(dt, { drag: 1.6, lift: -0.4, time: t });
    },
  };
  return bridge;
}
