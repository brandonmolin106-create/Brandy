// The night sky dome and the lighting environment it provides.
import * as THREE from 'three';
import { U, ED_COMMON, ED_SKY } from './shaders.js';

export function createSky() {
  const mat = new THREE.ShaderMaterial({
    uniforms: { ...U, uStarAmt: { value: 1 } },
    vertexShader: /* glsl */`
      varying vec3 vWorld;
      void main() {
        vec4 w = modelMatrix * vec4(position, 1.0);
        vWorld = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w;
        gl_Position.z = gl_Position.w; // pin to the far plane
      }`,
    fragmentShader: /* glsl */`
      ${ED_COMMON}
      ${ED_SKY}
      uniform float uStarAmt;
      varying vec3 vWorld;
      void main() {
        vec3 dir = normalize(vWorld - cameraPosition);
        vec3 col = edSky(dir, uStarAmt);
        // Haze near the horizon matches the fog so land fades into sky.
        float horizonFog = 1.0 - smoothstep(0.0, 0.16, dir.y);
        col = mix(col, edFogColor(), horizonFog * 0.55);
        vec3 glow = uTorchCol * edScatter(cameraPosition, dir, 3000.0, uTorchPos)
                  + uFireCol * edScatter(cameraPosition, dir, 3000.0, uFirePos) * 0.35;
        col += glow * uHaze;
        gl_FragColor = vec4(col, 1.0);
      }`,
    side: THREE.BackSide,
    depthWrite: false,
    depthTest: true,
  });
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(2500, 48, 24), mat);
  mesh.name = 'sky';
  mesh.frustumCulled = false;
  mesh.renderOrder = -10;
  return mesh;
}

// Bake the sky (without the star's glare) into an environment map for PBR ambient light.
export function bakeEnvironment(renderer, sky) {
  const envScene = new THREE.Scene();
  const envSky = sky.clone();
  envSky.material = sky.material.clone();
  envSky.material.uniforms = { ...U, uStarAmt: { value: 0 } };
  envSky.position.set(0, 0, 0);
  envScene.add(envSky);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const cubeRT = new THREE.WebGLCubeRenderTarget(128, { type: THREE.HalfFloatType });
  const cubeCam = new THREE.CubeCamera(1, 5000, cubeRT);
  envScene.add(cubeCam);
  const bake = () => {
    cubeCam.update(renderer, envScene);
    const rt = pmrem.fromCubemap(cubeRT.texture);
    return rt.texture;
  };
  return { bake, dispose: () => { pmrem.dispose(); cubeRT.dispose(); } };
}
