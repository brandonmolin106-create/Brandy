// Builds the whole world: land, river, sky, mist, rocks, lights.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { createTerrain } from './terrain.js';
import { createSky, bakeEnvironment } from './sky.js';
import { createWater } from './water.js';
import { createMist } from './mist.js';
import { loadProps } from './props.js';
import { STAR_DIR } from './config.js';

const TEX = ['ground', 'cliff', 'shore', 'stone', 'planks'];

export async function loadTextures(renderer, onProgress) {
  const loader = new THREE.TextureLoader();
  const aniso = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const out = {};
  const jobs = [];
  for (const name of TEX) {
    for (const map of ['diff', 'nor', 'arm']) {
      jobs.push(loader.loadAsync(`assets/textures/${name}_${map}.webp`).then((t) => {
        t.wrapS = t.wrapT = THREE.RepeatWrapping;
        t.anisotropy = aniso;
        t.colorSpace = map === 'diff' ? THREE.SRGBColorSpace : THREE.NoColorSpace;
        out[`${name}_${map}`] = t;
        onProgress?.();
      }));
    }
  }
  await Promise.all(jobs);
  return out;
}

export async function buildWorld(renderer, scene, quality, onProgress) {
  const textures = await loadTextures(renderer, onProgress);

  const terrain = createTerrain(textures, quality);
  scene.add(terrain.group);
  onProgress?.();

  const sky = createSky();
  scene.add(sky);

  const water = createWater(terrain.heightTex, terrain.heightBounds);
  scene.add(water);

  const mist = createMist(terrain.heightTex, terrain.heightBounds);
  scene.add(mist);

  const gltf = new GLTFLoader();
  gltf.setMeshoptDecoder(MeshoptDecoder);
  const props = await loadProps(gltf, terrain.field, quality);
  scene.add(props.group);
  onProgress?.();

  // Starlight: a cold, high, shadowless key so the land reads in silhouette.
  const starlight = new THREE.DirectionalLight(0x8796ff, 0.5);
  starlight.position.set(STAR_DIR[0] * 40 + 10, 90, STAR_DIR[2] * 40);
  scene.add(starlight);
  const hemi = new THREE.HemisphereLight(0x33407a, 0x07070c, 0.7);
  scene.add(hemi);
  // The golden star lays a hair-thin rim of gold on everything facing it.
  const starRim = new THREE.DirectionalLight(0xffc27a, 0.4);
  starRim.position.set(STAR_DIR[0] * 100, STAR_DIR[1] * 100, STAR_DIR[2] * 100);
  scene.add(starRim);

  const env = bakeEnvironment(renderer, sky);
  scene.environment = env.bake();
  scene.environmentIntensity = 0.9;
  // Re-bake the ambient light from the sky as it is now (cold night, or turned to gold).
  env.setWarm = () => {
    const old = scene.environment;
    scene.environment = env.bake();
    old?.dispose?.();
  };

  return { textures, terrain, sky, water, mist, props, starlight, hemi, starRim, env };
}
