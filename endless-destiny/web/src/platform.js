// The circular stone platform with seven worn steps, and on it the four-metre bronze
// cauldron shaped like the studio's leaf — its veins are the channels the fire climbs.
import * as THREE from 'three';
import { patchMaterial, U } from './shaders.js';
import { PLATFORM, PLATEAU } from './config.js';
import { drawEmblem, starPath } from './emblem.js';
import { createFlame, createGlow, createParticles } from './fx.js';

const LEAF_H = 4.0;
const S = LEAF_H / 340;           // emblem units -> metres

// Half-width of the emblem outline at SVG height y (tip at -170, base at +170).
function outlineHalfWidth(y) {
  const ay = Math.abs(y);
  if (ay >= 50) {
    const t = (170 - ay) / 120;
    const top = y < 0;
    return (top ? 5 : 4) + (126 - (top ? 5 : 4)) * Math.pow(t, 0.92);
  }
  return 126 + 21 * Math.cos((ay / 50) * Math.PI / 2);
}

function emblemCanvas(size = 1024) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const g = c.getContext('2d');
  g.fillStyle = '#000';
  g.fillRect(0, 0, size, size);
  drawEmblem(g, size, { color: '#fff', stroke: 10, star: false });
  return c;
}

function buildLeafGeometry(mask, maskSize) {
  const NA = 110, NB = 150;
  const pos = [], uv = [], idx = [];
  const sampleMask = (u, v) => {
    const x = Math.min(maskSize - 1, Math.max(0, Math.round(u * (maskSize - 1))));
    const y = Math.min(maskSize - 1, Math.max(0, Math.round((1 - v) * (maskSize - 1))));
    return mask[(y * maskSize + x) * 4] / 255;
  };
  for (const side of [1, -1]) {
    const base = pos.length / 3;
    for (let j = 0; j <= NB; j++) {
      const b = j / NB;
      const ySvg = 170 - b * 340;
      const W = outlineHalfWidth(ySvg);
      for (let i = 0; i <= NA; i++) {
        const a = (i / NA) * 2 - 1;
        const xSvg = a * W;
        const u = (xSvg + 190) / 380;
        const v = 1 - (ySvg + 190) / 380;
        const lens = Math.sqrt(Math.max(0, 1 - a * a));
        const relief = sampleMask(u, v) * lens;
        const T = 0.24 * W * S * lens + relief * 0.035;
        pos.push(xSvg * S, b * LEAF_H, side * T);
        uv.push(u, v);
      }
    }
    for (let j = 0; j < NB; j++) {
      for (let i = 0; i < NA; i++) {
        const a = base + j * (NA + 1) + i, bb = a + 1, c = a + (NA + 1), d = c + 1;
        if (side > 0) idx.push(a, bb, c, bb, d, c);
        else idx.push(a, c, bb, bb, c, d);
      }
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  return geo;
}

export function stoneMaterial(t, key) {
  return patchMaterial(new THREE.MeshStandardMaterial({ color: 0x8d8a92, roughness: 1, metalness: 0 }), key, {
    uniforms: { tSD: { value: t.stone_diff }, tSN: { value: t.stone_nor }, tSA: { value: t.stone_arm } },
    vertexPars: 'varying vec3 vStN;',
    vertex: 'vStN = normalize(mat3(modelMatrix) * objectNormal);',
    fragPars: 'varying vec3 vStN; uniform sampler2D tSD, tSN, tSA; vec3 stUnpack(vec4 s){return s.xyz*2.0-1.0;}',
    frag: (fs) => fs
      .replace('#include <map_fragment>', /* glsl */`
        vec3 swp = vEdWorld; vec3 swn = normalize(vStN);
        vec3 sbw = pow(abs(swn), vec3(4.0)); sbw /= (sbw.x + sbw.y + sbw.z);
        vec2 sX = swp.zy * 0.45, sY = swp.xz * 0.45, sZ = swp.xy * 0.45;
        vec3 stAlb = texture2D(tSD, sX).rgb * sbw.x + texture2D(tSD, sY).rgb * sbw.y + texture2D(tSD, sZ).rgb * sbw.z;
        vec3 stArm = texture2D(tSA, sX).rgb * sbw.x + texture2D(tSA, sY).rgb * sbw.y + texture2D(tSA, sZ).rgb * sbw.z;
        vec3 nX = stUnpack(texture2D(tSN, sX)), nY = stUnpack(texture2D(tSN, sY)), nZ = stUnpack(texture2D(tSN, sZ));
        nX = vec3(nX.xy + swn.zy, abs(nX.z) * swn.x);
        nY = vec3(nY.xy + swn.xz, abs(nY.z) * swn.y);
        nZ = vec3(nZ.xy + swn.xy, abs(nZ.z) * swn.z);
        vec3 stN = normalize(nX.zyx * sbw.x + nY.xzy * sbw.y + nZ.xyz * sbw.z);
        diffuseColor.rgb *= stAlb;
      `)
      .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = clamp(stArm.g, 0.3, 1.0);')
      .replace('#include <metalnessmap_fragment>', 'float metalnessFactor = 0.0;')
      .replace('#include <normal_fragment_maps>', 'normal = normalize((viewMatrix * vec4(stN, 0.0)).xyz);')
      .replace('#include <aomap_fragment>', 'reflectedLight.indirectDiffuse *= stArm.r; reflectedLight.directDiffuse *= mix(1.0, stArm.r, 0.5);'),
  });
}

export function createPlatform(textures) {
  const group = new THREE.Group();
  group.name = 'platform';
  group.position.set(PLATFORM.x, PLATEAU, PLATFORM.z);

  // Seven worn steps.
  const stone = stoneMaterial(textures, 'stone');
  const stoneMat = stone;
  for (let i = 0; i < PLATFORM.steps; i++) {
    const r = PLATFORM.radius - i * PLATFORM.tread;
    const h = PLATFORM.rise * (i + 1) + 0.4;
    const geo = new THREE.CylinderGeometry(r, r + 0.04, h, 96, 1);
    // Worn edges: nudge the rim vertices a little.
    const p = geo.attributes.position;
    for (let k = 0; k < p.count; k++) {
      const x = p.getX(k), z = p.getZ(k), y = p.getY(k);
      const a = Math.atan2(z, x);
      const wob = Math.sin(a * 7 + i) * 0.03 + Math.sin(a * 19 + i * 3) * 0.015;
      const s = 1 + wob / r;
      p.setXYZ(k, x * s, y - (y > 0 ? Math.abs(Math.sin(a * 5 + i * 2)) * 0.03 : 0), z * s);
    }
    geo.computeVertexNormals();
    const m = new THREE.Mesh(geo, stone);
    m.position.y = h / 2 - 0.4;
    m.receiveShadow = true;
    m.castShadow = true;
    group.add(m);
  }
  const topY = PLATFORM.rise * PLATFORM.steps;

  // The leaf, engraved faintly into the top of the platform.
  const canvas = emblemCanvas(1024);
  const maskData = canvas.getContext('2d').getImageData(0, 0, 1024, 1024).data;
  const emblemTex = new THREE.CanvasTexture(canvas);
  emblemTex.anisotropy = 4;
  const floorMat = new THREE.MeshBasicMaterial({
    map: emblemTex, color: 0x000000, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false,
  });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(7.6, 7.6), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = topY + 0.012;
  floor.renderOrder = 2;
  group.add(floor);

  // The cauldron itself.
  const leafGeo = buildLeafGeometry(maskData, 1024);
  const cauldronUniforms = { uFill: { value: 0 }, uLeafMask: { value: emblemTex }, uHeat: { value: 0 } };
  const bronze = patchMaterial(new THREE.MeshStandardMaterial({
    color: 0x8a6636, metalness: 0.9, roughness: 0.38,
  }), 'cauldron', {
    uniforms: cauldronUniforms,
    vertexPars: 'varying vec2 vLeafUv; varying float vLeafH;',
    vertex: `vLeafUv = uv; vLeafH = position.y / ${LEAF_H.toFixed(2)};`,
    fragPars: 'uniform sampler2D uLeafMask; uniform float uFill, uHeat; varying vec2 vLeafUv; varying float vLeafH; float lh(vec2 p){return fract(sin(dot(p, vec2(12.9898,78.233)))*43758.5453);}',
    frag: (fs) => fs
      .replace('#include <map_fragment>', /* glsl */`
        float vein = texture2D(uLeafMask, vLeafUv).r;
        // Green-brown patina settles in the recesses; the raised veins stay polished.
        vec3 patina = vec3(0.16, 0.2, 0.14);
        diffuseColor.rgb = mix(patina, diffuseColor.rgb, 0.35 + vein * 0.65);
        float grain = lh(floor(vLeafUv * 400.0));
        diffuseColor.rgb *= 0.85 + grain * 0.2;
      `)
      .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = mix(0.75, 0.3, vein);')
      .replace('#include <emissivemap_fragment>', /* glsl */`
        float wave = vLeafH + (lh(floor(vLeafUv * 60.0)) - 0.5) * 0.03;
        float filled = smoothstep(wave - 0.02, wave + 0.02, uFill);
        float fq = (uFill - vLeafH) * 14.0;
        float front = exp(-fq * fq) * step(0.01, uFill) * step(uFill, 1.02);
        float flick = 0.85 + 0.15 * sin(uTime * 9.0 + vLeafUv.y * 40.0);
        totalEmissiveRadiance += vec3(1.0, 0.6, 0.2) * vein * (filled * 1.25 * flick + front * 2.6);
        totalEmissiveRadiance += vec3(1.0, 0.45, 0.12) * uHeat * 0.1;
      `),
  });
  const leaf = new THREE.Mesh(leafGeo, bronze);
  leaf.position.y = topY + 0.42;
  leaf.castShadow = true;
  leaf.receiveShadow = true;
  // Face the leaf toward the bridge so the approaching torchbearer meets it head on.
  leaf.rotation.y = 0;
  group.add(leaf);

  const plinth = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.78, 0.44, 48), stone);
  plinth.position.y = topY + 0.2;
  plinth.castShadow = true;
  group.add(plinth);

  // The golden four-pointed star in the open point of the leaf.
  const starShape = new THREE.Shape();
  const sp = starPath(0, 0, 13, 3.2).replace('M ', '').replace(' Z', '').split(' L ').map((pt) => pt.split(' ').map(Number));
  sp.forEach(([x, y], i) => (i ? starShape.lineTo(x * S, -y * S) : starShape.moveTo(x * S, -y * S)));
  const starGeo = new THREE.ExtrudeGeometry(starShape, { depth: 0.03, bevelEnabled: true, bevelSize: 0.008, bevelThickness: 0.01, bevelSegments: 2 });
  starGeo.translate(0, 0, -0.015);
  const starMat = new THREE.MeshStandardMaterial({ color: 0xc89b4a, metalness: 1, roughness: 0.25, emissive: 0xffc060, emissiveIntensity: 0.2 });
  const star = new THREE.Mesh(starGeo, starMat);
  star.position.set(0, topY + 0.42 + (170 + 126) * S, 0);
  star.scale.setScalar(2.2);
  group.add(star);
  const starGlow = createGlow(0xffc060, 1.4, 0);
  starGlow.position.copy(star.position);
  group.add(starGlow);

  // The column of flame and the embers that climb like snow falling upward.
  const column = new THREE.Group();
  column.position.set(0, topY + 0.42 + LEAF_H - 0.1, 0);
  group.add(column);
  const flames = [
    createFlame({ intensity: 1.7, turbulence: 0.5, seed: 0.1 }),
    createFlame({ intensity: 1.25, turbulence: 0.7, seed: 0.5 }),
    createFlame({ intensity: 0.9, turbulence: 0.9, seed: 0.9 }),
  ];
  flames.forEach((f) => { f.visible = false; column.add(f); });
  const colGlow = createGlow(0xffa040, 20, 0);
  colGlow.position.y = 8;
  column.add(colGlow);
  const fireLight = new THREE.PointLight(0xffa14a, 0, 260, 1.6);
  fireLight.position.y = 3;
  column.add(fireLight);
  const embers = createParticles({ count: 1400, color: 0xffb455, size: 0.09 });
  embers.points.material.uniforms.uBright.value = 3.5;

  const worldCol = new THREE.Vector3();
  const api = {
    group, leaf, star, starMat, starGlow, stoneMat, floorMat, flames, fireLight, column, embers, cauldronUniforms,
    topY: PLATEAU + topY,
    lit: 0,          // 0..1 how far the fire has climbed
    blaze: 0,        // 0..1 column strength
    stepHeight(r) {
      // Height of the platform surface at distance r from its centre (relative to PLATEAU).
      for (let i = PLATFORM.steps - 1; i >= 0; i--) {
        if (r <= PLATFORM.radius - i * PLATFORM.tread) return PLATFORM.rise * (i + 1);
      }
      return 0;
    },
    update(dt, t) {
      cauldronUniforms.uFill.value = api.lit;
      cauldronUniforms.uHeat.value = api.blaze;
      const b = api.blaze;
      flames.forEach((f, i) => {
        f.visible = b > 0.01;
        f.material.uniforms.uTime.value = t * (1 - i * 0.12);
        f.material.uniforms.uLife.value = b;
        const w = [6, 8.5, 11][i], h = [22, 16, 11][i];
        f.scale.set(w * (0.7 + 0.3 * b), h * b, 1);
      });
      colGlow.material.opacity = 0.16 * b;
      fireLight.intensity = b * 1500 * (1 + Math.sin(t * 5.1) * 0.04);
      starMat.emissiveIntensity = 0.2 + api.lit * 0.6 + b * 6;
      starGlow.material.opacity = Math.min(1, api.lit * 0.3 + b * 0.9);
      floorMat.color.setRGB(0.9 * b, 0.55 * b, 0.2 * b);
      column.getWorldPosition(worldCol);
      if (b > 0.05) {
        for (let k = 0; k < 6; k++) {
          if (Math.random() > b) continue;
          const a = Math.random() * Math.PI * 2, r = Math.random() * 30;
          embers.emit(worldCol.x + Math.cos(a) * r, worldCol.y - 4 + Math.random() * 3, worldCol.z + Math.sin(a) * r,
            (Math.random() - 0.5) * 0.3, 0.6 + Math.random() * 1.2, (Math.random() - 0.5) * 0.3, 6 + Math.random() * 6);
        }
        for (let k = 0; k < 3; k++) {
          embers.emit(worldCol.x + (Math.random() - 0.5), worldCol.y + Math.random() * 3, worldCol.z + (Math.random() - 0.5),
            (Math.random() - 0.5) * 1.5, 3 + Math.random() * 4, (Math.random() - 0.5) * 1.5, 4 + Math.random() * 3);
        }
      }
      embers.update(dt, { drag: 0.15, lift: 0.08, swirl: 0.25, time: t });
      U.uFireCol.value.set(1.0, 0.58, 0.2).multiplyScalar(b * 22);
      U.uFirePos.value.set(worldCol.x, worldCol.y + 6, worldCol.z);
    },
  };
  return api;
}
