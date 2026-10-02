/* =====================================================================
   BRANDON MOLINA — TikTok site app
   Reads window.SITE (videos.js) and renders everything.
   ===================================================================== */
(function () {
  "use strict";
  const S = window.SITE || { profile: {}, categories: [], videos: [] };
  const P = S.profile || {};
  const CATS = S.categories || [];
  const VBASE = P.videoBase || "videos/", CBASE = P.coverBase || "covers/";
  const VIDEOS = (S.videos || []).map((v, i) => ({
    _i: i, id: v.id, title: v.t || "Untitled", category: v.c, date: v.d || "", dur: v.s || 0,
    views: v.v || 0, likes: v.l || 0, music: v.m || "", tags: v.g || [], pinned: !!v.p, photo: !!v.ph, slide: !!v.sl,
    src: VBASE + v.id + ".mp4", poster: CBASE + v.id + ".jpg",
    url: `https://www.tiktok.com/@${P.handle}/video/${v.id}`
  }));
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const catById = Object.fromEntries(CATS.map(c => [c.id, c]));
  const handle = (P.handle || "").replace(/^@/, "");
  const tiktokUrl = (P.links && P.links.tiktok) || (handle ? `https://www.tiktok.com/@${handle}` : "https://www.tiktok.com/");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const touch = matchMedia("(hover: none)").matches;
  const PAGE = 24;

  /* ---------- helpers ---------- */
  const fmt = n => { n = Number(n) || 0; if (n >= 1e9) return (n / 1e9).toFixed(1).replace(/\.0$/, "") + "B"; if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, "") + "M"; if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, "") + "K"; return String(n); };
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const mmss = s => { s = Math.max(0, Math.round(s || 0)); return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); };
  const niceDate = d => { if (!d) return ""; const t = new Date(d + "T00:00:00"); return isNaN(t) ? d : t.toLocaleDateString("en-AU", { day: "numeric", month: "short", year: "numeric" }); };
  const toast = (() => { let el, t; return msg => { if (!el) { el = document.createElement("div"); el.className = "toast"; document.body.appendChild(el); } el.textContent = msg; el.classList.add("show"); clearTimeout(t); t = setTimeout(() => el.classList.remove("show"), 2400); }; })();
  const splitText = el => { const txt = el.textContent; el.textContent = ""; let i = 0; for (const ch of txt) { const s = document.createElement("span"); s.className = "ch"; s.style.setProperty("--i", i++); s.textContent = ch === " " ? " " : ch; el.appendChild(s); } };

  /* ---------- profile ---------- */
  function mountProfile() {
    const name = P.name || "Brandon Molina";
    $("#hero-name").textContent = name; splitText($(".splash-name"));
    $("#hero-location").textContent = P.location || "";
    $("#hero-bio").textContent = P.bio || "";
    $("#footer-name").textContent = name;
    $("#year").textContent = new Date().getFullYear();
    const h = $("#hero-handle"); h.textContent = "@" + handle; h.href = tiktokUrl;
    $("#cta-handle").textContent = "@" + handle;
    ["#follow-top", "#follow-hero", "#follow-cta"].forEach(id => { $(id).href = tiktokUrl; });
    document.title = `${name} (@${handle}) — TikTok`;
    const st = P.stats || {};
    const totals = { followers: st.followers || 0, likes: st.likes || 0, videos: st.videos || VIDEOS.length, views: st.views || VIDEOS.reduce((a, v) => a + v.views, 0) };
    $$("[data-count]").forEach(el => { el.dataset.target = totals[el.dataset.count] || 0; el.textContent = "0"; });
    const L = P.links || {}, wrap = $("#socials");
    const icons = {
      instagram: `<svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M7 2h10a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5zm0 2a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3H7zm5 3.5a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9zm0 2a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM17.5 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/></svg>`,
      youtube: `<svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12 31 31 0 0 0 1 16.8a3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1c.4-1.6.5-3.2.5-4.8s-.1-3.2-.5-4.8zM9.8 15.1V8.9l6 3.1-6 3.1z"/></svg>`,
      email: `<svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm0 2v.5l8 5 8-5V6H4zm0 2.8V18h16V8.8l-8 5-8-5z"/></svg>`
    };
    Object.entries(icons).forEach(([k, svg]) => { if (!L[k]) return; const a = document.createElement("a"); a.href = k === "email" ? "mailto:" + L[k] : L[k]; if (k !== "email") { a.target = "_blank"; a.rel = "noopener"; } a.title = k; a.innerHTML = svg; wrap.appendChild(a); });
  }
  function countUp() {
    $$("[data-count]").forEach(el => {
      const target = Number(el.dataset.target) || 0, t0 = performance.now(), dur = 1800;
      const step = t => { const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 4); el.textContent = fmt(Math.round(target * e)); if (p < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    });
  }
  function typewriter() {
    const lines = [P.tagline || "you. the one reading this.", "You are amazing.", "Keep on going.", "Stay true to yourself.", "You got this, bro."];
    const el = $("#typer"); let li = 0, ci = 0, del = false;
    if (reduce) { el.textContent = lines[0]; return; }
    (function tick() {
      const line = lines[li];
      el.textContent = line.slice(0, ci);
      let wait = del ? 40 : 70;
      if (!del && ci === line.length) { wait = 1800; del = true; }
      else if (del && ci === 0) { del = false; li = (li + 1) % lines.length; wait = 300; }
      ci += del ? -1 : 1;
      setTimeout(tick, wait);
    })();
  }

  /* ---------- categories / ticker / highlights ---------- */
  const countFor = id => VIDEOS.filter(v => v.category === id).length;
  function mountCategories() {
    const nav = $("#topnav"), grid = $("#cat-grid"), chips = $("#chips"), ticker = $("#ticker");
    const allChip = document.createElement("button"); allChip.className = "chip active"; allChip.dataset.cat = "all"; allChip.textContent = `All · ${VIDEOS.length}`; chips.appendChild(allChip);
    const tick = [];
    CATS.forEach(c => {
      const n = countFor(c.id); if (!n) return;
      const a = document.createElement("a"); a.href = "#cat-" + c.id; a.textContent = c.emoji + " " + c.name; nav.appendChild(a);
      const card = document.createElement("a"); card.className = "cat-card reveal"; card.href = "#cat-" + c.id; card.style.setProperty("--c", c.color);
      const minis = VIDEOS.filter(v => v.category === c.id).slice(0, 3).map(v => `<img src="${v.poster}" alt="" loading="lazy">`).join("");
      card.innerHTML = `<div class="mini">${minis}</div><span class="emoji">${esc(c.emoji)}</span><h3>${esc(c.name)}</h3><p>${esc(c.blurb || "")}</p><span class="count">${n} video${n === 1 ? "" : "s"}</span>`;
      grid.appendChild(card);
      const chip = document.createElement("button"); chip.className = "chip"; chip.dataset.cat = c.id; chip.style.setProperty("--c", c.color); chip.textContent = `${c.emoji} ${c.name} · ${n}`; chips.appendChild(chip);
      tick.push(`<span style="--c:${c.color}">${c.emoji} <b>${esc(c.name)}</b> ${n}</span>`);
    });
    ticker.innerHTML = tick.join("") + tick.join("");
    const row = $("#highlight-row");
    [...VIDEOS].sort((a, b) => b.views - a.views).slice(0, 4).forEach((v, i) => {
      const c = catById[v.category] || {};
      const b = document.createElement("button"); b.className = "highlight reveal"; b.style.setProperty("--c", c.color || "#ffb020"); b.style.transitionDelay = i * 90 + "ms";
      b.innerHTML = `<img src="${v.poster}" alt="" loading="lazy"><div class="shade"></div><span class="rank">#${i + 1}</span><div class="meta"><div class="title">${esc(v.title)}</div><div class="views">▶ ${fmt(v.views)} views · ♥ ${fmt(v.likes)}</div></div>`;
      b.addEventListener("click", () => openModal(v._i)); row.appendChild(b);
    });
  }

  /* ---------- filtering ---------- */
  const state = { q: "", cat: "all", sort: "newest", shown: {} };
  let visible = [];
  function filtered() {
    const q = state.q.trim().toLowerCase();
    let list = VIDEOS.filter(v => (state.cat === "all" || v.category === state.cat) && (!q || v.title.toLowerCase().includes(q) || v.music.toLowerCase().includes(q) || v.tags.some(t => t.includes(q)) || (catById[v.category]?.name || "").toLowerCase().includes(q) || v.date.includes(q)));
    const byDate = (a, b) => b.date.localeCompare(a.date) || a._i - b._i;
    const sorts = { newest: byDate, oldest: (a, b) => -byDate(a, b), views: (a, b) => b.views - a.views, likes: (a, b) => b.likes - a.likes, longest: (a, b) => b.dur - a.dur, az: (a, b) => a.title.localeCompare(b.title) };
    list.sort(sorts[state.sort] || byDate);
    if (state.sort === "newest") list.sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0));
    return list;
  }

  function cardFor(v) {
    const c = catById[v.category] || {};
    const b = document.createElement("button"); b.className = "card"; b.type = "button"; b.dataset.index = v._i; b.style.setProperty("--c", c.color || "#fe2c55");
    b.setAttribute("aria-label", "Play: " + v.title);
    b.innerHTML = `<img class="poster" src="${v.poster}" alt="" loading="lazy" onload="this.classList.add('loaded')"><div class="shade"></div>
      ${v.pinned ? `<span class="badge">Top</span>` : ""}<span class="nowm">No watermark</span><span class="dur">${v.photo ? "📷 photo" : v.slide ? "📷 " + mmss(v.dur) : mmss(v.dur)}</span>
      <div class="play"></div><div class="meta"><div class="title">${esc(v.title)}</div><div class="sub"><span class="dot"></span><span>${esc(c.name || "")}</span><span>· ${esc(niceDate(v.date))}</span></div></div>
      <span class="views">${fmt(v.views)}</span>`;
    b.addEventListener("click", () => openModal(v._i));
    if (!touch && !reduce) {
      let vid, t;
      b.addEventListener("mouseenter", () => { t = setTimeout(() => { if (!vid) { vid = document.createElement("video"); vid.className = "preview"; vid.muted = true; vid.loop = true; vid.playsInline = true; vid.preload = "none"; vid.src = v.src; b.insertBefore(vid, b.querySelector(".shade")); } vid.currentTime = 0; vid.play().then(() => b.classList.add("previewing")).catch(() => {}); }, 350); });
      b.addEventListener("mouseleave", () => { clearTimeout(t); b.classList.remove("previewing"); if (vid) vid.pause(); });
      b.addEventListener("mousemove", e => { const r = b.getBoundingClientRect(); const x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5; b.style.transform = `translateY(-8px) scale(1.03) rotateY(${x * 10}deg) rotateX(${-y * 10}deg)`; });
      b.addEventListener("mouseleave", () => { b.style.transform = ""; });
    }
    return b;
  }

  function render(keepShown) {
    if (!keepShown) state.shown = {};
    visible = filtered();
    const root = $("#sections"); root.innerHTML = "";
    const cats = state.cat === "all" ? CATS : CATS.filter(c => c.id === state.cat);
    let shown = 0;
    cats.forEach(c => {
      const list = visible.filter(v => v.category === c.id); if (!list.length) return;
      shown += list.length;
      const lim = state.shown[c.id] || (state.cat === "all" ? PAGE / 2 : PAGE);
      const sec = document.createElement("section"); sec.className = "section cat-section"; sec.id = "cat-" + c.id; sec.style.setProperty("--c", c.color);
      sec.innerHTML = `<h2><span class="emoji">${esc(c.emoji)}</span>${esc(c.name)} <span class="pill">${list.length}</span></h2><p class="blurb">${esc(c.blurb || "")}</p><div class="grid"></div>`;
      const grid = sec.querySelector(".grid");
      list.slice(0, lim).forEach(v => grid.appendChild(cardFor(v)));
      if (list.length > lim) {
        const more = document.createElement("button"); more.className = "btn btn-ghost show-more"; more.textContent = `Show ${Math.min(PAGE, list.length - lim)} more of ${list.length - lim} ↓`;
        more.addEventListener("click", () => { state.shown[c.id] = lim + PAGE; const y = more.getBoundingClientRect().top + scrollY; render(true); scrollTo(0, y - 300); });
        sec.appendChild(more);
      }
      root.appendChild(sec);
    });
    $("#empty").hidden = shown > 0;
    $("#result-count").textContent = shown ? `${shown} video${shown === 1 ? "" : "s"}${state.q ? ` matching “${state.q}”` : ""}` : "";
    observe();
  }

  /* ---------- player ---------- */
  const video = $("#player"); let current = -1;
  function openModal(i) {
    const v = VIDEOS[i]; if (!v) return;
    current = i; const c = catById[v.category] || {};
    const ph = $("#modal-photo"); if (v.photo) { video.pause(); video.removeAttribute("src"); video.load(); video.hidden = true; ph.hidden = false; ph.src = v.poster; $("#modal-player").classList.add("paused", "is-photo"); }
    else { ph.hidden = true; video.hidden = false; $("#modal-player").classList.remove("is-photo"); video.src = v.src; video.poster = v.poster; video.load(); }
    $("#modal-cat").textContent = (c.emoji ? c.emoji + " " : "") + (c.name || "Other"); $("#modal-cat").style.setProperty("--c", c.color || "#fe2c55");
    $("#modal-title").textContent = v.title;
    $("#modal-stats").innerHTML = `<span>▶ <b>${fmt(v.views)}</b> views</span><span>♥ <b>${fmt(v.likes)}</b></span><span>⏱ <b>${mmss(v.dur)}</b></span><span>📅 <b>${esc(niceDate(v.date))}</b></span>`;
    $("#modal-music").textContent = v.music || "original sound";
    $("#modal-tags").innerHTML = v.tags.map(t => `<span>#${esc(t)}</span>`).join("");
    $("#modal-open").href = v.url;
    const pos = visible.findIndex(x => x._i === i);
    $("#modal-prev").disabled = pos <= 0; $("#modal-next").disabled = pos < 0 || pos >= visible.length - 1;
    $("#modal").hidden = false; document.body.style.overflow = "hidden";
    history.replaceState(null, "", "#v=" + v.id);
    if (!v.photo) video.play().catch(() => $("#modal-player").classList.add("paused"));
  }
  function closeModal() { video.pause(); video.removeAttribute("src"); video.load(); $("#modal").hidden = true; document.body.style.overflow = ""; current = -1; history.replaceState(null, "", location.pathname + location.search); }
  function step(d) { const pos = visible.findIndex(x => x._i === current); const nx = visible[pos + d]; if (nx) openModal(nx._i); }
  function bindPlayer() {
    const wrap = $("#modal-player"), fill = $("#p-fill"), buf = $("#p-buf"), time = $("#p-time"), bar = $("#p-bar");
    const toggle = () => video.paused ? video.play() : video.pause();
    video.addEventListener("click", toggle); $("#p-play").addEventListener("click", toggle);
    video.addEventListener("play", () => { wrap.classList.remove("paused"); $("#p-play").textContent = "❚❚"; });
    video.addEventListener("pause", () => { wrap.classList.add("paused"); $("#p-play").textContent = "▶"; });
    video.addEventListener("timeupdate", () => { const p = video.duration ? video.currentTime / video.duration : 0; fill.style.width = p * 100 + "%"; time.textContent = mmss(video.currentTime) + " / " + mmss(video.duration || 0); });
    video.addEventListener("progress", () => { try { const b = video.buffered; if (b.length && video.duration) buf.style.width = (b.end(b.length - 1) / video.duration) * 100 + "%"; } catch (e) {} });
    video.addEventListener("ended", () => { if ($("#autonext").checked && !$("#modal-next").disabled) step(1); });
    video.addEventListener("error", () => { wrap.classList.add("paused"); toast("Video file not found yet. Open on TikTok instead."); });
    bar.addEventListener("click", e => { const r = bar.getBoundingClientRect(); if (video.duration) video.currentTime = ((e.clientX - r.left) / r.width) * video.duration; });
    $("#p-mute").addEventListener("click", () => { video.muted = !video.muted; $("#p-mute").textContent = video.muted ? "🔇" : "🔊"; });
    $("#p-full").addEventListener("click", () => { (wrap.requestFullscreen || wrap.webkitRequestFullscreen || function () {}).call(wrap); });
    $("#modal-share").addEventListener("click", async () => { const v = VIDEOS[current]; if (!v) return; const url = location.origin + location.pathname + "#v=" + v.id; try { if (navigator.share) await navigator.share({ title: v.title, url }); else { await navigator.clipboard.writeText(url); toast("Link copied 🔗"); } } catch (e) {} });
  }

  /* ---------- particles canvas ---------- */
  function particles() {
    const cv = $("#fx"), ctx = cv.getContext("2d"); let w, h, pts = [], shooting = [], dpr = Math.min(2, devicePixelRatio || 1), mx = 0, my = 0;
    function resize() { w = cv.width = innerWidth * dpr; h = cv.height = innerHeight * dpr; cv.style.width = innerWidth + "px"; cv.style.height = innerHeight + "px"; const n = Math.min(260, Math.floor((innerWidth * innerHeight) / 7000)); pts = Array.from({ length: n }, () => ({ x: Math.random() * w, y: Math.random() * h, r: (Math.random() * 1.6 + .4) * dpr, a: Math.random() * 6, s: Math.random() * .02 + .005, vy: (Math.random() * .2 + .05) * dpr, vx: (Math.random() - .5) * .1 * dpr, hue: Math.random() < .5 ? "255,255,255" : (Math.random() < .5 ? "37,244,238" : "254,44,85") })); }
    addEventListener("mousemove", e => { mx = e.clientX / innerWidth - .5; my = e.clientY / innerHeight - .5; }, { passive: true });
    function frame() {
      ctx.clearRect(0, 0, w, h);
      for (const p of pts) { p.a += p.s; const tw = (Math.sin(p.a) + 1) / 2; p.y -= p.vy; p.x += p.vx; if (p.y < 0) { p.y = h; p.x = Math.random() * w; } const px = p.x + mx * 40 * dpr * p.r, py = p.y + my * 40 * dpr * p.r; ctx.beginPath(); ctx.arc(px, py, p.r, 0, Math.PI * 2); ctx.fillStyle = `rgba(${p.hue},${.15 + tw * .7})`; ctx.fill(); }
      if (Math.random() < .005 && shooting.length < 2) shooting.push({ x: Math.random() * w, y: Math.random() * h * .4, vx: (8 + Math.random() * 6) * dpr, vy: (3 + Math.random() * 3) * dpr, life: 1 });
      shooting = shooting.filter(s => s.life > 0);
      for (const s of shooting) { ctx.strokeStyle = `rgba(255,255,255,${s.life})`; ctx.lineWidth = 2 * dpr; ctx.lineCap = "round"; ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(s.x - s.vx * 6, s.y - s.vy * 6); ctx.stroke(); s.x += s.vx; s.y += s.vy; s.life -= .02; }
      requestAnimationFrame(frame);
    }
    addEventListener("resize", resize, { passive: true }); resize(); if (reduce) { frame(); return; } frame();
  }

  /* ---------- cursor, magnetic, ripple, confetti ---------- */
  function cursorFx() {
    if (touch) return;
    const cur = $("#cursor"); let x = 0, y = 0, rx = 0, ry = 0, last = 0;
    addEventListener("mousemove", e => { x = e.clientX; y = e.clientY; cur.querySelector(".dot").style.transform = `translate(${x}px,${y}px)`; if (!reduce && performance.now() - last > 40) { last = performance.now(); const t = document.createElement("i"); t.className = "trail"; t.style.left = x + "px"; t.style.top = y + "px"; t.style.background = Math.random() < .5 ? "var(--cyan)" : "var(--red)"; document.body.appendChild(t); setTimeout(() => t.remove(), 600); } }, { passive: true });
    (function loop() { rx += (x - rx) * .18; ry += (y - ry) * .18; cur.querySelector(".ring").style.transform = `translate(${rx}px,${ry}px)` + (document.body.classList.contains("hovering") ? " scale(1.8)" : ""); requestAnimationFrame(loop); })();
    document.addEventListener("mouseover", e => { document.body.classList.toggle("hovering", !!e.target.closest("a,button,.card,input,select,label")); });
    $$(".magnetic").forEach(el => { el.addEventListener("mousemove", e => { const r = el.getBoundingClientRect(); el.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * .25}px,${(e.clientY - r.top - r.height / 2) * .35}px) scale(1.04)`; }); el.addEventListener("mouseleave", () => { el.style.transform = ""; }); });
  }
  document.addEventListener("click", e => {
    const b = e.target.closest(".btn"); if (!b) return;
    const r = b.getBoundingClientRect(), s = document.createElement("span"); s.className = "ripple"; const d = Math.max(r.width, r.height); s.style.cssText = `width:${d}px;height:${d}px;left:${e.clientX - r.left - d / 2}px;top:${e.clientY - r.top - d / 2}px`; b.appendChild(s); setTimeout(() => s.remove(), 700);
    if (b.id.startsWith("follow")) confetti(e.clientX, e.clientY);
  });
  function confetti(x, y) {
    if (reduce) return;
    const cols = ["#fe2c55", "#25f4ee", "#ffb020", "#7c5cff", "#fff"];
    for (let i = 0; i < 36; i++) { const c = document.createElement("i"); c.className = "confetti"; const a = Math.random() * Math.PI * 2, d = 80 + Math.random() * 180; c.style.cssText = `left:${x}px;top:${y}px;background:${cols[i % cols.length]};--dx:${Math.cos(a) * d}px;--dy:${Math.sin(a) * d + 120}px;animation-delay:${Math.random() * .1}s`; document.body.appendChild(c); setTimeout(() => c.remove(), 1700); }
  }

  /* ---------- scroll stuff ---------- */
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { threshold: .1 });
  function observe() { $$(".card:not(.in)").forEach((el, i) => { el.style.transitionDelay = (i % 12) * 40 + "ms"; io.observe(el); }); $$(".reveal:not(.in)").forEach(el => io.observe(el)); $$("[data-split]:not(.splash-name):not(.done)").forEach(el => { el.classList.add("done"); splitText(el); }); }
  let lastY = 0;
  function onScroll() {
    const y = scrollY, max = document.documentElement.scrollHeight - innerHeight;
    $("#progress").style.width = (max ? y / max * 100 : 0) + "%";
    $("#topbar").classList.toggle("scrolled", y > 20);
    $("#topbar").classList.toggle("hide", y > lastY && y > 400 && !$("#topnav").classList.contains("open")); lastY = y;
    let cur = null; for (const s of $$(".cat-section")) if (s.getBoundingClientRect().top < 200) cur = s.id;
    $$("#topnav a").forEach(a => a.classList.toggle("active", a.getAttribute("href") === "#" + cur));
    const hy = Math.min(y, 700); $(".hero-inner").style.transform = `translateY(${hy * .18}px)`; $(".hero-inner").style.opacity = String(1 - hy / 1000);
  }

  /* ---------- wire up ---------- */
  function bind() {
    $("#search").addEventListener("input", e => { state.q = e.target.value; render(); });
    $("#sort").addEventListener("change", e => { state.sort = e.target.value; render(); });
    $("#chips").addEventListener("click", e => { const chip = e.target.closest(".chip"); if (!chip) return; $$(".chip").forEach(c => c.classList.toggle("active", c === chip)); state.cat = chip.dataset.cat; render(); if (state.cat !== "all") toast(`${catById[state.cat].emoji} ${catById[state.cat].name}`); });
    $("#clear-filters").addEventListener("click", () => { state.q = ""; state.cat = "all"; $("#search").value = ""; $$(".chip").forEach(c => c.classList.toggle("active", c.dataset.cat === "all")); render(); });
    $("#shuffle-btn").addEventListener("click", () => { visible = filtered(); openModal(VIDEOS[Math.floor(Math.random() * VIDEOS.length)]._i); });
    $$("[data-close]").forEach(el => el.addEventListener("click", closeModal));
    $("#modal-prev").addEventListener("click", () => step(-1)); $("#modal-next").addEventListener("click", () => step(1));
    addEventListener("keydown", e => { if ($("#modal").hidden) { if (e.key === "/" && document.activeElement !== $("#search")) { e.preventDefault(); $("#search").focus(); } return; } if (e.key === "Escape") closeModal(); if (e.key === "ArrowLeft") step(-1); if (e.key === "ArrowRight") step(1); if (e.key === " ") { e.preventDefault(); video.paused ? video.play() : video.pause(); } if (e.key === "m") $("#p-mute").click(); });
    const mb = $("#menu-btn"), nav = $("#topnav");
    mb.addEventListener("click", () => { const o = nav.classList.toggle("open"); mb.setAttribute("aria-expanded", String(o)); });
    nav.addEventListener("click", () => { nav.classList.remove("open"); mb.setAttribute("aria-expanded", "false"); });
    addEventListener("scroll", onScroll, { passive: true });
    const av = $("#avatar-wrap");
    av.addEventListener("mousemove", e => { const r = av.getBoundingClientRect(); const x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5; av.style.transform = `perspective(700px) rotateY(${x * 22}deg) rotateX(${-y * 22}deg)`; });
    av.addEventListener("mouseleave", () => { av.style.transform = ""; });
    av.addEventListener("click", () => { confetti(innerWidth / 2, innerHeight / 3); toast("You are amazing 💛"); });
  }

  document.addEventListener("DOMContentLoaded", () => {
    mountProfile(); mountCategories(); render(); bind(); bindPlayer(); particles(); cursorFx(); onScroll();
    setTimeout(() => { $$(".hero .reveal").forEach((el, i) => setTimeout(() => el.classList.add("in"), i * 110)); countUp(); typewriter(); }, reduce ? 0 : 2200);
    const m = /#v=(\d+)/.exec(location.hash); if (m) { const v = VIDEOS.find(x => x.id === m[1]); if (v) { visible = filtered(); setTimeout(() => openModal(v._i), reduce ? 0 : 2400); } }
  });
})();
