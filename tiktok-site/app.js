/* =====================================================================
   ECHOES IN THE DARK — TikTok site app
   Reads window.SITE (videos.js) and renders everything.
   ===================================================================== */
(function () {
  "use strict";
  const S = window.SITE || { profile: {}, categories: [], videos: [] };
  const P = S.profile || {};
  const CATS = S.categories || [];
  const VIDEOS = (S.videos || []).map((v, i) => ({ ...v, _i: i }));
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const catById = Object.fromEntries(CATS.map(c => [c.id, c]));
  const handle = (P.handle || "").replace(/^@/, "");
  const tiktokUrl = P.links && P.links.tiktok ? P.links.tiktok : (handle ? `https://www.tiktok.com/@${handle}` : "https://www.tiktok.com/");

  /* ---------- helpers ---------- */
  const fmt = n => {
    n = Number(n) || 0;
    if (n >= 1e9) return (n / 1e9).toFixed(1).replace(/\.0$/, "") + "B";
    if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, "") + "K";
    return String(n);
  };
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const videoId = url => { const m = /\/video\/(\d+)/.exec(url || ""); return m ? m[1] : null; };
  const toast = (() => {
    let el, t;
    return msg => {
      if (!el) { el = document.createElement("div"); el.className = "toast"; document.body.appendChild(el); }
      el.textContent = msg; el.classList.add("show"); clearTimeout(t); t = setTimeout(() => el.classList.remove("show"), 2600);
    };
  })();

  /* ---------- logo (image if present, otherwise built-in animated mark) ---------- */
  const LOGO_SVG = `
    <svg class="logo-mark" viewBox="0 0 100 100" aria-label="Echoes in the Dark">
      <defs>
        <linearGradient id="lg" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stop-color="#25f4ee"/><stop offset=".5" stop-color="#8b5cf6"/><stop offset="1" stop-color="#fe2c55"/>
        </linearGradient>
      </defs>
      <circle class="ring" cx="50" cy="50" r="44" fill="none" stroke="url(#lg)" stroke-width="3" stroke-dasharray="40 18 90 30"/>
      <circle class="ring ring2" cx="50" cy="50" r="33" fill="none" stroke="url(#lg)" stroke-width="2" stroke-dasharray="12 10" opacity=".8"/>
      <circle cx="50" cy="50" r="20" fill="#07060f" stroke="url(#lg)" stroke-width="2"/>
      <path d="M38 50 Q44 36 50 50 T62 50" fill="none" stroke="url(#lg)" stroke-width="3" stroke-linecap="round"/>
      <circle cx="50" cy="50" r="3" fill="#fff"/>
    </svg>`;
  function mountLogos() {
    const slots = $$("[data-logo]");
    const useImg = src => slots.forEach(s => { s.innerHTML = `<img src="${esc(src)}" alt="Echoes in the Dark logo">`; });
    const useSvg = () => slots.forEach(s => { s.innerHTML = LOGO_SVG; });
    if (!P.logo) return useSvg();
    const img = new Image();
    img.onload = () => useImg(P.logo);
    img.onerror = useSvg;
    img.src = P.logo;
  }

  /* ---------- profile ---------- */
  function mountProfile() {
    const name = P.name || "Echoes in the Dark";
    $("#hero-name").textContent = name;
    $("#hero-studio").textContent = P.studio || "Echoes in the Dark";
    $("#hero-tagline").textContent = P.tagline || "";
    $("#hero-bio").textContent = P.bio || "";
    $("#footer-name").textContent = name;
    $("#year").textContent = new Date().getFullYear();
    const h = $("#hero-handle");
    h.textContent = handle ? "@" + handle : "@ add your handle in videos.js";
    h.href = tiktokUrl;
    $("#cta-handle").textContent = handle ? "@" + handle : "on TikTok";
    ["#follow-top", "#follow-hero", "#follow-cta"].forEach(id => { $(id).href = tiktokUrl; });
    document.title = (handle ? "@" + handle + " · " : "") + "Echoes in the Dark — TikTok";

    // avatar
    const img = $("#avatar-img"), fb = $("#avatar-fallback");
    fb.textContent = name.split(/\s+/).map(w => w[0]).join("").slice(0, 2).toUpperCase() || "E";
    img.alt = name + " profile picture";
    if (P.avatar) {
      img.onload = () => fb.classList.add("avatar-fallback-hidden");
      img.onerror = () => { img.classList.add("broken"); };
      img.src = P.avatar;
    }

    // stats with count-up
    const st = P.stats || {};
    const totals = { followers: st.followers || 0, likes: st.likes || 0, videos: st.videos || VIDEOS.length };
    $$("[data-count]").forEach(el => { el.dataset.target = totals[el.dataset.count] || 0; el.textContent = "0"; });

    // socials
    const L = P.links || {};
    const icons = {
      instagram: `<svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M7 2h10a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5zm0 2a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3H7zm5 3.5a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9zm0 2a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM17.5 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/></svg>`,
      youtube: `<svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12 31 31 0 0 0 1 16.8a3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1c.4-1.6.5-3.2.5-4.8s-.1-3.2-.5-4.8zM9.8 15.1V8.9l6 3.1-6 3.1z"/></svg>`,
      spotify: `<svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm4.6 14.4a.6.6 0 0 1-.9.2c-2.4-1.5-5.4-1.8-9-1a.6.6 0 1 1-.3-1.2c3.9-.9 7.3-.5 10 1.1.3.2.4.6.2.9zm1.2-2.7a.8.8 0 0 1-1.1.3c-2.8-1.7-7-2.2-10.3-1.2a.8.8 0 1 1-.4-1.5c3.7-1.1 8.4-.6 11.6 1.4.3.2.4.7.2 1zm.1-2.8C14.6 9 9.2 8.8 6.1 9.7a.9.9 0 1 1-.5-1.8c3.6-1.1 9.5-.9 13.3 1.4a.9.9 0 0 1-.9 1.6z"/></svg>`,
      email: `<svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm0 2v.5l8 5 8-5V6H4zm0 2.8V18h16V8.8l-8 5-8-5z"/></svg>`
    };
    const wrap = $("#socials");
    Object.entries(icons).forEach(([k, svg]) => {
      if (!L[k]) return;
      const a = document.createElement("a");
      a.href = k === "email" ? "mailto:" + L[k] : L[k];
      a.target = k === "email" ? "_self" : "_blank"; a.rel = "noopener"; a.title = k; a.innerHTML = svg;
      wrap.appendChild(a);
    });
  }

  function countUp() {
    $$("[data-count]").forEach(el => {
      const target = Number(el.dataset.target) || 0, t0 = performance.now(), dur = 1600;
      const step = t => {
        const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
        el.textContent = fmt(Math.round(target * e));
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
  }

  /* ---------- categories ---------- */
  const countFor = id => VIDEOS.filter(v => v.category === id).length;
  function mountCategories() {
    const nav = $("#topnav"), grid = $("#cat-grid"), chips = $("#chips");
    const allChip = document.createElement("button");
    allChip.className = "chip active"; allChip.dataset.cat = "all"; allChip.textContent = "All"; allChip.setAttribute("role", "tab");
    chips.appendChild(allChip);
    CATS.forEach(c => {
      const a = document.createElement("a");
      a.href = "#cat-" + c.id; a.textContent = c.emoji + " " + c.name; nav.appendChild(a);

      const card = document.createElement("a");
      card.className = "cat-card reveal"; card.href = "#cat-" + c.id; card.style.setProperty("--c", c.color || "#8b5cf6");
      card.innerHTML = `<span class="emoji">${esc(c.emoji || "")}</span><h3>${esc(c.name)}</h3><p>${esc(c.blurb || "")}</p><span class="count">${countFor(c.id)} video${countFor(c.id) === 1 ? "" : "s"}</span>`;
      grid.appendChild(card);

      const chip = document.createElement("button");
      chip.className = "chip"; chip.dataset.cat = c.id; chip.setAttribute("role", "tab");
      chip.style.setProperty("--c", c.color || "#8b5cf6"); chip.textContent = c.emoji + " " + c.name;
      chips.appendChild(chip);
    });
  }

  /* ---------- video rendering ---------- */
  const state = { q: "", cat: "all", sort: "newest" };
  let visible = [];

  function filtered() {
    const q = state.q.trim().toLowerCase();
    let list = VIDEOS.filter(v => (state.cat === "all" || v.category === state.cat) &&
      (!q || (v.title || "").toLowerCase().includes(q) || (v.tags || []).some(t => t.toLowerCase().includes(q)) || (catById[v.category]?.name || "").toLowerCase().includes(q)));
    const byDate = (a, b) => (b.date || "").localeCompare(a.date || "") || a._i - b._i;
    if (state.sort === "newest") list.sort(byDate);
    if (state.sort === "oldest") list.sort((a, b) => -byDate(a, b));
    if (state.sort === "az") list.sort((a, b) => (a.title || "").localeCompare(b.title || ""));
    list.sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0));
    return list;
  }

  const TT_ICON = `<svg class="tt" viewBox="0 0 24 24"><path fill="#fff" d="M16.5 3c.4 2.4 1.9 4 4.5 4.2v3.2c-1.7 0-3.2-.5-4.5-1.4v6.4A6.4 6.4 0 1 1 10 9v3.3a3.2 3.2 0 1 0 3.3 3.2V3h3.2z"/></svg>`;

  function cardFor(v, n) {
    const c = catById[v.category] || {};
    const b = document.createElement("button");
    b.className = "card" + (v.demo ? " has-demo" : ""); b.type = "button"; b.dataset.index = v._i;
    b.style.setProperty("--c", c.color || "#8b5cf6");
    b.setAttribute("aria-label", "Play: " + (v.title || "video"));
    b.innerHTML = `
      <div class="poster gen" data-poster></div>
      <div class="shade"></div>
      ${v.pinned ? `<span class="badge">Pinned</span>` : `<span class="num">#${n}</span>`}
      ${v.demo ? `<span class="badge demo">Demo</span>` : ""}
      <div class="play"></div>
      <div class="meta">
        <div class="title">${esc(v.title || "Untitled")}</div>
        <div class="sub"><span class="dot"></span><span>${esc(c.name || "")}</span>${v.date ? `<span>· ${esc(v.date)}</span>` : ""}</div>
      </div>
      ${TT_ICON}`;
    b.addEventListener("click", () => openModal(v._i));
    loadPoster(v, b.querySelector("[data-poster]"));
    return b;
  }

  // TikTok oEmbed gives the cover image + real title for any public video link.
  const posterCache = new Map();
  async function loadPoster(v, el) {
    if (!v.url) return;
    if (posterCache.has(v.url)) return apply(posterCache.get(v.url));
    try {
      const r = await fetch("https://www.tiktok.com/oembed?url=" + encodeURIComponent(v.url));
      if (!r.ok) throw new Error(r.status);
      const j = await r.json();
      posterCache.set(v.url, j); apply(j);
    } catch (e) { /* keep generated poster */ }
    function apply(j) {
      if (j && j.thumbnail_url) {
        const im = new Image();
        im.onload = () => { el.classList.remove("gen"); el.style.backgroundImage = `url("${j.thumbnail_url}")`; };
        im.src = j.thumbnail_url;
      }
    }
  }

  function render() {
    visible = filtered();
    const root = $("#sections"); root.innerHTML = "";
    const cats = state.cat === "all" ? CATS : CATS.filter(c => c.id === state.cat);
    let shown = 0;
    cats.forEach(c => {
      const list = visible.filter(v => v.category === c.id);
      if (!list.length) return;
      shown += list.length;
      const sec = document.createElement("section");
      sec.className = "section cat-section"; sec.id = "cat-" + c.id; sec.style.setProperty("--c", c.color || "#8b5cf6");
      sec.innerHTML = `<h2><span class="emoji">${esc(c.emoji || "")}</span>${esc(c.name)} <span class="pill">${list.length}</span></h2><p class="blurb">${esc(c.blurb || "")}</p><div class="grid"></div>`;
      const grid = sec.querySelector(".grid");
      list.forEach((v, i) => grid.appendChild(cardFor(v, i + 1)));
      root.appendChild(sec);
    });
    // uncategorised videos (typo in category id) still show up so nothing gets lost
    const orphans = visible.filter(v => !catById[v.category]);
    if (orphans.length && (state.cat === "all")) {
      shown += orphans.length;
      const sec = document.createElement("section");
      sec.className = "section cat-section"; sec.id = "cat-other";
      sec.innerHTML = `<h2>Other <span class="pill">${orphans.length}</span></h2><p class="blurb">These videos have a category id that isn't in the list. Fix it in videos.js.</p><div class="grid"></div>`;
      orphans.forEach((v, i) => sec.querySelector(".grid").appendChild(cardFor(v, i + 1)));
      root.appendChild(sec);
    }
    $("#empty").hidden = shown > 0;
    $("#result-count").textContent = shown ? `${shown} video${shown === 1 ? "" : "s"}${state.q ? ` matching “${state.q}”` : ""}` : "";
    observeCards();
  }

  /* ---------- modal player ---------- */
  let current = -1;
  function openModal(i) {
    const v = VIDEOS[i]; if (!v) return;
    current = i;
    const c = catById[v.category] || {};
    const m = $("#modal"), player = $("#modal-player");
    const id = videoId(v.url);
    player.innerHTML = id
      ? `<iframe src="https://www.tiktok.com/embed/v2/${id}" allow="autoplay; encrypted-media; fullscreen; picture-in-picture" allowfullscreen title="${esc(v.title || "TikTok video")}"></iframe>`
      : `<div class="no-video">${v.url ? "This link doesn't look like a TikTok video link.<br>It needs to contain <b>/video/&lt;id&gt;</b>." : "No TikTok link yet.<br>Paste the video URL into <b>videos.js</b> to play it here."}</div>`;
    $("#modal-cat").textContent = (c.emoji ? c.emoji + " " : "") + (c.name || "Other");
    $("#modal-cat").style.setProperty("--c", c.color || "#8b5cf6");
    $("#modal-title").textContent = v.title || "Untitled";
    $("#modal-tags").innerHTML = (v.tags || []).map(t => `<span>#${esc(t)}</span>`).join("");
    const open = $("#modal-open"); open.href = v.url || tiktokUrl; open.textContent = v.url ? "Open on TikTok ↗" : "Go to profile ↗";
    const pos = visible.findIndex(x => x._i === i);
    $("#modal-prev").disabled = pos <= 0; $("#modal-next").disabled = pos < 0 || pos >= visible.length - 1;
    m.hidden = false; document.body.style.overflow = "hidden";
    $(".modal-close").focus();
  }
  function closeModal() { $("#modal").hidden = true; $("#modal-player").innerHTML = ""; document.body.style.overflow = ""; current = -1; }
  function step(d) { const pos = visible.findIndex(x => x._i === current); const nx = visible[pos + d]; if (nx) openModal(nx._i); }

  /* ---------- starfield ---------- */
  function starfield() {
    const cv = $("#stars"), ctx = cv.getContext("2d");
    let w, h, stars = [], shooting = [], dpr = Math.min(2, window.devicePixelRatio || 1);
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    function resize() {
      w = cv.width = innerWidth * dpr; h = cv.height = innerHeight * dpr;
      cv.style.width = innerWidth + "px"; cv.style.height = innerHeight + "px";
      const n = Math.min(420, Math.floor((innerWidth * innerHeight) / 4500));
      stars = Array.from({ length: n }, () => ({ x: Math.random() * w, y: Math.random() * h, r: (Math.random() * 1.4 + .3) * dpr, a: Math.random(), s: Math.random() * .02 + .005, d: Math.random() * .15 + .05 }));
    }
    let mx = 0, my = 0;
    addEventListener("mousemove", e => { mx = (e.clientX / innerWidth - .5); my = (e.clientY / innerHeight - .5); });
    function frame() {
      ctx.clearRect(0, 0, w, h);
      for (const s of stars) {
        s.a += s.s; const tw = (Math.sin(s.a) + 1) / 2;
        s.y += s.d * dpr; if (s.y > h) { s.y = 0; s.x = Math.random() * w; }
        const px = s.x + mx * 30 * dpr * s.r, py = s.y + my * 30 * dpr * s.r;
        ctx.beginPath(); ctx.arc(px, py, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${.25 + tw * .75})`; ctx.fill();
      }
      if (!reduce && Math.random() < .006 && shooting.length < 2) shooting.push({ x: Math.random() * w, y: Math.random() * h * .4, vx: (8 + Math.random() * 6) * dpr, vy: (3 + Math.random() * 3) * dpr, life: 1 });
      shooting = shooting.filter(s => s.life > 0);
      for (const s of shooting) {
        ctx.strokeStyle = `rgba(255,255,255,${s.life})`; ctx.lineWidth = 2 * dpr; ctx.lineCap = "round";
        ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(s.x - s.vx * 6, s.y - s.vy * 6); ctx.stroke();
        s.x += s.vx; s.y += s.vy; s.life -= .02;
      }
      if (!reduce) requestAnimationFrame(frame);
    }
    addEventListener("resize", resize, { passive: true }); resize(); frame();
  }

  /* ---------- scroll reveal / active nav ---------- */
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { threshold: .12 });
  function observeCards() {
    $$(".card").forEach((el, i) => { el.style.transitionDelay = (i % 12) * 45 + "ms"; io.observe(el); });
    $$(".reveal:not(.in)").forEach(el => io.observe(el));
  }
  function activeNav() {
    const secs = $$(".cat-section"), links = $$("#topnav a");
    let cur = null;
    for (const s of secs) if (s.getBoundingClientRect().top < 160) cur = s.id;
    links.forEach(a => a.classList.toggle("active", a.getAttribute("href") === "#" + cur));
    $(".topbar").classList.toggle("scrolled", scrollY > 20);
  }

  /* ---------- wire up ---------- */
  function bind() {
    $("#search").addEventListener("input", e => { state.q = e.target.value; render(); });
    $("#sort").addEventListener("change", e => { state.sort = e.target.value; render(); });
    $("#chips").addEventListener("click", e => {
      const chip = e.target.closest(".chip"); if (!chip) return;
      $$(".chip").forEach(c => c.classList.toggle("active", c === chip));
      state.cat = chip.dataset.cat; render();
      if (state.cat !== "all") toast((catById[state.cat]?.emoji || "") + " " + (catById[state.cat]?.name || ""));
    });
    $("#clear-filters").addEventListener("click", () => { state.q = ""; state.cat = "all"; $("#search").value = ""; $$(".chip").forEach(c => c.classList.toggle("active", c.dataset.cat === "all")); render(); });
    $$("[data-close]").forEach(el => el.addEventListener("click", closeModal));
    $("#modal-prev").addEventListener("click", () => step(-1));
    $("#modal-next").addEventListener("click", () => step(1));
    addEventListener("keydown", e => {
      if ($("#modal").hidden) return;
      if (e.key === "Escape") closeModal();
      if (e.key === "ArrowLeft") step(-1);
      if (e.key === "ArrowRight") step(1);
    });
    const mb = $("#menu-btn"), nav = $("#topnav");
    mb.addEventListener("click", () => { const o = nav.classList.toggle("open"); mb.setAttribute("aria-expanded", String(o)); });
    nav.addEventListener("click", () => { nav.classList.remove("open"); mb.setAttribute("aria-expanded", "false"); });
    addEventListener("scroll", activeNav, { passive: true });
    const glow = $("#cursor-glow");
    addEventListener("mousemove", e => { glow.style.left = e.clientX + "px"; glow.style.top = e.clientY + "px"; glow.style.opacity = "1"; }, { passive: true });
    // hero parallax
    addEventListener("scroll", () => { const y = Math.min(scrollY, 600); $(".hero-inner").style.transform = `translateY(${y * .15}px)`; $(".hero-inner").style.opacity = String(1 - y / 900); }, { passive: true });
    // avatar tilt
    const av = $(".avatar-wrap");
    av.addEventListener("mousemove", e => { const r = av.getBoundingClientRect(); const x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5; av.style.transform = `perspective(700px) rotateY(${x * 18}deg) rotateX(${-y * 18}deg)`; });
    av.addEventListener("mouseleave", () => { av.style.transform = ""; });
    av.style.transition = "transform .3s ease";
  }

  /* ---------- go ---------- */
  document.addEventListener("DOMContentLoaded", () => {
    mountLogos(); mountProfile(); mountCategories(); render(); bind(); starfield(); activeNav();
    setTimeout(() => { $$(".hero .reveal").forEach((el, i) => setTimeout(() => el.classList.add("in"), i * 110)); countUp(); }, 1900);
    if (!handle) console.warn("[Echoes] No TikTok handle set — edit profile.handle in videos.js");
    if (VIDEOS.some(v => v.demo)) console.warn("[Echoes] Demo videos are still in videos.js — replace them with your real links");
  });
})();
