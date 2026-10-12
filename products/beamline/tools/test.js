const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  let fails = 0; const check = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
  async function open(file, vw) { const ctx = await browser.newContext({ viewport: vw || { width: 420, height: 820 } }); const page = await ctx.newPage(); const errs = []; page.on('pageerror', e => errs.push(e.message)); page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); }); await page.goto('file://' + path.resolve(file)); await page.waitForTimeout(400); return { ctx, page, errs }; }
  async function solve(page) { // click the solution cells: once for '/', twice for '\'
    return page.evaluate(async () => {
      const B = window.Beamline, L = B.level, cv = document.getElementById('c'); const r = cv.getBoundingClientRect(); const px = parseFloat(cv.style.width), pad = 18, cs = (px - pad * 2) / L.size;
      for (const [k, m] of Object.entries(L.solution)) { const x = +k % L.size, y = Math.floor(+k / L.size); const cx = r.left + pad + (x + 0.5) * cs, cy = r.top + pad + (y + 0.5) * cs; for (let i = 0; i < m; i++) { cv.dispatchEvent(new MouseEvent('click', { clientX: cx, clientY: cy, bubbles: true })); } }
      return Object.keys(B.mirrors).length;
    });
  }
  // --- level integrity, all 40 ---
  { const { page, ctx } = await open('build/free/index.html');
    const report = await page.evaluate(() => { const B = window.Beamline; const out = []; for (let n = 1; n <= B.TOTAL; n++) { const L = B.makeLevel(n); if (!L) { out.push({ n, ok: false, why: 'null' }); continue; } const crystals = L.cells.flat().filter(v => v === 2).length; const s = B.trace(L, L.solution); const z = B.trace(L, {}); out.push({ n, ok: s.hitTarget && s.lit.size === crystals && !(z.hitTarget && z.lit.size === crystals), size: L.size, par: L.par, crystals, mirrors: Object.keys(L.solution).length }); } return out; });
    const bad = report.filter(r => !r.ok); check(bad.length === 0, `all 40 levels generate, solvable by solution, not by zero mirrors (${bad.map(b => b.n).join(',') || 'none bad'})`);
    const parsUsed = report.filter(r => r.ok && r.mirrors === r.par).length; check(parsUsed === 40, 'solution uses exactly par mirrors on every level');
    console.log('curve: ' + report.filter(r => [1, 5, 10, 20, 30, 40].includes(r.n)).map(r => `L${r.n} ${r.size}x${r.size} par${r.par} c${r.crystals}`).join(' | '));
    const determ = await page.evaluate(() => JSON.stringify(window.Beamline.makeLevel(17)) === JSON.stringify(window.Beamline.makeLevel(17))); check(determ, 'levels are deterministic');
    await ctx.close(); }
  // --- free edition play-through ---
  { const { page, ctx, errs } = await open('build/free/index.html');
    check(errs.length === 0, 'free: no errors on load ' + JSON.stringify(errs));
    check((await page.textContent('#h-level')) === '1', 'free: starts on level 1');
    for (let n = 1; n <= 3; n++) { const used = await solve(page); await page.waitForTimeout(500); check(!(await page.locator('#ov-win').isHidden()), `free: level ${n} won by clicking the solution (${used} mirrors)`); const stars = await page.textContent('#win-stars'); check(stars === '★★★', `free: 3 stars at par (${stars})`); await page.click('#win-next'); await page.waitForTimeout(100); }
    check((await page.textContent('#h-level')) === '4', 'free: advanced to level 4');
    await page.reload(); await page.waitForTimeout(300); check((await page.textContent('#h-level')) === '4' && (await page.textContent('#h-stars')) === '9', 'free: progress persists (level 4, 9 stars)');
    // undo + reset
    await page.evaluate(() => { const cv = document.getElementById('c'); const r = cv.getBoundingClientRect(); cv.dispatchEvent(new MouseEvent('click', { clientX: r.left + 40, clientY: r.top + 40, bubbles: true })); });
    const m1 = await page.evaluate(() => Object.keys(window.Beamline.mirrors).length); await page.click('#b-undo'); const m2 = await page.evaluate(() => Object.keys(window.Beamline.mirrors).length); check(m1 === 1 && m2 === 0, 'undo removes the last mirror');
    // mirror budget enforced
    const over = await page.evaluate(() => { const B = window.Beamline, L = B.level, cv = document.getElementById('c'); const r = cv.getBoundingClientRect(); const px = parseFloat(cv.style.width), pad = 18, cs = (px - pad * 2) / L.size; let clicks = 0; for (let y = 0; y < L.size && clicks < L.par + 3; y++) for (let x = 0; x < L.size && clicks < L.par + 3; x++) { if (L.cells[y][x] !== 0) continue; cv.dispatchEvent(new MouseEvent('click', { clientX: r.left + pad + (x + 0.5) * cs, clientY: r.top + pad + (y + 0.5) * cs, bubbles: true })); clicks++; } return Object.keys(B.mirrors).length <= L.par; }); check(over, 'cannot place more mirrors than par');
    await page.click('#b-reset'); check(await page.evaluate(() => Object.keys(window.Beamline.mirrors).length) === 0, 'reset clears the board');
    // jump to 20, clear it, hit the wall
    await page.evaluate(() => { const s = JSON.parse(localStorage.getItem('beamline.v1')); for (let n = 1; n <= 19; n++) s.stars[n] = 3; s.level = 20; localStorage.setItem('beamline.v1', JSON.stringify(s)); }); await page.reload(); await page.waitForTimeout(300);
    check((await page.textContent('#h-level')) === '20', 'free: on level 20'); await solve(page); await page.waitForTimeout(500); await page.click('#win-next'); await page.waitForTimeout(100);
    check(!(await page.locator('#ov-wall').isHidden()), 'free: paywall shows after level 20');
    check((await page.getAttribute('#buy', 'href')).includes('gumroad.com/l/beamline'), 'free: buy button links to Gumroad');
    await page.click('#wall-close'); check(!(await page.locator('#ov-levels').isHidden()), 'free: level select opens from the wall');
    check((await page.locator('#lv-grid button').count()) === 40, 'level grid shows 40');
    await page.click('#lv-close'); await page.click('#b-levels'); await page.click('#lv-zen'); check(!(await page.locator('#ov-wall').isHidden()), 'free: zen is gated behind the full edition');
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth); check(!overflow, 'no horizontal overflow at 420px');
    check(errs.length === 0, 'free: no errors at end ' + JSON.stringify(errs));
    await page.click('#wall-close'); await page.click('#lv-close'); await page.evaluate(() => localStorage.clear()); await page.reload(); await page.waitForTimeout(400); await solve(page); await page.waitForTimeout(100);
    await page.screenshot({ path: 'examples/screenshot-level1-solved.png' });
    await page.evaluate(() => { const s = JSON.parse(localStorage.getItem('beamline.v1')); s.level = 12; localStorage.setItem('beamline.v1', JSON.stringify(s)); }); await page.reload(); await page.waitForTimeout(400); await page.screenshot({ path: 'examples/screenshot-level12.png' });
    const wide = await browser.newPage({ viewport: { width: 1100, height: 760 } }); await wide.goto('file://' + path.resolve('build/free/index.html')); await wide.waitForTimeout(400); await wide.evaluate(() => { const s = JSON.parse(localStorage.getItem('beamline.v1') || '{"stars":{},"sound":true}'); s.level = 18; localStorage.setItem('beamline.v1', JSON.stringify(s)); }); await wide.reload(); await wide.waitForTimeout(400); await wide.screenshot({ path: 'examples/screenshot-level18-desktop.png' }); await wide.close();
    await ctx.close(); }
  // --- full edition ---
  { const { page, ctx, errs } = await open('product/index.html');
    await page.evaluate(() => { const s = { stars: {}, sound: true, level: 21 }; for (let n = 1; n <= 20; n++) s.stars[n] = 3; localStorage.setItem('beamline.v1', JSON.stringify(s)); }); await page.reload(); await page.waitForTimeout(300);
    check((await page.textContent('#h-level')) === '21', 'full: level 21 playable');
    await solve(page); await page.waitForTimeout(500); check(!(await page.locator('#ov-win').isHidden()), 'full: level 21 won');
    await page.click('#win-next'); await page.evaluate(() => { const s = JSON.parse(localStorage.getItem('beamline.v1')); for (let n = 1; n <= 39; n++) s.stars[n] = 3; s.level = 40; localStorage.setItem('beamline.v1', JSON.stringify(s)); }); await page.reload(); await page.waitForTimeout(300);
    await solve(page); await page.waitForTimeout(500); await page.click('#win-next'); await page.waitForTimeout(100); check(!(await page.locator('#ov-done').isHidden()), 'full: completion screen after level 40');
    await page.click('#done-zen'); await page.waitForTimeout(200); check((await page.textContent('#h-level')) === 'ZEN', 'full: zen mode starts');
    await solve(page); await page.waitForTimeout(500); check(!(await page.locator('#ov-win').isHidden()), 'full: zen puzzle solvable');
    check(errs.length === 0, 'full: no errors ' + JSON.stringify(errs));
    await ctx.close(); }
  await browser.close(); console.log(fails ? `\n${fails} FAILURES` : '\nALL PASS'); process.exit(fails ? 1 : 0);
})();
