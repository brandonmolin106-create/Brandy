// Echoes: small leaves of light left along the journey. Faint until you listen.
// Each one gathered lights another part of the leaf and asks one of the song's questions.
import * as THREE from 'three';
import { ECHOES } from './config.js';
import { drawEmblem } from './emblem.js';
import { createParticles } from './fx.js';

function emblemSpriteTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  g.shadowColor = 'rgba(255,255,255,0.9)';
  g.shadowBlur = 10;
  drawEmblem(g, 256, { color: 'rgba(255,255,255,1)', stroke: 11, star: true, starColor: '#fff' });
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export function createEchoes(field) {
  const tex = emblemSpriteTexture();
  const group = new THREE.Group();
  group.name = 'echoes';
  const motes = createParticles({ count: 900, color: 0xcfd8ff, size: 0.045 });
  motes.points.material.uniforms.uBright.value = 2.4;
  const list = ECHOES.map((def, i) => {
    const [x, z] = def.pos;
    const y = field.sample(x, z) + 1.35;
    const mat = new THREE.SpriteMaterial({
      map: tex, color: 0xffd9a0, transparent: true, opacity: 0.1, depthWrite: false,
      blending: THREE.AdditiveBlending, fog: false,
    });
    const sprite = new THREE.Sprite(mat);
    sprite.scale.set(0.62, 0.68, 1);
    sprite.position.set(x, y, z);
    sprite.renderOrder = 8;
    group.add(sprite);
    return {
      def, index: i, sprite, mat,
      home: new THREE.Vector3(x, y, z),
      state: 'idle',   // idle | gathering | gathered
      heard: 0,        // 0..1 how strongly it answers the listen
      t: 0,
      from: new THREE.Vector3(),
    };
  });

  const api = {
    group, list, motes,
    gatheredCount() { return list.filter((e) => e.state !== 'idle').length; },
    reset(keep = []) {
      for (const e of list) {
        e.state = keep.includes(e.def.id) ? 'gathered' : 'idle';
        e.sprite.visible = e.state === 'idle';
        e.sprite.position.copy(e.home);
        e.heard = 0;
      }
    },
    // Returns the echo gathered this frame (or null).
    update(dt, t, { playerPos, listening, torchPos, pulseRadius }) {
      let gathered = null;
      for (const e of list) {
        if (e.state === 'gathered') continue;
        const s = e.sprite;
        if (e.state === 'gathering') {
          e.t += dt / 1.3;
          const k = Math.min(1, e.t);
          const ease = k * k * (3 - 2 * k);
          s.position.lerpVectors(e.from, torchPos, ease);
          s.position.y += Math.sin(k * Math.PI) * 0.8;
          s.scale.set(0.62 * (1 - ease * 0.85), 0.68 * (1 - ease * 0.85), 1);
          e.mat.opacity = 1 - ease * 0.6;
          if (Math.random() < 0.8) motes.emit(s.position.x, s.position.y, s.position.z, (Math.random() - 0.5) * 0.4, Math.random() * 0.3, (Math.random() - 0.5) * 0.4, 1.2);
          if (k >= 1) { e.state = 'gathered'; s.visible = false; }
          continue;
        }
        const d = s.position.distanceTo(playerPos);
        // The listen pulse lights echoes as its ring passes over them.
        const ringHit = pulseRadius > 0 && Math.abs(pulseRadius - d) < 3 ? 1 : 0;
        const target = Math.max(listening && d < 75 ? 1 : 0, ringHit, d < 9 ? 0.55 : 0);
        e.heard += (target - e.heard) * Math.min(1, dt * (target > e.heard ? 5 : 0.6));
        const bob = Math.sin(t * 1.3 + e.index) * 0.12;
        s.position.set(e.home.x, e.home.y + bob, e.home.z);
        const breathe = 1 + Math.sin(t * 2.2 + e.index * 1.7) * 0.06;
        s.scale.set(0.62 * breathe * (1 + e.heard * 0.35), 0.68 * breathe * (1 + e.heard * 0.35), 1);
        s.material.rotation = Math.sin(t * 0.5 + e.index) * 0.08;
        e.mat.opacity = 0.09 + e.heard * 0.95 + Math.sin(t * 3 + e.index) * 0.02;
        if (Math.random() < dt * (2 + e.heard * 16)) {
          const a = Math.random() * Math.PI * 2, r = 0.2 + Math.random() * 0.5;
          motes.emit(s.position.x + Math.cos(a) * r, s.position.y - 0.3 + Math.random() * 0.6, s.position.z + Math.sin(a) * r,
            Math.cos(a) * 0.05, 0.12 + Math.random() * 0.1, Math.sin(a) * 0.05, 2 + Math.random() * 2);
        }
        if (d < 1.9) {
          e.state = 'gathering';
          e.t = 0;
          e.from.copy(s.position);
          gathered = e;
        }
      }
      motes.update(dt, { drag: 0.5, lift: 0.02, swirl: 0.12, time: t });
      return gathered;
    },
    nearestIdle(pos) {
      let best = null, bd = 1e9;
      for (const e of list) {
        if (e.state !== 'idle') continue;
        const d = e.home.distanceTo(pos);
        if (d < bd) { bd = d; best = e; }
      }
      return best ? { echo: best, dist: bd } : null;
    },
  };
  return api;
}
