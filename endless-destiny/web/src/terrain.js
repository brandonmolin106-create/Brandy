// Terrain mesh: tiled for culling, textured with scanned ground and rock
// (Poly Haven, CC0) blended by slope and height.
import * as THREE from 'three';
import { buildField } from './terrainfield.js';
import { patchMaterial } from './shaders.js';

const TILE = 64; // quads per tile side

export function createTerrain(textures, quality) {
  const res = 1.0 / quality.terrain; // metres per sample
  const field = buildField(res);
  const { h, nx, nz, dx, dz, x0, z0 } = field;

  // Normals from the full grid so tile seams match.
  const normals = new Float32Array(nx * nz * 3);
  for (let j = 0; j < nz; j++) {
    for (let i = 0; i < nx; i++) {
      const hl = h[j * nx + Math.max(i - 1, 0)];
      const hr = h[j * nx + Math.min(i + 1, nx - 1)];
      const hd = h[Math.max(j - 1, 0) * nx + i];
      const hu = h[Math.min(j + 1, nz - 1) * nx + i];
      const ax = (hl - hr) / (2 * dx), az = (hd - hu) / (2 * dz);
      const len = Math.hypot(ax, 1, az);
      const k = (j * nx + i) * 3;
      normals[k] = ax / len; normals[k + 1] = 1 / len; normals[k + 2] = az / len;
    }
  }

  const material = makeTerrainMaterial(textures);
  const group = new THREE.Group();
  group.name = 'terrain';
  for (let tj = 0; tj < nz - 1; tj += TILE) {
    for (let ti = 0; ti < nx - 1; ti += TILE) {
      const w = Math.min(TILE, nx - 1 - ti), d = Math.min(TILE, nz - 1 - tj);
      const vcount = (w + 1) * (d + 1);
      const pos = new Float32Array(vcount * 3);
      const nor = new Float32Array(vcount * 3);
      let v = 0;
      for (let j = 0; j <= d; j++) {
        for (let i = 0; i <= w; i++) {
          const gi = ti + i, gj = tj + j, g = gj * nx + gi;
          pos[v * 3] = x0 + gi * dx;
          pos[v * 3 + 1] = h[g];
          pos[v * 3 + 2] = z0 + gj * dz;
          nor[v * 3] = normals[g * 3]; nor[v * 3 + 1] = normals[g * 3 + 1]; nor[v * 3 + 2] = normals[g * 3 + 2];
          v++;
        }
      }
      const idx = new Uint32Array(w * d * 6);
      let k = 0;
      for (let j = 0; j < d; j++) {
        for (let i = 0; i < w; i++) {
          const a = j * (w + 1) + i, b = a + 1, c = a + (w + 1), e = c + 1;
          idx[k++] = a; idx[k++] = c; idx[k++] = b;
          idx[k++] = b; idx[k++] = c; idx[k++] = e;
        }
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
      geo.setIndex(new THREE.BufferAttribute(idx, 1));
      geo.computeBoundingSphere();
      geo.computeBoundingBox();
      const mesh = new THREE.Mesh(geo, material);
      mesh.receiveShadow = true;
      mesh.matrixAutoUpdate = false;
      group.add(mesh);
    }
  }

  // Height texture for the water (shore transparency) and mist (ground fade).
  const half = new Uint16Array(nx * nz);
  for (let i = 0; i < h.length; i++) half[i] = THREE.DataUtils.toHalfFloat(h[i]);
  const heightTex = new THREE.DataTexture(half, nx, nz, THREE.RedFormat, THREE.HalfFloatType);
  heightTex.magFilter = THREE.LinearFilter;
  heightTex.minFilter = THREE.LinearFilter;
  heightTex.needsUpdate = true;
  const heightBounds = new THREE.Vector4(x0, z0, (nx - 1) * dx, (nz - 1) * dz);

  return { group, field, material, heightTex, heightBounds };
}

function makeTerrainMaterial(t) {
  const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, metalness: 0 });
  const uniforms = {
    tGroundD: { value: t.ground_diff }, tGroundN: { value: t.ground_nor }, tGroundA: { value: t.ground_arm },
    tCliffD: { value: t.cliff_diff }, tCliffN: { value: t.cliff_nor }, tCliffA: { value: t.cliff_arm },
    tShoreD: { value: t.shore_diff }, tShoreN: { value: t.shore_nor }, tShoreA: { value: t.shore_arm },
  };
  return patchMaterial(mat, 'terrain', {
    uniforms,
    vertexPars: 'varying vec3 vTerrN;',
    vertex: 'vTerrN = normalize(mat3(modelMatrix) * objectNormal);',
    fragPars: /* glsl */`
      varying vec3 vTerrN;
      uniform sampler2D tGroundD, tGroundN, tGroundA, tCliffD, tCliffN, tCliffA, tShoreD, tShoreN, tShoreA;
      float tHash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float tNoise(vec2 p) {
        vec2 i = floor(p), f = fract(p);
        f = f * f * (3.0 - 2.0 * f);
        return mix(mix(tHash(i), tHash(i + vec2(1, 0)), f.x), mix(tHash(i + vec2(0, 1)), tHash(i + vec2(1, 1)), f.x), f.y);
      }
      vec3 unpackN(vec4 s) { return s.xyz * 2.0 - 1.0; }
    `,
    frag: (fs) => fs
      .replace('#include <map_fragment>', /* glsl */`
        vec3 wp = vEdWorld;
        vec3 wn = normalize(vTerrN);
        float macro = tNoise(wp.xz * 0.045) * 0.6 + tNoise(wp.xz * 0.013) * 0.4;
        float slope = 1.0 - wn.y;
        float cliffW = smoothstep(0.24, 0.46, slope + (macro - 0.5) * 0.16);
        float shoreW = (1.0 - smoothstep(0.3, 2.4 + macro * 1.5, wp.y)) * (1.0 - cliffW);

        // Ground: two scales to break up tiling.
        vec2 guv = wp.xz * 0.28;
        vec2 guv2 = wp.xz * 0.061 + 0.37;
        vec3 gAlb = mix(texture2D(tGroundD, guv).rgb, texture2D(tGroundD, guv2).rgb, 0.35);
        vec3 gArm = texture2D(tGroundA, guv).rgb;
        vec3 gTn = unpackN(texture2D(tGroundN, guv));
        vec3 gN = normalize(vec3(gTn.xy + wn.xz, abs(gTn.z) * wn.y)).xzy;

        vec3 sAlb = texture2D(tShoreD, wp.xz * 0.22).rgb;
        vec3 sArm = texture2D(tShoreA, wp.xz * 0.22).rgb;
        vec3 sTn = unpackN(texture2D(tShoreN, wp.xz * 0.22));
        vec3 sN = normalize(vec3(sTn.xy + wn.xz, abs(sTn.z) * wn.y)).xzy;

        // Cliffs: triplanar so steep canyon walls do not stretch.
        vec3 bw = pow(abs(wn), vec3(4.0));
        bw /= (bw.x + bw.y + bw.z);
        vec2 uvX = wp.zy * 0.09, uvY = wp.xz * 0.09, uvZ = wp.xy * 0.09;
        vec3 cAlb = texture2D(tCliffD, uvX).rgb * bw.x + texture2D(tCliffD, uvY).rgb * bw.y + texture2D(tCliffD, uvZ).rgb * bw.z;
        vec3 cArm = texture2D(tCliffA, uvX).rgb * bw.x + texture2D(tCliffA, uvY).rgb * bw.y + texture2D(tCliffA, uvZ).rgb * bw.z;
        vec3 tX = unpackN(texture2D(tCliffN, uvX));
        vec3 tY = unpackN(texture2D(tCliffN, uvY));
        vec3 tZ = unpackN(texture2D(tCliffN, uvZ));
        tX = vec3(tX.xy + wn.zy, abs(tX.z) * wn.x);
        tY = vec3(tY.xy + wn.xz, abs(tY.z) * wn.y);
        tZ = vec3(tZ.xy + wn.xy, abs(tZ.z) * wn.z);
        vec3 cN = normalize(tX.zyx * bw.x + tY.xzy * bw.y + tZ.xyz * bw.z);

        vec3 albedo = mix(gAlb, sAlb, shoreW);
        vec3 arm = mix(gArm, sArm, shoreW);
        vec3 terrN = normalize(mix(gN, sN, shoreW));
        albedo = mix(albedo, cAlb * vec3(0.92, 0.9, 0.95), cliffW);
        arm = mix(arm, cArm, cliffW);
        terrN = normalize(mix(terrN, cN, cliffW));
        albedo *= mix(0.72, 1.12, macro);
        // Wet dark sand at the waterline.
        float wet = 1.0 - smoothstep(0.05, 0.7, wp.y);
        albedo *= mix(1.0, 0.45, wet);
        arm.g = mix(arm.g, 0.25, wet);
        diffuseColor.rgb *= albedo;
      `)
      .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = clamp(arm.g, 0.2, 1.0);')
      .replace('#include <metalnessmap_fragment>', 'float metalnessFactor = 0.0;')
      .replace('#include <normal_fragment_maps>', 'normal = normalize((viewMatrix * vec4(terrN, 0.0)).xyz);')
      .replace('#include <aomap_fragment>', /* glsl */`
        float ambientOcclusion = mix(1.0, arm.r, 0.85);
        reflectedLight.indirectDiffuse *= ambientOcclusion;
        reflectedLight.indirectSpecular *= ambientOcclusion;
        reflectedLight.directDiffuse *= mix(1.0, arm.r, 0.4);
      `),
  });
}
