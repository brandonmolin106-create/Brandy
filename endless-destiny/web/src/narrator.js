// The narrator: reads every line out loud. Deep, warm, slow; every sentence falls at the end.
// Uses the browser's text-to-speech. Drop real recordings into assets/voice/ (see
// assets/voice/README.md) and they replace the synthetic voice line by line.
const PREFERRED = [
  /Daniel/i, /Google UK English Male/i, /Microsoft (Ryan|Guy|Thomas|George|Christopher|Andrew|Brian)/i,
  /Arthur/i, /Oliver/i, /Aaron/i, /Rishi/i, /Fred/i, /Alex/i, /Male/i,
];

export function createNarrator(subtitle) {
  const synth = window.speechSynthesis || null;
  let voice = null;
  let enabled = true;
  let recordings = {};
  let current = null;       // { cancel }
  let volume = 1;
  const queue = [];

  const pickVoice = () => {
    if (!synth) return;
    const voices = synth.getVoices().filter((v) => /^en(-|_|$)/i.test(v.lang));
    for (const re of PREFERRED) {
      const v = voices.find((x) => re.test(x.name));
      if (v) { voice = v; return; }
    }
    voice = voices.find((v) => /en-GB/i.test(v.lang)) || voices[0] || null;
  };
  if (synth) {
    pickVoice();
    synth.addEventListener?.('voiceschanged', pickVoice);
  }
  fetch('assets/voice/manifest.json').then((r) => (r.ok ? r.json() : {})).then((m) => { recordings = m || {}; }).catch(() => {});

  const wordsDuration = (text) => Math.max(2.2, text.split(/\s+/).length / 2.1 + 0.9);

  function playOne(item) {
    const { text, id } = item;
    subtitle.show(text, item.kind);
    let finished = false;
    const done = () => {
      if (finished) return;
      finished = true;
      current = null;
      setTimeout(() => {
        if (!current) subtitle.hide();
        next();
      }, item.hold ?? 700);
      item.onend?.();
    };
    // A real recording wins over the synthetic voice.
    if (enabled && id && recordings[id]) {
      const a = new Audio('assets/voice/' + recordings[id]);
      a.volume = volume;
      a.onended = done;
      a.onerror = () => setTimeout(done, wordsDuration(text) * 1000);
      a.play().catch(() => setTimeout(done, wordsDuration(text) * 1000));
      current = { cancel() { a.pause(); done(); } };
      return;
    }
    if (enabled && synth) {
      const u = new SpeechSynthesisUtterance(text);
      if (voice) u.voice = voice;
      u.lang = voice?.lang || 'en-GB';
      u.rate = 0.84;
      u.pitch = 0.72;
      u.volume = volume;
      u.onend = done;
      u.onerror = done;
      // Some browsers never fire onend; never leave a line stuck on screen.
      const guard = setTimeout(done, (wordsDuration(text) * 1.8 + 2) * 1000);
      u.onend = () => { clearTimeout(guard); done(); };
      synth.speak(u);
      current = { cancel() { clearTimeout(guard); synth.cancel(); done(); } };
      return;
    }
    const tmr = setTimeout(done, wordsDuration(text) * 1000);
    current = { cancel() { clearTimeout(tmr); done(); } };
  }
  function next() {
    if (current || !queue.length) return;
    playOne(queue.shift());
  }

  return {
    get speaking() { return !!current || queue.length > 0; },
    get enabled() { return enabled; },
    setEnabled(v) { enabled = v; if (!v && synth) synth.cancel(); },
    setVolume(v) { volume = v; },
    // kind: 'story' lines interrupt; 'echo' questions queue behind.
    say(text, { id = null, kind = 'story', onend = null, hold } = {}) {
      if (kind === 'story') {
        queue.length = 0;
        current?.cancel();
      }
      queue.push({ text, id, kind, onend, hold });
      next();
    },
    sayAll(lines, opts = {}) {
      lines.forEach((text, i) => this.say(text, { ...opts, id: opts.id ? `${opts.id}-${i + 1}` : null, kind: i === 0 ? opts.kind || 'story' : 'echo', onend: i === lines.length - 1 ? opts.onend : null }));
    },
    stop() { queue.length = 0; current?.cancel(); if (synth) synth.cancel(); subtitle.hide(); },
    // Browsers only allow speech after a tap or key press: call this from the Begin button.
    unlock() {
      if (!synth) return;
      try {
        const u = new SpeechSynthesisUtterance(' ');
        u.volume = 0;
        synth.speak(u);
      } catch { /* speech unavailable */ }
      pickVoice();
    },
  };
}
