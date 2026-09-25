// The river: flat and dark as polished obsidian, carrying the stars and the golden star.
import * as THREE from 'three';
import { U, ED_COMMON, ED_SKY } from './shaders.js';
import { WATER_Y } from './config.js';

export function createWater(heightTex, heightBounds) {
  const uniforms = {
    ...U,
    uHeightTex: { value: heightTex },
    uHeightBounds: { value: heightBounds },
    uRippleCenter: { value: new THREE.Vector3(0, 0, 0) },
    uRippleTime: { value: -100 },
  };
  const mat = new THREE.ShaderMaterial({
    uniforms,
    transparent: true,
    depthWrite: true,
    vertexShader: /* glsl */`
      varying vec3 vWorld;
      void main() {
        vec4 w = modelMatrix * vec4(position, 1.0);
        vWorld = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w;
      }`,
    fragmentShader: /* glsl */`
      ${ED_COMMON}
      ${ED_SKY}
      uniform sampler2D uHeightTex;
      uniform vec4 uHeightBounds;
      uniform vec3 uRippleCenter;
      uniform float uRippleTime;
      varying vec3 vWorld;

      float wHash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      float wNoise(vec2 p) {
        vec2 i = floor(p), f = fract(p);
        vec2 u = f * f * (3.0 - 2.0 * f);
        return mix(mix(wHash(i), wHash(i + vec2(1, 0)), u.x), mix(wHash(i + vec2(0, 1)), wHash(i + vec2(1, 1)), u.x), u.y);
      }
      // Slow current running north along the river, plus fine shivering ripples.
      float wHeight(vec2 p) {
        float t = uTime;
        float h = 0.0;
        h += wNoise(p * 0.35 + vec2(0.0, t * 0.18)) * 0.5;
        h += wNoise(p * 0.9 + vec2(t * 0.05, t * 0.32)) * 0.25;
        h += wNoise(p * 2.3 - vec2(t * 0.21, -t * 0.4)) * 0.12;
        h += wNoise(p * 5.1 + vec2(-t * 0.3, t * 0.6)) * 0.05;
        float dr = length(p - uRippleCenter.xz);
        float rt = uTime - uRippleTime;
        float ring = sin((dr - rt * 1.6) * 7.0) * exp(-abs(dr - rt * 1.6) * 1.2) * exp(-rt * 0.35) * step(0.0, rt);
        return h * 0.05 + ring * 0.03;
      }

      void main() {
        vec2 p = vWorld.xz;
        float e = 0.06;
        float h0 = wHeight(p);
        float hx = wHeight(p + vec2(e, 0.0));
        float hz = wHeight(p + vec2(0.0, e));
        vec3 camToP = vWorld - cameraPosition;
        float dist = length(camToP);
        vec3 V = camToP / dist;
        // Ripples fade with distance so the far river reads as a razor-flat line.
        float detail = 1.0 - smoothstep(60.0, 900.0, dist);
        vec3 N = normalize(vec3(-(hx - h0) / e * detail, 1.0, -(hz - h0) / e * detail));

        vec3 R = reflect(V, N);
        R.y = abs(R.y);
        float cosT = max(dot(-V, N), 0.0);
        float fres = 0.02 + 0.98 * pow(1.0 - cosT, 5.0);
        vec3 refl = edSky(R, 1.0);

        // How deep is it here? Shallow water near the shore lets the sand show through.
        vec2 huv = (p - uHeightBounds.xy) / uHeightBounds.zw;
        float ground = texture2D(uHeightTex, clamp(huv, 0.0, 1.0)).r;
        bool inside = all(greaterThan(huv, vec2(0.0))) && all(lessThan(huv, vec2(1.0)));
        float depth = inside ? max(0.0, ${WATER_Y.toFixed(2)} - ground) : 30.0;

        vec3 deepCol = vec3(0.0015, 0.0022, 0.0055);
        vec3 col = mix(deepCol, refl, fres);

        // The torch and the cauldron fire glint on the water.
        vec3 L1 = uTorchPos - vWorld;
        float d1 = length(L1);
        vec3 H1 = normalize(L1 / d1 - V);
        col += uTorchCol * pow(max(dot(N, H1), 0.0), 260.0) * 6.0 / (1.0 + d1 * d1 * 0.02);
        col += uTorchCol * 0.02 / (1.0 + d1 * d1 * 0.15);
        vec3 L2 = uFirePos - vWorld;
        float d2 = length(L2);
        vec3 H2 = normalize(L2 / d2 - V);
        col += uFireCol * pow(max(dot(N, H2), 0.0), 180.0) * 4.0 / (1.0 + d2 * d2 * 0.0004);

        // Gold-rimmed rings when the flame is gathered.
        float dr = length(p - uRippleCenter.xz);
        float rt = uTime - uRippleTime;
        float cq = (dr - rt * 1.6) * 3.0;
        float crest = exp(-cq * cq) * exp(-rt * 0.5) * step(0.0, rt) * step(rt, 12.0);
        col += vec3(1.0, 0.66, 0.26) * crest * 1.4;

        col = edWorldFx(col, vec3(0.02), vWorld);
        col = edFog(col, vWorld);
        float alpha = smoothstep(0.0, 0.55, depth);
        gl_FragColor = vec4(col, alpha);
      }`,
  });
  const geo = new THREE.PlaneGeometry(5000, 5000, 1, 1);
  geo.rotateX(-Math.PI / 2);
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(0, WATER_Y, -200);
  mesh.name = 'river';
  mesh.renderOrder = 1;
  mesh.frustumCulled = false;
  return mesh;
}
