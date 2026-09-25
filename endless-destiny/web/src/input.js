// Keyboard + mouse, touch (joystick, look pad, buttons) and gamepad, merged into one state.
export function createInput(canvas, touchUI) {
  const keys = new Set();
  const state = {
    move: { x: 0, y: 0 },      // x = right, y = forward
    look: { x: 0, y: 0 },      // accumulated this frame (radians-ish)
    hurry: false,
    listen: false,
    act: false,                // true for one frame when pressed
    pause: false,
    usingTouch: false,
    usingPad: false,
    sensitivity: 1,
  };
  let actQueued = false, pauseQueued = false;
  let pointerLocked = false;
  let dragging = false, lastX = 0, lastY = 0;

  const onKey = (e, down) => {
    if (e.target && ['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return;
    const k = e.code;
    if (down) {
      if (!keys.has(k) && (k === 'KeyE' || k === 'Enter' || k === 'Space')) actQueued = true;
      if (!keys.has(k) && (k === 'Escape' || k === 'KeyP')) pauseQueued = true;
      keys.add(k);
    } else keys.delete(k);
    if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(k)) e.preventDefault();
  };
  addEventListener('keydown', (e) => onKey(e, true));
  addEventListener('keyup', (e) => onKey(e, false));
  addEventListener('blur', () => keys.clear());

  // Mouse: pointer lock where allowed, click-and-drag everywhere else.
  canvas.addEventListener('mousedown', (e) => {
    if (e.button === 2) { state.mouseListen = true; return; }
    dragging = true; lastX = e.clientX; lastY = e.clientY;
    if (!pointerLocked && canvas.requestPointerLock) {
      try {
        const p = canvas.requestPointerLock();
        if (p && p.catch) p.catch(() => {});
      } catch { /* pointer lock unavailable: drag to look */ }
    }
  });
  addEventListener('mouseup', (e) => {
    if (e.button === 2) state.mouseListen = false;
    dragging = false;
  });
  canvas.addEventListener('contextmenu', (e) => e.preventDefault());
  document.addEventListener('pointerlockchange', () => { pointerLocked = document.pointerLockElement === canvas; });
  addEventListener('mousemove', (e) => {
    if (pointerLocked) {
      state.look.x += e.movementX * 0.0022 * state.sensitivity;
      state.look.y += e.movementY * 0.0022 * state.sensitivity;
    } else if (dragging) {
      state.look.x += (e.clientX - lastX) * 0.004 * state.sensitivity;
      state.look.y += (e.clientY - lastY) * 0.004 * state.sensitivity;
      lastX = e.clientX; lastY = e.clientY;
    }
  });

  // Touch: left half = floating joystick, right half = look.
  const touches = new Map();
  const joy = touchUI?.joy, knob = touchUI?.knob;
  const onTouchStart = (e) => {
    state.usingTouch = true;
    document.body.classList.add('touch');
    for (const t of e.changedTouches) {
      const left = t.clientX < innerWidth * 0.45;
      touches.set(t.identifier, { kind: left ? 'move' : 'look', x0: t.clientX, y0: t.clientY, x: t.clientX, y: t.clientY });
      if (left && joy) {
        joy.style.left = t.clientX + 'px';
        joy.style.top = t.clientY + 'px';
        joy.classList.add('on');
      }
    }
    e.preventDefault();
  };
  const onTouchMove = (e) => {
    for (const t of e.changedTouches) {
      const s = touches.get(t.identifier);
      if (!s) continue;
      if (s.kind === 'look') {
        state.look.x += (t.clientX - s.x) * 0.006 * state.sensitivity;
        state.look.y += (t.clientY - s.y) * 0.006 * state.sensitivity;
      }
      s.x = t.clientX; s.y = t.clientY;
    }
    e.preventDefault();
  };
  const onTouchEnd = (e) => {
    for (const t of e.changedTouches) {
      const s = touches.get(t.identifier);
      if (s?.kind === 'move' && joy) joy.classList.remove('on');
      touches.delete(t.identifier);
    }
  };
  canvas.addEventListener('touchstart', onTouchStart, { passive: false });
  canvas.addEventListener('touchmove', onTouchMove, { passive: false });
  canvas.addEventListener('touchend', onTouchEnd);
  canvas.addEventListener('touchcancel', onTouchEnd);

  if (touchUI?.listenBtn) {
    const b = touchUI.listenBtn;
    const on = (e) => { e.preventDefault(); state.touchListen = true; b.classList.add('held'); };
    const off = () => { state.touchListen = false; b.classList.remove('held'); };
    b.addEventListener('touchstart', on, { passive: false });
    b.addEventListener('touchend', off);
    b.addEventListener('touchcancel', off);
  }
  if (touchUI?.actBtn) {
    touchUI.actBtn.addEventListener('touchstart', (e) => { e.preventDefault(); actQueued = true; }, { passive: false });
  }

  let padActPrev = false, padPausePrev = false;
  state.update = () => {
    let mx = 0, my = 0;
    if (keys.has('KeyW') || keys.has('ArrowUp')) my += 1;
    if (keys.has('KeyS') || keys.has('ArrowDown')) my -= 1;
    if (keys.has('KeyD') || keys.has('ArrowRight')) mx += 1;
    if (keys.has('KeyA') || keys.has('ArrowLeft')) mx -= 1;
    for (const s of touches.values()) {
      if (s.kind !== 'move') continue;
      const dx = s.x - s.x0, dy = s.y - s.y0;
      const len = Math.hypot(dx, dy), max = 56;
      const k = Math.min(len, max) / max;
      if (len > 4) { mx += (dx / len) * k; my -= (dy / len) * k; }
      if (knob) knob.style.transform = `translate(${(dx / Math.max(len, 1)) * Math.min(len, max)}px, ${(dy / Math.max(len, 1)) * Math.min(len, max)}px)`;
    }
    state.hurry = keys.has('ShiftLeft') || keys.has('ShiftRight');
    let padListen = false;
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    for (const p of pads) {
      if (!p) continue;
      const dz = (v) => (Math.abs(v) < 0.15 ? 0 : v);
      const lx = dz(p.axes[0] || 0), ly = dz(p.axes[1] || 0), rx = dz(p.axes[2] || 0), ry = dz(p.axes[3] || 0);
      if (lx || ly || rx || ry) state.usingPad = true;
      mx += lx; my -= ly;
      state.look.x += rx * 0.045 * state.sensitivity;
      state.look.y += ry * 0.035 * state.sensitivity;
      const a = p.buttons[0]?.pressed;
      if (a && !padActPrev) actQueued = true;
      padActPrev = a;
      const st = p.buttons[9]?.pressed;
      if (st && !padPausePrev) pauseQueued = true;
      padPausePrev = st;
      padListen = (p.buttons[6]?.value || 0) > 0.3 || (p.buttons[7]?.value || 0) > 0.3 || p.buttons[2]?.pressed;
      if (p.buttons[10]?.pressed) state.hurry = true;
    }
    const len = Math.hypot(mx, my);
    if (len > 1) { mx /= len; my /= len; }
    state.move.x = mx;
    state.move.y = my;
    state.listen = keys.has('KeyQ') || keys.has('KeyL') || !!state.mouseListen || !!state.touchListen || padListen;
    state.act = actQueued;
    state.pause = pauseQueued;
    actQueued = false;
    pauseQueued = false;
  };
  state.consumeLook = () => {
    const l = { x: state.look.x, y: state.look.y };
    state.look.x = 0; state.look.y = 0;
    return l;
  };
  state.releasePointer = () => { if (document.exitPointerLock && pointerLocked) document.exitPointerLock(); };
  return state;
}
