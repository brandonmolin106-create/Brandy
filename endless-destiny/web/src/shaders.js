// Shared GLSL and the global uniforms every lit surface in the world listens to:
// the torch, the cauldron fire, the gold wave, the listen pulse and the haze.
import * as THREE from 'three';
import { STAR_DIR } from './config.js';

export const U = {
  uTime: { value: 0 },
  uTorchPos: { value: new THREE.Vector3(0, -100, 0) },
  uTorchCol: { value: new THREE.Vector3(0, 0, 0) },
  uFirePos: { value: new THREE.Vector3(10, 34, -290) },
  uFireCol: { value: new THREE.Vector3(0, 0, 0) },
  uGoldCenter: { value: new THREE.Vector3(10, 30, -290) },
  uGoldRadius: { value: 0 },
  uGold: { value: 0 },
  uPulseCenter: { value: new THREE.Vector3() },
  uPulseRadius: { value: 0 },
  uPulseAmt: { value: 0 },
  uFogCol: { value: new THREE.Vector3(0.030, 0.030, 0.072) },
  uFogDensity: { value: 0.010 },
  uFogFalloff: { value: 0.045 },
  uFogBase: { value: 0 },
  uHaze: { value: 0.011 },
  uStarDir: { value: new THREE.Vector3(...STAR_DIR) },
};

export const ED_COMMON = /* glsl */`
uniform float uTime;
uniform vec3 uTorchPos;
uniform vec3 uTorchCol;
uniform vec3 uFirePos;
uniform vec3 uFireCol;
uniform vec3 uGoldCenter;
uniform float uGoldRadius;
uniform float uGold;
uniform vec3 uPulseCenter;
uniform float uPulseRadius;
uniform float uPulseAmt;
uniform vec3 uFogCol;
uniform float uFogDensity;
uniform float uFogFalloff;
uniform float uFogBase;
uniform float uHaze;
uniform vec3 uStarDir;

// Light scattered toward the eye by haze along a ray passing a point light.
float edScatter(vec3 ro, vec3 rd, float L, vec3 P) {
  vec3 op = P - ro;
  float t0 = dot(op, rd);
  float h = sqrt(max(dot(op, op) - t0 * t0, 0.02));
  return (atan((L - t0) / h) - atan(-t0 / h)) / h;
}

vec3 edFogColor() {
  return mix(uFogCol, uFogCol * vec3(2.3, 1.55, 0.8), uGold * 0.85);
}

// Height fog (denser low down, in the canyon and over the river) plus glow around the flames.
vec3 edFog(vec3 col, vec3 wp) {
  vec3 ro = cameraPosition;
  vec3 dv = wp - ro;
  float L = max(length(dv), 1e-3);
  vec3 rd = dv / L;
  float k = rd.y * uFogFalloff;
  float base = uFogDensity * exp(-(ro.y - uFogBase) * uFogFalloff);
  float optical = base * (abs(k * L) > 1e-3 ? (1.0 - exp(-k * L)) / k : L);
  float fog = 1.0 - exp(-optical);
  vec3 glow = uTorchCol * edScatter(ro, rd, L, uTorchPos) + uFireCol * edScatter(ro, rd, L, uFirePos) * 0.25;
  return mix(col, edFogColor(), fog) + glow * uHaze;
}

// Listen pulse ring and the golden wave that turns the world from blue to gold.
vec3 edWorldFx(vec3 c, vec3 alb, vec3 wp) {
  float dp = length(wp.xz - uPulseCenter.xz);
  float q = (dp - uPulseRadius) / 1.6;
  float ring = exp(-q * q) * uPulseAmt;
  float inner = (1.0 - smoothstep(0.0, uPulseRadius + 0.01, dp)) * uPulseAmt * 0.12;
  c += (alb + 0.03) * vec3(0.42, 0.48, 1.0) * (ring * 1.4 + inner);
  float dg = length(wp - uGoldCenter);
  float g = (dg - uGoldRadius) / 7.0;
  float front = exp(-g * g) * step(0.5, uGoldRadius) * (1.0 - smoothstep(500.0, 700.0, uGoldRadius));
  float inside = (1.0 - smoothstep(uGoldRadius - 40.0, uGoldRadius, dg)) * (1.0 - smoothstep(40.0, 420.0, dg) * 0.75);
  c += alb * vec3(1.0, 0.58, 0.18) * (front * 2.2 + inside * uGold * 0.12);
  return c;
}
`;

export const ED_SKY = /* glsl */`
float edHash13(vec3 p) {
  p = fract(p * 0.1031);
  p += dot(p, p.zyx + 31.32);
  return fract((p.x + p.y) * p.z);
}
vec3 edHash33(vec3 p) {
  p = fract(p * vec3(0.1031, 0.1030, 0.0973));
  p += dot(p, p.yxz + 33.33);
  return fract((p.xxy + p.yxx) * p.zyx);
}
float edNoise3(vec3 p) {
  vec3 i = floor(p);
  vec3 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  float n000 = edHash13(i), n100 = edHash13(i + vec3(1, 0, 0));
  float n010 = edHash13(i + vec3(0, 1, 0)), n110 = edHash13(i + vec3(1, 1, 0));
  float n001 = edHash13(i + vec3(0, 0, 1)), n101 = edHash13(i + vec3(1, 0, 1));
  float n011 = edHash13(i + vec3(0, 1, 1)), n111 = edHash13(i + vec3(1, 1, 1));
  return mix(mix(mix(n000, n100, f.x), mix(n010, n110, f.x), f.y),
             mix(mix(n001, n101, f.x), mix(n011, n111, f.x), f.y), f.z);
}
float edFbm3(vec3 p) {
  float s = 0.0, a = 0.5;
  for (int i = 0; i < 4; i++) { s += a * edNoise3(p); p *= 2.03; a *= 0.5; }
  return s;
}
float edStars(vec3 dir, float scale, float density, float sizeK) {
  vec3 p = dir * scale;
  vec3 cell = floor(p);
  vec3 f = fract(p);
  float on = step(1.0 - density, edHash13(cell));
  vec3 r = edHash33(cell + 17.0);
  vec3 d3 = f - (0.25 + 0.5 * r);
  float d2 = dot(d3, d3);
  float tw = 0.7 + 0.3 * sin(uTime * (0.8 + 2.5 * r.z) + r.x * 40.0);
  return on * exp(-d2 * sizeK) * (0.25 + 0.75 * r.y * r.y) * tw;
}
// The night: true black, deep indigo, midnight blue, soft violet — and one golden star.
vec3 edSky(vec3 dir, float starAmt) {
  float h = dir.y;
  vec3 zen = vec3(0.0035, 0.0045, 0.014);
  vec3 mid = vec3(0.009, 0.012, 0.036);
  vec3 hor = vec3(0.036, 0.031, 0.082);
  vec3 col = mix(hor, mid, smoothstep(0.0, 0.2, h));
  col = mix(col, zen, smoothstep(0.2, 0.85, h));
  col = mix(col, hor * 0.55, smoothstep(0.0, -0.12, h));
  vec3 bandN = normalize(vec3(0.42, 0.22, 0.88));
  float bd = dot(dir, bandN) / 0.26;
  float band = exp(-bd * bd);
  float neb = edFbm3(dir * 3.2 + vec3(0.0, 0.0, uTime * 0.0015));
  col += vec3(0.018, 0.016, 0.040) * band * (0.25 + neb * neb * 1.6) * smoothstep(-0.02, 0.25, h);
  float st = edStars(dir, 150.0, 0.11, 700.0) * 1.3 + edStars(dir, 330.0, 0.13, 1100.0) * 0.55;
  st *= smoothstep(-0.01, 0.1, h) * (1.0 - 0.45 * band);
  col += vec3(0.72, 0.8, 1.0) * st;
  col = mix(col, col * vec3(1.9, 1.35, 0.8) + vec3(0.03, 0.017, 0.005) * (1.0 - smoothstep(-0.05, 0.3, h)), uGold * 0.8);
  if (starAmt > 0.0) {
    float c = dot(dir, uStarDir);
    float x = max(0.0, 1.0 - c);
    vec3 gold = vec3(1.0, 0.68, 0.28);
    float core = exp(-x * 160000.0) * 16.0;
    float halo = exp(-x * 9000.0) * 0.8 + exp(-x * 900.0) * 0.04;
    vec3 t = normalize(cross(uStarDir, vec3(0.0, 1.0, 0.0)));
    vec3 b = cross(t, uStarDir);
    float u = dot(dir, t), v = dot(dir, b);
    float spikes = (exp(-abs(v) * 1100.0) * exp(-abs(u) * 55.0) + exp(-abs(u) * 1100.0) * exp(-abs(v) * 55.0)) * 7.0 * step(0.0, c);
    col += gold * (core + halo + spikes) * starAmt;
  }
  return col;
}
`;

// Swap three.js fog for our height fog on patched materials.
THREE.ShaderChunk.fog_fragment = /* glsl */`
#ifdef USE_FOG
  #ifdef ED_PATCHED
    gl_FragColor.rgb = edFog(gl_FragColor.rgb, vEdWorld);
  #else
    #ifdef FOG_EXP2
      float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
    #else
      float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
    #endif
    gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
  #endif
#endif
`;

// Hook a built-in PBR material into the world uniforms (fog, gold wave, pulse).
export function patchMaterial(mat, key, opts = {}) {
  const { uniforms = {}, vertexPars = '', beginNormal = '', beginVertex = '', vertex = '', fragPars = '', frag = null } = opts;
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, U, uniforms);
    shader.vertexShader = '#define ED_PATCHED\n' + shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vEdWorld;\nuniform float uTime;\n' + vertexPars)
      .replace('#include <beginnormal_vertex>', '#include <beginnormal_vertex>\n' + beginNormal)
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n' + beginVertex)
      .replace('#include <project_vertex>', `#include <project_vertex>
        vec4 edW = vec4(transformed, 1.0);
        #ifdef USE_INSTANCING
          edW = instanceMatrix * edW;
        #endif
        vEdWorld = (modelMatrix * edW).xyz;
        ${vertex}`);
    let fs = '#define ED_PATCHED\n' + shader.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vEdWorld;\n' + ED_COMMON + fragPars)
      .replace('#include <opaque_fragment>',
        'outgoingLight = edWorldFx(outgoingLight, diffuseColor.rgb, vEdWorld);\n#include <opaque_fragment>');
    if (frag) fs = frag(fs);
    shader.fragmentShader = fs;
  };
  mat.customProgramCacheKey = () => 'ed-' + key;
  return mat;
}
