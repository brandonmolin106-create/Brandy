// Cinema look: bloom, ACES, then film grain, vignette, gentle halation, letterbox and fades.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';

const CinemaShader = {
  uniforms: {
    tDiffuse: { value: null },
    uTime: { value: 0 },
    uFade: { value: 1 },
    uBars: { value: 0 },
    uGrain: { value: 0.055 },
    uVignette: { value: 0.55 },
    uAspect: { value: 1.7 },
    uWhite: { value: 0 },
  },
  vertexShader: /* glsl */`
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: /* glsl */`
    uniform sampler2D tDiffuse;
    uniform float uTime, uFade, uBars, uGrain, uVignette, uAspect, uWhite;
    varying vec2 vUv;
    float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233)) + uTime * 3.7) * 43758.5453); }
    void main() {
      vec2 uv = vUv;
      vec2 c = uv - 0.5;
      // Slight lens edge falloff and colour fringing.
      float r2 = dot(c * vec2(uAspect, 1.0), c * vec2(uAspect, 1.0));
      vec2 off = c * 0.0022 * r2;
      vec3 col;
      col.r = texture2D(tDiffuse, uv + off).r;
      col.g = texture2D(tDiffuse, uv).g;
      col.b = texture2D(tDiffuse, uv - off).b;
      col *= 1.0 - uVignette * smoothstep(0.15, 1.1, r2);
      // Fine 35mm grain, stronger in the shadows.
      float g = hash(uv * vec2(1920.0, 1080.0)) - 0.5;
      float lum = dot(col, vec3(0.299, 0.587, 0.114));
      col += g * uGrain * (1.0 - lum * 0.7);
      col = mix(col, vec3(1.0, 0.9, 0.7), uWhite);
      col *= uFade;
      // 2.39:1 letterbox for cinematic moments.
      float barH = uBars * 0.5 * (1.0 - (16.0 / 9.0) / 2.39);
      if (uv.y < barH || uv.y > 1.0 - barH) col = vec3(0.0);
      gl_FragColor = vec4(col, 1.0);
    }`,
};

export function createPost(renderer, scene, camera, quality) {
  const size = renderer.getSize(new THREE.Vector2());
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(size.x * quality.bloomScale, size.y * quality.bloomScale), 0.6, 0.5, 0.85);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  const cinema = new ShaderPass(CinemaShader);
  composer.addPass(cinema);
  return {
    composer, bloom, cinema,
    setSize(w, h) {
      composer.setSize(w, h);
      bloom.setSize(w * quality.bloomScale, h * quality.bloomScale);
      cinema.uniforms.uAspect.value = w / h;
    },
    render(t) {
      cinema.uniforms.uTime.value = t;
      composer.render();
    },
  };
}
