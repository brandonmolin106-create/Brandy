// The Echoes in the Dark leaf — a pointed leaf in a diamond, split by a straight
// centre channel, filled with mirrored flowing veins that curve outward and upward,
// its two sides rising to an open point that holds one small golden four-pointed star.
// Vector redraw so it can draw itself, light up vein by vein, and texture the cauldron.
// Coordinates: 300 x 340 box, origin at the centre, y down (SVG convention).

const TIP_Y = -170, BOT_Y = 170, HALF_W = 147;

// Left half outline: from the top tip, down the upper edge, round the shoulder, to the base.
function outlineLeft() {
  return `M -5 ${TIP_Y} C -32 -138 -84 -94 -126 -50 C -151 -24 -151 24 -126 50 C -84 94 -34 138 -4 ${BOT_Y}`;
}
// Inner edge of the left half: straight up the centre, bowing out around the star.
function stemLeft() {
  return `M -4 ${BOT_Y - 2} L -7 -84 C -8 -104 -21 -112 -21 -126 C -21 -144 -11 -158 -5 ${TIP_Y}`;
}

// Veins: nested currents. Each rises from the centre channel, runs out along the lower
// edge, turns up along the upper edge and curls back toward the star at its end.
function veinLeft(k, n) {
  const f = (k + 1) / (n + 1);                // 0..1 from outer to inner
  const inset = 15 + f * 112;                 // distance in from the outline
  const y0 = BOT_Y - 20 - f * 176;            // where it leaves the channel
  const sx = -HALF_W + inset;                 // x of its outermost reach
  const shoulderY = -4 - f * 30;
  const topY = -132 + f * 70;                 // where it curls
  const curlX = -13 - (1 - f) * 30;
  const c1x = -8 + (sx + 8) * 0.3, c1y = y0 - 34 - (1 - f) * 20;
  return [
    `M -8 ${y0.toFixed(1)}`,
    `C ${c1x.toFixed(1)} ${c1y.toFixed(1)} ${(sx + 2).toFixed(1)} ${(shoulderY + 34).toFixed(1)} ${sx.toFixed(1)} ${shoulderY.toFixed(1)}`,
    `C ${(sx - 2).toFixed(1)} ${(shoulderY - 38).toFixed(1)} ${(curlX - 26 + f * 10).toFixed(1)} ${(topY - 4).toFixed(1)} ${curlX.toFixed(1)} ${topY.toFixed(1)}`,
    `C ${(curlX + 6).toFixed(1)} ${(topY + 3).toFixed(1)} ${(curlX + 5).toFixed(1)} ${(topY + 12).toFixed(1)} ${(curlX - 2).toFixed(1)} ${(topY + 13).toFixed(1)}`,
  ].join(' ');
}

export const VEINS_PER_SIDE = 5;

// Parts in drawing order: channel first, then veins outward in mirrored pairs, then the outline.
export function emblemParts() {
  const mirror = (d) => `<g transform="scale(-1,1)"><path d="${d}"/></g>`;
  const parts = [];
  parts.push({ id: 'channel', left: stemLeft() });
  for (let k = VEINS_PER_SIDE - 1; k >= 0; k--) parts.push({ id: `vein${k}`, left: veinLeft(k, VEINS_PER_SIDE) });
  parts.push({ id: 'outline', left: outlineLeft() });
  return parts.map((p, i) => ({ ...p, svg: `<path pathLength="1" style="animation-delay:${(i * 0.32).toFixed(2)}s" d="${p.left}"/>${mirror(p.left).replace('<path ', `<path pathLength="1" style="animation-delay:${(i * 0.32).toFixed(2)}s" `)}` }));
}

// Four-pointed star path centred at (cx, cy).
export function starPath(cx = 0, cy = -126, r = 13, inner = 3.2) {
  const pts = [];
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2 - Math.PI / 2;
    const rr = i % 2 === 0 ? r : inner;
    pts.push(`${(cx + Math.cos(a) * rr).toFixed(2)} ${(cy + Math.sin(a) * rr).toFixed(2)}`);
  }
  return `M ${pts.join(' L ')} Z`;
}

// Standalone SVG markup. colour = line colour; lit = number of parts shown in gold.
export function emblemSVG({ color = '#e9e6f4', gold = '#e8b85c', stroke = 7.5, lit = 0, starOn = true, id = 'emblem', drawn = true } = {}) {
  const parts = emblemParts();
  const body = parts.map((p, i) => {
    const c = i < lit ? gold : color;
    return `<g class="part part-${p.id}${i < lit ? ' lit' : ''}" data-part="${p.id}" stroke="${c}">${p.svg}</g>`;
  }).join('');
  return `<svg id="${id}" class="emblem${drawn ? '' : ' undrawn'}" viewBox="-175 -190 350 380" role="img" aria-label="Echoes in the Dark leaf emblem">
    <g fill="none" stroke-width="${stroke}" stroke-linecap="round" stroke-linejoin="round">${body}</g>
    <path class="emblem-star${starOn ? ' on' : ''}" d="${starPath()}" fill="${gold}"/>
  </svg>`;
}

// Draw the emblem into a 2D canvas (for textures: the cauldron channels, the platform floor).
export function drawEmblem(ctx, size, { color = '#fff', stroke = 9, star = true, starColor = '#fff' } = {}) {
  ctx.save();
  const s = size / 380;
  ctx.translate(size / 2, size / 2);
  ctx.scale(s, s);
  ctx.strokeStyle = color;
  ctx.lineWidth = stroke;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  for (const p of emblemParts()) {
    const path = new Path2D(p.left);
    ctx.stroke(path);
    ctx.save();
    ctx.scale(-1, 1);
    ctx.stroke(path);
    ctx.restore();
  }
  if (star) {
    ctx.fillStyle = starColor;
    ctx.fill(new Path2D(starPath()));
  }
  ctx.restore();
}

// Sample points along every part (for sparks gathering into the emblem, base upward).
export function samplePoints(step = 6) {
  if (typeof document === 'undefined') return [];
  const svgNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNS, 'svg');
  svg.style.position = 'absolute';
  svg.style.width = svg.style.height = '0';
  document.body.appendChild(svg);
  const pts = [];
  for (const p of emblemParts()) {
    const el = document.createElementNS(svgNS, 'path');
    el.setAttribute('d', p.left);
    svg.appendChild(el);
    const len = el.getTotalLength();
    for (let d = 0; d <= len; d += step) {
      const q = el.getPointAtLength(d);
      pts.push({ x: q.x, y: q.y, part: p.id }, { x: -q.x, y: q.y, part: p.id });
    }
  }
  svg.remove();
  return pts;
}
