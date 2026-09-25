// Walking the journey: movement over the land, the bridge and the steps, plus the
// third-person camera that follows the Torchbearer from behind.
import * as THREE from 'three';
import { pathInfo } from './terrainfield.js';
import { BRIDGE_X, RIM_SOUTH_Z, RIM_NORTH_Z, PLATFORM, PLATEAU } from './config.js';
import { DECK_Y } from './bridge.js';

const WALK = 3.0, HURRY = 5.0, BRIDGE_MAX = 2.4;

export function createPlayer({ field, colliders, platform, bridge, camera }) {
  const p = {
    pos: new THREE.Vector3(),
    vel: new THREE.Vector2(),
    yaw: 0,
    speed: 0,
    camYaw: 0,
    camPitch: 0.12,
    camDist: 4.2,
    lastLook: 0,
    control: true,         // player has control of movement
    camFree: true,         // player has control of the camera
    maxS: Infinity,        // furthest along the route they may walk (story gating)
    blockedReason: null,
    onBridge: false,
    bridgeActive: false,   // planks may form
    surface: 'ground',
    camTarget: new THREE.Vector3(),
    camPos: new THREE.Vector3(),
  };

  function onBridgeCorridor(x, z) {
    return Math.abs(x - BRIDGE_X) < 1.05 && z < RIM_SOUTH_Z + 0.35 && z > RIM_NORTH_Z - 1.3;
  }
  function groundAt(x, z) {
    const r = Math.hypot(x - PLATFORM.x, z - PLATFORM.z);
    if (r < PLATFORM.radius + 0.05) return { h: PLATEAU + platform.stepHeight(r), surface: 'stone' };
    if (onBridgeCorridor(x, z) && z < RIM_SOUTH_Z + 0.2) return { h: DECK_Y, surface: 'wood', bridge: true };
    return { h: field.sample(x, z), surface: 'ground' };
  }
  p.groundAt = groundAt;

  function canStand(x, z, fromH) {
    const g = groundAt(x, z);
    if (g.bridge) {
      if (!p.bridgeActive && z < bridge.frontierZ() - 0.1) return { ok: false, why: 'edge' };
      return { ok: true, g };
    }
    if (g.h < -0.35) return { ok: false, why: 'water' };
    if (g.h < fromH - 1.1) return { ok: false, why: 'edge' };
    // Steps up to 0.32 m are fine; otherwise the ground itself must be gentle enough to climb.
    if (g.h > fromH + 0.32) return { ok: false, why: 'steep' };
    if (g.surface === 'ground' && g.h > fromH + 0.01 && field.normal(x, z)[1] < 0.74) return { ok: false, why: 'steep' };
    const info = pathInfo(x, z);
    if (info.d > 40) return { ok: false, why: 'far' };
    if (info.s > p.maxS) return { ok: false, why: 'gate' };
    for (const c of colliders) {
      const dx = x - c.x, dz = z - c.z;
      if (dx * dx + dz * dz < (c.r + 0.35) * (c.r + 0.35)) return { ok: false, why: 'rock' };
    }
    return { ok: true, g };
  }

  p.place = (x, z, yaw) => {
    const g = groundAt(x, z);
    p.pos.set(x, g.h, z);
    p.yaw = yaw;
    p.camYaw = yaw;
    p.vel.set(0, 0);
    p.snapCamera();
  };

  p.update = (dt, input) => {
    // Camera look.
    const look = input.consumeLook();
    if (p.camFree && (look.x || look.y)) {
      p.camYaw -= look.x;
      p.camPitch = THREE.MathUtils.clamp(p.camPitch + look.y, -0.55, 0.85);
      p.lastLook = 0;
    } else p.lastLook += dt;

    let mx = 0, my = 0;
    if (p.control) { mx = input.move.x; my = input.move.y; }
    const fx = -Math.sin(p.camYaw), fz = -Math.cos(p.camYaw);
    const rx = Math.cos(p.camYaw), rz = -Math.sin(p.camYaw);
    let dx = fx * my + rx * mx, dz = fz * my + rz * mx;
    const len = Math.hypot(dx, dz);
    let max = input.hurry ? HURRY : WALK;
    if (p.onBridge) max = Math.min(max, BRIDGE_MAX);
    if (len > 1) { dx /= len; dz /= len; }
    const accel = Math.min(1, dt * (len > 0.01 ? 5 : 7));
    p.vel.x += (dx * max - p.vel.x) * accel;
    p.vel.y += (dz * max - p.vel.y) * accel;

    // Move with sliding: try the full step, then each axis.
    p.blockedReason = null;
    const stepX = p.vel.x * dt, stepZ = p.vel.y * dt;
    const tryMove = (nx, nz) => {
      const r = canStand(nx, nz, p.pos.y);
      if (r.ok) { p.pos.x = nx; p.pos.z = nz; return r.g; }
      p.blockedReason = r.why;
      return null;
    };
    let g = null;
    if (stepX || stepZ) {
      g = tryMove(p.pos.x + stepX, p.pos.z + stepZ)
        || tryMove(p.pos.x + stepX, p.pos.z)
        || tryMove(p.pos.x, p.pos.z + stepZ);
      if (!g) p.vel.multiplyScalar(0.5);
    }
    // Keep to the planks while over the canyon.
    const nowG = groundAt(p.pos.x, p.pos.z);
    p.onBridge = !!nowG.bridge;
    if (p.onBridge) p.pos.x = THREE.MathUtils.clamp(p.pos.x, BRIDGE_X - 0.8, BRIDGE_X + 0.8);
    p.surface = nowG.surface;
    // Smooth the height so steps and bumps do not jolt the camera.
    p.pos.y += (nowG.h - p.pos.y) * Math.min(1, dt * 14);

    p.speed = Math.hypot(p.vel.x, p.vel.y);
    if (p.speed > 0.2) {
      const want = Math.atan2(-p.vel.x, -p.vel.y);
      let d = want - p.yaw;
      d = Math.atan2(Math.sin(d), Math.cos(d));
      p.yaw += d * Math.min(1, dt * 7);
      // Ease the camera back behind the torchbearer while walking.
      if (p.camFree && p.lastLook > 1.6) {
        let c = p.yaw - p.camYaw;
        c = Math.atan2(Math.sin(c), Math.cos(c));
        p.camYaw += c * Math.min(1, dt * 0.8);
      }
    }
  };

  const tmp = new THREE.Vector3();
  function desiredCamera(out) {
    const cp = Math.cos(p.camPitch), sp = Math.sin(p.camPitch);
    p.camTarget.set(p.pos.x, p.pos.y + 1.55, p.pos.z);
    // Over the right shoulder.
    const sideX = Math.cos(p.camYaw) * 0.38, sideZ = -Math.sin(p.camYaw) * 0.38;
    out.set(
      p.camTarget.x + Math.sin(p.camYaw) * cp * p.camDist + sideX,
      p.camTarget.y + sp * p.camDist + 0.2,
      p.camTarget.z + Math.cos(p.camYaw) * cp * p.camDist + sideZ,
    );
    const gh = groundAt(out.x, out.z).h;
    if (out.y < gh + 0.45) out.y = gh + 0.45;
    return out;
  }
  p.snapCamera = () => {
    desiredCamera(p.camPos);
    camera.position.copy(p.camPos);
    camera.lookAt(p.camTarget.x - Math.cos(p.camYaw) * -0.38, p.camTarget.y, p.camTarget.z);
  };
  p.updateCamera = (dt) => {
    desiredCamera(tmp);
    p.camPos.lerp(tmp, Math.min(1, dt * 6));
    camera.position.copy(p.camPos);
    const lookX = p.camTarget.x + Math.cos(p.camYaw) * 0.38 - Math.sin(p.camYaw) * 3;
    const lookZ = p.camTarget.z - Math.sin(p.camYaw) * 0.38 - Math.cos(p.camYaw) * 3;
    camera.lookAt(lookX, p.camTarget.y - Math.sin(p.camPitch) * 1.2, lookZ);
  };
  return p;
}
