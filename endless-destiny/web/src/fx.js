// Fire and light: the torch flame, glow sprites, rising embers and golden dust.
import * as THREE from 'three';

// Tall, narrow, golden and almost still.
export function createFlameMaterial({ intensity = 6, turbulence = 0.35, seed = 0 } = {}) {
  return new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uIntensity: { value: intensity },
      uTurb: { value: turbulence },
      uSeed: { value: seed },
      uLife: { value: 1 },
    },
    vertexShader: /* glsl */`
      varying vec2 vUv;
      void main() {
        vUv = uv;
        // Cylindrical billboard: stays upright, turns to face the camera.
        vec3 center = (modelMatrix * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
        vec3 toCam = cameraPosition - center;
        toCam.y = 0.0;
        toCam = normalize(toCam + vec3(1e-5, 0.0, 0.0));
        vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), toCam));
        float sx = length(modelMatrix[0].xyz);
        float sy = length(modelMatrix[1].xyz);
        vec3 wp = center + right * position.x * sx + vec3(0.0, 1.0, 0.0) * position.y * sy;
        gl_Position = projectionMatrix * viewMatrix * vec4(wp, 1.0);
      }`,
    fragmentShader: /* glsl */`
      uniform float uTime, uIntensity, uTurb, uSeed, uLife;
      varying vec2 vUv;
      float h21(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1))) * 45758.5453); }
      float n21(vec2 p) {
        vec2 i = floor(p), f = fract(p);
        f = f * f * (3.0 - 2.0 * f);
        return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y);
      }
      void main() {
        vec2 uv = vUv;
        float t = uTime * 1.3 + uSeed * 17.0;
        float n = n21(vec2(uv.x * 3.0, uv.y * 4.0 - t * 1.6)) * 0.6 + n21(vec2(uv.x * 7.0, uv.y * 9.0 - t * 2.7)) * 0.4;
        float x = (uv.x - 0.5) * 2.0;
        x += (n - 0.5) * uTurb * smoothstep(0.1, 1.0, uv.y);
        float y = uv.y;
        // Teardrop: wide at the base, drawn to a fine tip.
        float width = mix(0.55, 0.02, pow(y, 0.9)) * smoothstep(0.0, 0.14, y);
        float body = 1.0 - smoothstep(width * 0.55, width, abs(x));
        body *= 1.0 - smoothstep(0.78 + (n - 0.5) * 0.15, 1.0, y);
        float core = (1.0 - smoothstep(0.0, width * 0.45, abs(x))) * (1.0 - smoothstep(0.1, 0.6, y));
        vec3 deep = vec3(1.0, 0.36, 0.06);
        vec3 gold = vec3(1.0, 0.70, 0.26);
        vec3 white = vec3(1.0, 0.93, 0.78);
        vec3 col = mix(deep, gold, smoothstep(0.0, 0.7, body));
        col = mix(col, white, core);
        float a = body * uLife;
        gl_FragColor = vec4(col * uIntensity * a, a);
      }`,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
}

export function createFlame(opts = {}) {
  const geo = new THREE.PlaneGeometry(1, 1);
  geo.translate(0, 0.5, 0);
  const mesh = new THREE.Mesh(geo, createFlameMaterial(opts));
  mesh.frustumCulled = false;
  mesh.renderOrder = 5;
  return mesh;
}

// Soft radial glow and a thin horizontal anamorphic streak.
function glowTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grd.addColorStop(0, 'rgba(255,255,255,1)');
  grd.addColorStop(0.2, 'rgba(255,255,255,0.45)');
  grd.addColorStop(0.5, 'rgba(255,255,255,0.1)');
  grd.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
let _glowTex = null;
export function createGlow(color = 0xffb35c, size = 2, opacity = 0.5, streak = false) {
  _glowTex ||= glowTexture();
  const mat = new THREE.SpriteMaterial({
    map: _glowTex, color, transparent: true, opacity, depthWrite: false,
    blending: THREE.AdditiveBlending, fog: false,
  });
  const s = new THREE.Sprite(mat);
  s.scale.set(streak ? size * 7 : size, streak ? size * 0.12 : size, 1);
  s.renderOrder = 6;
  return s;
}

// GPU particles: embers rising in slow motion, golden dust, echo motes.
export function createParticles({ count = 200, color = 0xffc070, size = 0.05, additive = true } = {}) {
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(count * 3);
  const vel = new Float32Array(count * 3);
  const life = new Float32Array(count * 2); // age, lifetime
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aLife', new THREE.BufferAttribute(life, 2));
  const mat = new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(color) }, uSize: { value: size }, uScale: { value: 600 }, uBright: { value: 3 } },
    vertexShader: /* glsl */`
      attribute vec2 aLife;
      varying float vAlpha;
      uniform float uSize, uScale;
      void main() {
        float t = aLife.x / max(aLife.y, 1e-3);
        vAlpha = smoothstep(0.0, 0.1, t) * (1.0 - smoothstep(0.55, 1.0, t)) * step(aLife.x, aLife.y);
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = uSize * uScale / max(-mv.z, 0.1);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */`
      uniform vec3 uColor;
      uniform float uBright;
      varying float vAlpha;
      void main() {
        vec2 c = gl_PointCoord - 0.5;
        float d = length(c);
        float a = (1.0 - smoothstep(0.1, 0.5, d)) * vAlpha;
        if (a < 0.01) discard;
        gl_FragColor = vec4(uColor * uBright * a, a);
      }`,
    transparent: true,
    depthWrite: false,
    blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending,
  });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  points.renderOrder = 7;
  let cursor = 0;
  const sys = {
    points, pos, vel, life, count,
    emit(x, y, z, vx, vy, vz, lifetime) {
      const i = cursor;
      cursor = (cursor + 1) % count;
      pos[i * 3] = x; pos[i * 3 + 1] = y; pos[i * 3 + 2] = z;
      vel[i * 3] = vx; vel[i * 3 + 1] = vy; vel[i * 3 + 2] = vz;
      life[i * 2] = 0; life[i * 2 + 1] = lifetime;
    },
    update(dt, { drag = 0.2, lift = 0, swirl = 0, time = 0, attract = null } = {}) {
      for (let i = 0; i < count; i++) {
        const li = i * 2;
        if (life[li] >= life[li + 1]) continue;
        life[li] += dt;
        const k = i * 3;
        if (attract) {
          vel[k] += (attract.x - pos[k]) * attract.k * dt;
          vel[k + 1] += (attract.y - pos[k + 1]) * attract.k * dt;
          vel[k + 2] += (attract.z - pos[k + 2]) * attract.k * dt;
        }
        vel[k + 1] += lift * dt;
        if (swirl) {
          vel[k] += Math.sin(time * 1.3 + i) * swirl * dt;
          vel[k + 2] += Math.cos(time * 1.1 + i * 1.7) * swirl * dt;
        }
        const f = Math.max(0, 1 - drag * dt);
        vel[k] *= f; vel[k + 1] *= f; vel[k + 2] *= f;
        pos[k] += vel[k] * dt; pos[k + 1] += vel[k + 1] * dt; pos[k + 2] += vel[k + 2] * dt;
      }
      geo.attributes.position.needsUpdate = true;
      geo.attributes.aLife.needsUpdate = true;
    },
    clear() { for (let i = 0; i < count; i++) life[i * 2 + 1] = 0; },
  };
  for (let i = 0; i < count; i++) life[i * 2 + 1] = 0;
  return sys;
}
