// Sound, all synthesised live: the river, night air, a low sacred drone, the breath of
// the flame, wooden knocks and bell tones for each plank, the impact and roar of the fire.
export function createAudio() {
  let ctx = null;
  let master, comp, reverb, reverbSend, amb, sfx;
  let noiseBuf = null;
  const nodes = {};
  let muted = false;
  let userVolume = 0.9;

  function makeNoise(seconds = 3) {
    const len = ctx.sampleRate * seconds;
    const buf = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = buf.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0;
    for (let i = 0; i < len; i++) {
      const w = Math.random() * 2 - 1;
      // Pinkish noise: gentler than white, closer to air and water.
      b0 = 0.99765 * b0 + w * 0.099046;
      b1 = 0.963 * b1 + w * 0.2965164;
      b2 = 0.57 * b2 + w * 1.0526913;
      d[i] = (b0 + b1 + b2 + w * 0.1848) * 0.18;
    }
    return buf;
  }
  function makeImpulse(seconds = 4.5, decay = 2.4) {
    const len = ctx.sampleRate * seconds;
    const buf = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let c = 0; c < 2; c++) {
      const d = buf.getChannelData(c);
      for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, decay);
    }
    return buf;
  }
  function loopNoise() {
    const s = ctx.createBufferSource();
    s.buffer = noiseBuf;
    s.loop = true;
    s.loopStart = Math.random() * 1.5;
    s.start(0, Math.random() * 2);
    return s;
  }
  function gain(v, to) {
    const g = ctx.createGain();
    g.gain.value = v;
    if (to) g.connect(to);
    return g;
  }
  function filter(type, freq, q = 0.7, to) {
    const f = ctx.createBiquadFilter();
    f.type = type;
    f.frequency.value = freq;
    f.Q.value = q;
    if (to) f.connect(to);
    return f;
  }
  function lfo(freq, depth, target) {
    const o = ctx.createOscillator();
    o.frequency.value = freq;
    const g = gain(depth);
    o.connect(g);
    g.connect(target);
    o.start();
    return o;
  }

  const api = {
    get ready() { return !!ctx; },
    get ctx() { return ctx; },
    start() {
      if (ctx) { if (ctx.state === 'suspended') ctx.resume(); return; }
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      ctx = new AC();
      noiseBuf = makeNoise();
      comp = ctx.createDynamicsCompressor();
      comp.threshold.value = -16;
      comp.ratio.value = 3;
      comp.connect(ctx.destination);
      master = gain(muted ? 0 : userVolume, comp);
      reverb = ctx.createConvolver();
      reverb.buffer = makeImpulse();
      reverbSend = gain(0.5, reverb);
      reverb.connect(master);
      amb = gain(1, master);
      sfx = gain(1, master);

      // River: a wide soft wash near the shores.
      const river = loopNoise();
      const rBp = filter('bandpass', 520, 0.5);
      const rLp = filter('lowpass', 1500, 0.5);
      nodes.river = gain(0, amb);
      river.connect(rBp); rBp.connect(rLp); rLp.connect(nodes.river);
      lfo(0.13, 180, rBp.frequency);

      // Night air.
      const air = loopNoise();
      const aLp = filter('lowpass', 380, 0.4);
      nodes.air = gain(0.05, amb);
      air.connect(aLp); aLp.connect(nodes.air);
      lfo(0.07, 0.025, nodes.air.gain);

      // Huge hollow wind rising from the canyon.
      const wind = loopNoise();
      const wBp = filter('bandpass', 170, 1.6);
      nodes.wind = gain(0, amb);
      wind.connect(wBp); wBp.connect(nodes.wind);
      lfo(0.05, 60, wBp.frequency);

      // Low sacred drone: A and E, slowly breathing.
      const drone = gain(0.0, amb);
      nodes.drone = drone;
      const dLp = filter('lowpass', 420, 0.8, drone);
      lfo(0.03, 160, dLp.frequency);
      for (const [f, type, v] of [[55, 'sine', 0.5], [82.41, 'triangle', 0.22], [110.2, 'sine', 0.25], [164.8, 'sine', 0.08]]) {
        const o = ctx.createOscillator();
        o.type = type;
        o.frequency.value = f;
        o.detune.value = (Math.random() - 0.5) * 8;
        const g = gain(v, dLp);
        o.connect(g);
        o.start();
      }
      drone.gain.setTargetAtTime(0.09, ctx.currentTime, 4);

      // The breath of the flame.
      const fl = loopNoise();
      const fLp = filter('lowpass', 420, 0.6);
      nodes.flame = gain(0, amb);
      fl.connect(fLp); fLp.connect(nodes.flame);

      // The roar of the great fire.
      const roar = loopNoise();
      const roLp = filter('lowpass', 700, 0.5);
      const roBp = filter('peaking', 180, 1, roLp);
      roBp.gain.value = 8;
      nodes.roar = gain(0, amb);
      roar.connect(roBp); roLp.connect(nodes.roar);
      lfo(0.4, 0.02, nodes.roar.gain);
    },
    setMuted(m) {
      muted = m;
      if (master) master.gain.setTargetAtTime(m ? 0 : userVolume, ctx.currentTime, 0.1);
    },
    setVolume(v) {
      userVolume = v;
      if (master && !muted) master.gain.setTargetAtTime(v, ctx.currentTime, 0.1);
    },
    // Continuous layers, set every frame.
    setLayers({ river = 0, wind = 0, flame = 0, roar = 0, duck = 0 } = {}) {
      if (!ctx) return;
      const t = ctx.currentTime;
      nodes.river.gain.setTargetAtTime(river * 0.34, t, 0.5);
      nodes.wind.gain.setTargetAtTime(wind * 0.55, t, 0.6);
      nodes.flame.gain.setTargetAtTime(flame * 0.1, t, 0.3);
      nodes.roar.gain.setTargetAtTime(roar * 0.5, t, 0.4);
      amb.gain.setTargetAtTime(1 - duck * 0.45, t, 0.3);
    },
    setListener(pos, fwd) {
      if (!ctx) return;
      const L = ctx.listener;
      if (L.positionX) {
        L.positionX.value = pos.x; L.positionY.value = pos.y; L.positionZ.value = pos.z;
        L.forwardX.value = fwd.x; L.forwardY.value = fwd.y; L.forwardZ.value = fwd.z;
        L.upX.value = 0; L.upY.value = 1; L.upZ.value = 0;
      } else if (L.setPosition) {
        L.setPosition(pos.x, pos.y, pos.z);
        L.setOrientation(fwd.x, fwd.y, fwd.z, 0, 1, 0);
      }
    },
    step(surface = 'ground', vol = 1) {
      if (!ctx) return;
      const t = ctx.currentTime;
      const s = ctx.createBufferSource();
      s.buffer = noiseBuf;
      const f = filter('bandpass', surface === 'stone' ? 900 : surface === 'wood' ? 420 : 1500, 0.9);
      const g = gain(0, sfx);
      s.connect(f); f.connect(g);
      const v = (surface === 'wood' ? 0.25 : 0.12) * vol;
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(v, t + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0008, t + (surface === 'ground' ? 0.16 : 0.1));
      s.start(t, Math.random() * 2, 0.25);
    },
    // A deep wooden knock and a soft bell tone: one plank, one step.
    plank(i) {
      if (!ctx) return;
      const t = ctx.currentTime;
      const o = ctx.createOscillator();
      o.type = 'sine';
      o.frequency.setValueAtTime(150, t);
      o.frequency.exponentialRampToValueAtTime(70, t + 0.12);
      const g = gain(0, sfx);
      o.connect(g);
      g.gain.setValueAtTime(0.0001, t);
      g.gain.linearRampToValueAtTime(0.5, t + 0.005);
      g.gain.exponentialRampToValueAtTime(0.0005, t + 0.35);
      o.start(t); o.stop(t + 0.4);
      const scale = [220, 261.63, 293.66, 329.63, 392, 440, 523.25, 587.33, 659.25, 783.99, 880];
      const base = scale[i % scale.length] * (i % 22 >= 11 ? 1 : 0.5) * 2;
      api.bell(base, 0.06, 2.6);
    },
    bell(freq, vol = 0.07, dur = 3) {
      if (!ctx) return;
      const t = ctx.currentTime;
      const out = gain(0, sfx);
      out.connect(reverbSend);
      out.gain.setValueAtTime(0.0001, t);
      out.gain.linearRampToValueAtTime(vol, t + 0.01);
      out.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      for (const [r, a] of [[1, 1], [2.76, 0.35], [5.4, 0.12], [8.93, 0.05]]) {
        const o = ctx.createOscillator();
        o.frequency.value = freq * r;
        const g = gain(a, out);
        o.connect(g);
        o.start(t); o.stop(t + dur);
      }
    },
    // Soft glassy shimmer: flame gathered, echo heard.
    shimmer(vol = 0.05, dur = 2.8, base = 1320) {
      if (!ctx) return;
      const t = ctx.currentTime;
      const out = gain(0, sfx);
      out.connect(reverbSend);
      out.gain.setValueAtTime(0.0001, t);
      out.gain.linearRampToValueAtTime(vol, t + 0.25);
      out.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      for (let k = 0; k < 7; k++) {
        const o = ctx.createOscillator();
        o.frequency.value = base * (1 + k * 0.5) * (1 + (Math.random() - 0.5) * 0.01);
        const g = gain(0.18 / (k + 1), out);
        const tr = ctx.createOscillator();
        tr.frequency.value = 4 + Math.random() * 3;
        const tg = gain(0.08 / (k + 1), g.gain);
        tr.connect(tg);
        o.connect(g);
        o.start(t); o.stop(t + dur);
        tr.start(t); tr.stop(t + dur);
      }
    },
    // An echo answering from its place in the world.
    echoAt(pos, delay = 0) {
      if (!ctx) return;
      const t = ctx.currentTime + delay;
      const p = ctx.createPanner();
      p.panningModel = 'HRTF';
      p.distanceModel = 'inverse';
      p.refDistance = 4;
      p.rolloffFactor = 0.7;
      if (p.positionX) { p.positionX.value = pos.x; p.positionY.value = pos.y; p.positionZ.value = pos.z; }
      else p.setPosition(pos.x, pos.y, pos.z);
      p.connect(sfx);
      p.connect(reverbSend);
      for (const [f, a] of [[987.77, 0.1], [1318.5, 0.06], [1975.5, 0.03]]) {
        const o = ctx.createOscillator();
        o.frequency.value = f;
        const g = gain(0, p);
        g.gain.setValueAtTime(0.0001, t);
        g.gain.linearRampToValueAtTime(a, t + 0.05);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 1.8);
        o.connect(g);
        o.start(t); o.stop(t + 1.9);
      }
    },
    listenSweep() {
      if (!ctx) return;
      const t = ctx.currentTime;
      const s = ctx.createBufferSource();
      s.buffer = noiseBuf;
      const f = filter('bandpass', 300, 4);
      f.frequency.setValueAtTime(300, t);
      f.frequency.exponentialRampToValueAtTime(2400, t + 1.2);
      const g = gain(0, sfx);
      g.connect(reverbSend);
      s.connect(f); f.connect(g);
      g.gain.setValueAtTime(0.0001, t);
      g.gain.linearRampToValueAtTime(0.1, t + 0.4);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 1.6);
      s.start(t, 0, 1.7);
    },
    // One second of total silence.
    silence(seconds = 1) {
      if (!ctx) return;
      const t = ctx.currentTime;
      master.gain.cancelScheduledValues(t);
      master.gain.setValueAtTime(master.gain.value, t);
      master.gain.linearRampToValueAtTime(0, t + 0.15);
      master.gain.setValueAtTime(0, t + seconds);
      master.gain.linearRampToValueAtTime(muted ? 0 : userVolume, t + seconds + 0.02);
    },
    // A deep chest-shaking impact.
    boom() {
      if (!ctx) return;
      const t = ctx.currentTime;
      const o = ctx.createOscillator();
      o.frequency.setValueAtTime(92, t);
      o.frequency.exponentialRampToValueAtTime(26, t + 1.6);
      const g = gain(0, sfx);
      g.connect(reverbSend);
      o.connect(g);
      g.gain.setValueAtTime(0.0001, t);
      g.gain.linearRampToValueAtTime(1.0, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0005, t + 3.2);
      o.start(t); o.stop(t + 3.3);
      const n = ctx.createBufferSource();
      n.buffer = noiseBuf;
      const lp = filter('lowpass', 900, 0.5);
      lp.frequency.setValueAtTime(1800, t);
      lp.frequency.exponentialRampToValueAtTime(120, t + 2);
      const ng = gain(0, sfx);
      n.connect(lp); lp.connect(ng);
      ng.gain.setValueAtTime(0.0001, t);
      ng.gain.linearRampToValueAtTime(0.7, t + 0.03);
      ng.gain.exponentialRampToValueAtTime(0.0005, t + 2.5);
      n.start(t, 0, 2.6);
    },
    // A single low resonant tone for the emblem.
    tone(freq = 110, dur = 5, vol = 0.12) {
      api.bell(freq, vol, dur);
    },
  };
  return api;
}
