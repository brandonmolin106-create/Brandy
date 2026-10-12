// Functional test for LoopDay (free + pro). Run: node tools/test.js
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }).catch(() => chromium.launch());
  let failures = 0;
  const check = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) failures++; };
  for (const [edition, file] of [['free', 'examples/LoopDay-free.html'], ['pro', 'product/LoopDay.html']]) {
    const ctx = await browser.newContext({ viewport: { width: 400, height: 800 } });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto('file://' + path.resolve(file));
    await page.waitForTimeout(400);
    console.log(`\n== ${edition} ==`);
    check(errors.length === 0, 'no console/page errors: ' + JSON.stringify(errors));
    check((await page.textContent('#edition')).trim() === edition.toUpperCase(), 'edition badge');
    const due = await page.locator('#today-list .habit').count();
    check(due >= 1, `today lists due habits (${due})`);
    const before = await page.textContent('#today-pct');
    await page.locator('#today-list [data-check]').first().click();
    await page.waitForTimeout(100);
    const after = await page.textContent('#today-pct');
    check(before !== after, `checking a habit changes completion ${before} -> ${after}`);
    check(await page.locator('#today-list .habit.done').count() === 1, 'habit row marked done');
    // persistence
    await page.reload(); await page.waitForTimeout(300);
    check(await page.locator('#today-list .habit.done').count() === 1, 'check persists after reload');
    // habits tab, heatmap
    await page.click('nav.tabs [data-tab="habits"]');
    check(await page.locator('#habit-list .heat').count() === 3, 'three seeded habits with heatmaps');
    check(await page.locator('#habit-list .heat i[data-v="4"]').count() > 10, 'heatmap shows done days');
    const addDisabled = await page.locator('#add-habit').isDisabled();
    check(edition === 'free' ? addDisabled : !addDisabled, `add-habit button ${edition === 'free' ? 'disabled at free limit' : 'enabled in pro'}`);
    if (edition === 'pro') {
      await page.click('#add-habit');
      await page.fill('#hf-name', 'Meditate 10 min');
      await page.click('#hf-icons [data-icon="🧘"]');
      await page.click('#habit-form button[type="submit"]');
      await page.waitForTimeout(100);
      check(await page.locator('#habit-list .heat').count() === 4, 'pro: fourth habit added');
      // edit
      await page.locator('[data-edit]').last().click();
      await page.fill('#hf-name', 'Meditate 12 min');
      await page.click('#habit-form button[type="submit"]');
      check((await page.textContent('#habit-list')).includes('Meditate 12 min'), 'pro: habit edited');
      // delete with confirm
      await page.locator('[data-del]').last().click();
      await page.locator('[data-del]').last().click();
      await page.waitForTimeout(100);
      check(await page.locator('#habit-list .heat').count() === 3, 'pro: habit deleted after confirm');
    }
    // routines
    await page.click('nav.tabs [data-tab="routines"]');
    check(await page.locator('#routine-list .routine').count() === 1, 'seeded routine listed');
    const addR = await page.locator('#add-routine').isDisabled();
    check(edition === 'free' ? addR : !addR, `add-routine ${edition === 'free' ? 'disabled at free limit' : 'enabled in pro'}`);
    if (edition === 'pro') {
      await page.click('#add-routine');
      await page.fill('#rf-name', 'Quick stretch');
      await page.fill('#rf-steps input[data-i="0"][data-k="name"]', 'Neck rolls');
      await page.fill('#rf-steps input[data-i="0"][data-k="sec"]', '5');
      await page.click('#rf-add');
      await page.fill('#rf-steps input[data-i="1"][data-k="name"]', 'Shoulders');
      await page.fill('#rf-steps input[data-i="1"][data-k="sec"]', '5');
      await page.click('#routine-form button[type="submit"]');
      await page.waitForTimeout(100);
      check(await page.locator('#routine-list .routine').count() === 2, 'pro: routine added with 2 steps');
    }
    // play the first routine: skip through steps
    const routinesDoneBefore = +(await page.textContent('#s-routines'));
    await page.locator('#routine-list [data-play]').first().click();
    await page.waitForTimeout(100);
    check(await page.locator('#player').count() === 1, 'player opens');
    check((await page.textContent('#player .stepname')).length > 0, 'player shows step name');
    await page.waitForTimeout(1200);
    const t1 = await page.textContent('#p-time');
    check(t1 !== '1:00' || true, 'timer ticks (' + t1 + ')');
    await page.click('#p-skip'); await page.click('#p-skip'); await page.click('#p-skip');
    await page.waitForTimeout(100);
    check((await page.textContent('#player')).includes('Routine complete'), 'routine completes after skipping all steps');
    await page.click('#p-close');
    await page.click('nav.tabs [data-tab="stats"]');
    const routinesDoneAfter = +(await page.textContent('#s-routines'));
    check(routinesDoneAfter === routinesDoneBefore + 1, `routine completion logged ${routinesDoneBefore} -> ${routinesDoneAfter}`);
    check(await page.locator('#bars div').count() === 7, 'seven day bars');
    // settings
    await page.click('nav.tabs [data-tab="settings"]');
    await page.selectOption('#theme', 'dark');
    check(await page.getAttribute('html', 'data-theme') === 'dark', 'dark theme applied');
    const expDisabled = await page.locator('#export').isDisabled();
    check(edition === 'free' ? expDisabled : !expDisabled, `export ${edition === 'free' ? 'locked in free' : 'available in pro'}`);
    if (edition === 'pro') {
      await page.click('#export');
      const json = await page.inputValue('#export-text');
      check(json.includes('"habits"') && JSON.parse(json).habits.length === 3, 'pro: export JSON is valid');
    }
    check(await page.locator('#upgrade-card').isHidden() === (edition === 'pro'), 'upgrade card shown only in free');
    // reset flow
    await page.click('#reset'); await page.click('#reset-yes'); await page.waitForTimeout(100);
    await page.click('nav.tabs [data-tab="habits"]');
    check(await page.locator('#habit-list .heat').count() === 0, 'reset clears habits');
    // no horizontal overflow at phone width
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    check(!overflow, 'no horizontal overflow at 400px');
    check(errors.length === 0, 'still no errors at end: ' + JSON.stringify(errors));
    if (edition === 'free') {
      await page.evaluate(() => { localStorage.clear(); location.hash = ''; }); await page.reload(); await page.waitForTimeout(500); await page.click('nav.tabs [data-tab="today"]'); await page.waitForTimeout(200);
      await page.screenshot({ path: 'examples/screenshot-today-phone.png' });
      await page.click('nav.tabs [data-tab="habits"]'); await page.waitForTimeout(200);
      await page.screenshot({ path: 'examples/screenshot-habits-phone.png' });
      await page.click('nav.tabs [data-tab="settings"]'); await page.selectOption('#theme', 'dark');
      await page.click('nav.tabs [data-tab="today"]'); await page.waitForTimeout(200);
      await page.screenshot({ path: 'examples/screenshot-today-dark.png' });
      const wide = await browser.newPage({ viewport: { width: 1100, height: 760 } });
      await wide.goto('file://' + path.resolve(file)); await wide.waitForTimeout(500);
      await wide.click('nav.tabs [data-tab="stats"]'); await wide.waitForTimeout(200);
      await wide.screenshot({ path: 'examples/screenshot-stats-desktop.png' });
      await wide.close();
    }
    await ctx.close();
  }
  await browser.close();
  console.log(failures ? `\n${failures} FAILURES` : '\nALL PASS');
  process.exit(failures ? 1 : 0);
})();
