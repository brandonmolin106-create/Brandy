// Screens and overlays: title, subtitles, prompts, chapter cards, the HUD leaf that
// fills with gold as echoes are gathered, pause, the ending and its gathering sparks.
import { emblemSVG, emblemParts, samplePoints, starPath } from './emblem.js';

const $ = (id) => document.getElementById(id);
const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'];

export function createUI() {
  const isTouch = matchMedia('(pointer: coarse)').matches;
  if (isTouch) document.body.classList.add('touch');

  $('load-emblem').innerHTML = emblemSVG({ id: 'load-svg', color: '#8f88c8', stroke: 8, starOn: true });
  $('load-svg').style.width = '74px';

  // HUD leaf: a dim base and a gold layer drawn along each part as echoes are gathered.
  const parts = emblemParts();
  const goldPaths = parts.map((p) => `<path pathLength="1" d="${p.left}"/><path pathLength="1" transform="scale(-1,1)" d="${p.left}"/>`);
  $('hud-emblem').innerHTML = `<svg class="emblem" viewBox="-175 -190 350 380" aria-hidden="true">
      <g fill="none" stroke="#5c5a7e" stroke-width="10" stroke-linecap="round">${parts.map((p) => p.svg).join('')}</g>
      <g class="gold-layer" fill="none" stroke="#edc36c" stroke-width="11" stroke-linecap="round">${goldPaths.map((g, i) => `<g data-i="${i}">${g}</g>`).join('')}</g>
      <path class="emblem-star" id="hud-star" d="${starPath()}" fill="#edc36c"/>
    </svg>`;
  const goldGroups = [...document.querySelectorAll('#hud-emblem .gold-layer > g')];

  const helpDesktop = 'Walk <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> · Look: mouse · Act <kbd>E</kbd> · Hold <kbd>Q</kbd> or right mouse to listen · <kbd>Shift</kbd> hurry · <kbd>Esc</kbd> pause · Gamepad works too';
  const helpTouch = 'Left thumb walks · right thumb looks · hold LISTEN to hear the echoes · ACT to gather, rise and sit';
  $('controls-help').innerHTML = isTouch ? helpTouch : helpDesktop;
  $('pause-help').innerHTML = isTouch ? helpTouch : helpDesktop;

  let subTimer = null, chapterTimer = null, hintTimer = null;
  // The official logo artwork, if one has been dropped into assets/brand/logo.png.
  let hasLogo = false;
  let logoFile = 'assets/brand/logo.png';
  fetch('assets/brand/brand.json').then((r) => (r.ok ? r.json() : {})).then((b) => {
    if (b && b.logo) { hasLogo = true; logoFile = 'assets/brand/' + b.logo; }
  }).catch(() => {});
  const revealLogo = (container, svg) => {
    if (!hasLogo || container.querySelector('.real-logo')) return;
    const img = new Image();
    img.className = 'real-logo';
    img.alt = 'Echoes in the Dark';
    img.onload = () => {
      container.appendChild(img);
      requestAnimationFrame(() => { img.style.opacity = '1'; if (svg) svg.style.opacity = '0'; });
    };
    img.src = logoFile;
  };
  const ui = {
    isTouch,
    title: {
      show({ heard = 0, total = 9, loops = 0 } = {}) {
        $('title').hidden = false;
        $('title').classList.remove('gone');
        $('title-emblem').innerHTML = emblemSVG({ id: 'title-svg', color: '#e9e6f4', stroke: 7.5, starOn: false, drawn: false });
        const svg = $('title-svg');
        svg.classList.add('draw');
        setTimeout(() => svg.querySelector('.emblem-star')?.classList.add('on'), 2600);
        setTimeout(() => revealLogo($('title-emblem'), svg), 4200);
        const st = $('title-stat');
        if (heard > 0 || loops > 0) {
          st.hidden = false;
          st.textContent = `Echoes heard: ${heard} of ${total}${loops ? ` · Journeys walked: ${loops}` : ''}`;
        } else st.hidden = true;
        setTimeout(() => $('btn-begin').focus({ preventScroll: true }), 50);
      },
      hide() {
        $('title').classList.add('gone');
        setTimeout(() => { $('title').hidden = true; }, 1700);
      },
    },
    subtitle: {
      show(text, kind = 'story') {
        const el = $('subtitle');
        clearTimeout(subTimer);
        el.classList.toggle('echo', kind === 'echo');
        el.textContent = text;
        el.classList.add('show');
      },
      hide() {
        $('subtitle').classList.remove('show');
      },
    },
    prompt(label, key = 'E') {
      const el = $('prompt');
      if (!label) { el.classList.remove('show'); return; }
      el.querySelector('.key').textContent = isTouch ? 'ACT' : key;
      el.querySelector('.label').textContent = label;
      el.classList.add('show');
    },
    chapter(i, name) {
      const el = $('chapter');
      el.querySelector('.num').textContent = ROMAN[i] || '';
      el.querySelector('.name').textContent = name;
      el.classList.add('show');
      clearTimeout(chapterTimer);
      chapterTimer = setTimeout(() => el.classList.remove('show'), 5200);
    },
    hint(text, seconds = 7) {
      const el = $('hint');
      clearTimeout(hintTimer);
      if (!text) { el.classList.remove('show'); return; }
      el.textContent = text;
      el.classList.add('show');
      hintTimer = setTimeout(() => el.classList.remove('show'), seconds * 1000);
    },
    // Fill the HUD leaf: `count` of `total` echoes spread over every part of the emblem.
    setEchoes(count, total = 9, starOn = false) {
      $('hud').classList.toggle('show', count > 0 || starOn);
      $('hud-count').textContent = `${count} / ${total}`;
      const F = (count / total) * goldGroups.length;
      goldGroups.forEach((g, i) => {
        const amt = Math.max(0, Math.min(1, F - i));
        g.querySelectorAll('path').forEach((p) => { p.style.strokeDashoffset = String(1 - amt); });
      });
      $('hud-star').classList.toggle('on', starOn);
    },
    showHUD(on) { $('hud').classList.toggle('show', on); },
    pause: {
      show() { $('pause').hidden = false; setTimeout(() => $('btn-resume').focus({ preventScroll: true }), 30); },
      hide() { $('pause').hidden = true; },
      get open() { return !$('pause').hidden; },
    },
    ending: {
      show({ heard, total, closing }) {
        const el = $('ending');
        el.hidden = false;
        requestAnimationFrame(() => el.classList.add('show'));
        $('ending-emblem').innerHTML = emblemSVG({ id: 'end-svg', color: '#ece8f6', stroke: 7, starOn: false, drawn: false });
        const svg = $('end-svg');
        svg.style.opacity = '0';
        document.querySelectorAll('#ending .fadein').forEach((n) => n.classList.remove('on'));
        $('end-stat').textContent = `Echoes heard: ${heard} of ${total}`;
        $('end-closing').textContent = closing;
        runSparks(svg, () => {
          svg.style.transition = 'opacity 1.4s ease';
          svg.style.opacity = '1';
          setTimeout(() => svg.querySelector('.emblem-star').classList.add('on'), 900);
          setTimeout(() => revealLogo($('ending-emblem'), svg), 2600);
          const seq = ['end-title', 'end-credit', 'end-studio', 'end-stat', 'end-closing', 'end-actions'];
          seq.forEach((id, i) => setTimeout(() => $(id).classList.add('on'), 1800 + i * 1300));
        });
      },
      hide() {
        const el = $('ending');
        el.classList.remove('show');
        setTimeout(() => { el.hidden = true; }, 2300);
      },
    },
    loaded() { document.body.classList.add('loaded'); },
    error(msg) {
      const el = $('load-error');
      el.hidden = false;
      el.textContent = msg;
    },
    progress(f) { $('load-bar').style.transform = `scaleX(${Math.min(1, f)})`; },
  };

  // Golden sparks drift in from every edge and gather into the leaf, from the base upward.
  function runSparks(svg, done) {
    const canvas = $('sparks');
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = innerWidth * dpr;
    canvas.height = innerHeight * dpr;
    const g = canvas.getContext('2d');
    const rect = svg.getBoundingClientRect();
    const scale = rect.width / 350;
    const cx = rect.left + rect.width / 2, cy = rect.top + rect.height / 2;
    const pts = samplePoints(7);
    const maxY = 190;
    const sparks = pts.map((p) => {
      const edge = Math.floor(Math.random() * 4);
      const sx = edge === 0 ? -20 : edge === 1 ? innerWidth + 20 : Math.random() * innerWidth;
      const sy = edge === 2 ? -20 : edge === 3 ? innerHeight + 20 : Math.random() * innerHeight;
      return { sx, sy, tx: cx + p.x * scale, ty: cy + p.y * scale, delay: ((maxY - p.y) / 380) * 2.2 + Math.random() * 0.5 };
    });
    const t0 = performance.now();
    const frame = (now) => {
      const t = (now - t0) / 1000;
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      g.clearRect(0, 0, innerWidth, innerHeight);
      g.globalCompositeOperation = 'lighter';
      let settled = 0;
      for (const s of sparks) {
        const k = Math.max(0, Math.min(1, (t - s.delay) / 1.6));
        const e = 1 - Math.pow(1 - k, 3);
        const x = s.sx + (s.tx - s.sx) * e, y = s.sy + (s.ty - s.sy) * e;
        const fade = t > 4.4 ? Math.max(0, 1 - (t - 4.4) / 1.2) : 1;
        const a = (k > 0 ? 0.85 : 0) * fade;
        if (k >= 1) settled++;
        g.fillStyle = `rgba(255,${190 + Math.floor(40 * e)},${110 + Math.floor(60 * e)},${a})`;
        g.beginPath();
        g.arc(x, y, 1.6 + (1 - e) * 1.2, 0, Math.PI * 2);
        g.fill();
      }
      if (t < 5.8) requestAnimationFrame(frame);
      else g.clearRect(0, 0, innerWidth, innerHeight);
      if (t > 3.9 && !frameDone) { frameDone = true; done(); }
    };
    let frameDone = false;
    requestAnimationFrame(frame);
  }
  return ui;
}
