// Mist: a knee-high ribbon over the river and layered fog boiling in the canyon.
import * as THREE from 'three';
import { U, ED_COMMON } from './shaders.js';
import { RIM_SOUTH_Z, RIM_NORTH_Z } from './config.js';

function mistMaterial(heightTex, heightBounds, { opacity = 0.5, scale = 0.03, speed = [0.6, 0.1], tint = [1, 1, 1] } = {}) {
  return new THREE.ShaderMaterial({
    uniforms: {
      ...U,
      uHeightTex: { value: heightTex },
      uHeightBounds: { value: heightBounds },
      uOpacity: { value: opacity },
      uScale: { value: scale },
      uSpeed: { value: new THREE.Vector2(...speed) },
      uTint: { value: new THREE.Vector3(...tint) },
    },
    vertexShader: /* glsl */`
      varying vec3 vWorld;
      varying vec2 vUv;
      void main() {
        vUv = uv;
        vec4 w = modelMatrix * vec4(position, 1.0);
        vWorld = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w;
      }`,
    fragmentShader: /* glsl */`
      ${ED_COMMON}
      uniform sampler2D uHeightTex;
      uniform vec4 uHeightBounds;
      uniform float uOpacity, uScale;
      uniform vec2 uSpeed;
      uniform vec3 uTint;
      varying vec3 vWorld;
      varying vec2 vUv;
      float mh(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float mn(vec2 p) {
        vec2 i = floor(p), f = fract(p);
        f = f * f * (3.0 - 2.0 * f);
        return mix(mix(mh(i), mh(i + vec2(1, 0)), f.x), mix(mh(i + vec2(0, 1)), mh(i + vec2(1, 1)), f.x), f.y);
      }
      float fbm(vec2 p) {
        float s = 0.0, a = 0.5;
        for (int i = 0; i < 5; i++) { s += a * mn(p); p = p * 2.07 + 13.1; a *= 0.5; }
        return s;
      }
      void main() {
        vec2 p = vWorld.xz * uScale;
        vec2 flow = uSpeed * uTime * uScale;
        float n = fbm(p + flow + fbm(p * 0.7 - flow * 0.5) * 1.3);
        float d = smoothstep(0.38, 0.85, n);
        // Fade where the sheet meets the ground and toward the edges of the sheet.
        vec2 huv = (vWorld.xz - uHeightBounds.xy) / uHeightBounds.zw;
        float ground = texture2D(uHeightTex, clamp(huv, 0.0, 1.0)).r;
        float above = smoothstep(0.0, 2.5, vWorld.y - ground);
        vec2 e = min(vUv, 1.0 - vUv);
        float edge = smoothstep(0.0, 0.18, min(e.x, e.y));
        // Soften when the camera is inside the sheet.
        vec3 toCam = vWorld - cameraPosition;
        float camNear = smoothstep(1.0, 12.0, length(toCam));
        // Seen edge-on a flat sheet turns into a hard streak: fade it out at grazing angles.
        float facing = smoothstep(0.03, 0.22, abs(toCam.y) / max(length(toCam), 1e-3));
        float a = d * above * edge * camNear * facing * uOpacity;
        vec3 lit = edFogColor() * 2.2 * uTint;
        float dt = length(vWorld - uTorchPos);
        lit += uTorchCol * 0.12 / (1.0 + dt * dt * 0.08);
        float df = length(vWorld - uFirePos);
        lit += uFireCol * 0.3 / (1.0 + df * df * 0.0015);
        vec3 col = edFog(lit, vWorld);
        gl_FragColor = vec4(col, a);
      }`,
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
}

export function createMist(heightTex, heightBounds) {
  const group = new THREE.Group();
  group.name = 'mist';
  const sheet = (w, d, x, y, z, opts) => {
    const geo = new THREE.PlaneGeometry(w, d, 1, 1);
    geo.rotateX(-Math.PI / 2);
    const m = new THREE.Mesh(geo, mistMaterial(heightTex, heightBounds, opts));
    m.position.set(x, y, z);
    m.renderOrder = 3;
    group.add(m);
    return m;
  };
  // River ribbons near the start and the end.
  sheet(240, 160, -60, 0.45, -20, { opacity: 0.55, scale: 0.045, speed: [1.2, -0.2] });
  sheet(240, 160, -60, 0.95, -30, { opacity: 0.35, scale: 0.03, speed: [0.9, -0.1] });
  sheet(240, 180, -60, 0.5, -400, { opacity: 0.55, scale: 0.045, speed: [1.2, -0.2] });
  sheet(240, 180, -60, 1.0, -410, { opacity: 0.35, scale: 0.03, speed: [0.9, -0.1] });
  // The canyon: layer upon layer of slow fog far below the bridge.
  const cz = (RIM_SOUTH_Z + RIM_NORTH_Z) / 2;
  const cw = RIM_SOUTH_Z - RIM_NORTH_Z + 30;
  [[2, 0.8], [6, 0.7], [10, 0.6], [14.5, 0.5], [18.5, 0.36]].forEach(([y, o], i) => {
    sheet(420, cw, 40, y, cz, { opacity: o, scale: 0.02 + i * 0.004, speed: [0.5 + i * 0.25, 0.15 * (i % 2 ? 1 : -1)], tint: [0.95, 0.95, 1.1] });
  });
  return group;
}
