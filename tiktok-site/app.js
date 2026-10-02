/* Brandon Molina TikTok site. Renders from window.SITE (videos.js).
   Likes and comments: shared database when the page runs inside claude.ai with the db capability,
   otherwise this browser's own storage. */
(function () {
  "use strict";
  const S = window.SITE || { profile: {}, categories: [], videos: [] };
  const P = S.profile || {}, CATS = S.categories || [];
  const VBASE = P.videoBase || "videos/", CBASE = P.coverBase || "covers/";
  const VIDEOS = (S.videos || []).map((v, i) => ({
    _i: i, id: v.id, title: v.t || "Untitled", category: v.c, date: v.d || "", dur: v.s || 0,
    views: v.v || 0, likes: v.l || 0, music: v.m || "", tags: v.g || [], pinned: !!v.p, photo: !!v.ph, slide: !!v.sl,
    get src() { return window.ASSETS ? (window.ASSETS[this.id] ? "/_blob/" + window.ASSETS[this.id] : "") : VBASE + this.id + ".mp4"; },
    poster: CBASE + v.id + ".jpg", url: "https://www.tiktok.com/@" + P.handle + "/video/" + v.id
  }));
  const byId = Object.fromEntries(VIDEOS.map(v => [v.id, v]));
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const catById = Object.fromEntries(CATS.map(c => [c.id, c]));
  const handle = (P.handle || "").replace(/^@/, "");
  const tiktokUrl = (P.links && P.links.tiktok) || "https://www.tiktok.com/@" + handle;
  const PAGE = 24;
  const fmt = n => { n = Number(n) || 0; if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, "") + "M"; if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, "") + "K"; return String(n); };
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const mmss = s => { s = Math.max(0, Math.round(s || 0)); return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); };
  const niceDate = d => { if (!d) return ""; const t = new Date(d + "T00:00:00"); return isNaN(t) ? d : t.toLocaleDateString("en-AU", { day: "numeric", month: "short", year: "numeric" }); };
  const ago = ms => { const s = Math.max(1, (Date.now() - ms) / 1000); if (s < 60) return "just now"; if (s < 3600) return Math.floor(s / 60) + "m"; if (s < 86400) return Math.floor(s / 3600) + "h"; if (s < 86400 * 30) return Math.floor(s / 86400) + "d"; return new Date(ms).toLocaleDateString("en-AU", { day: "numeric", month: "short" }); };
  const toast = (() => { let el, t; return msg => { if (!el) { el = document.createElement("div"); el.className = "toast"; el.setAttribute("role", "status"); document.body.appendChild(el); } el.textContent = msg; el.classList.add("show"); clearTimeout(t); t = setTimeout(() => el.classList.remove("show"), 2200); }; })();
  const HEART = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 20.3 4.6 13a4.4 4.4 0 0 1 6.2-6.2l1.2 1.2 1.2-1.2a4.4 4.4 0 0 1 6.2 6.2z"/></svg>';
  const BUBBLE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4 4h16v12H7l-3 3z"/></svg>';
  const EYE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>';
  const GENERIC_AVATAR = "data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><circle cx="16" cy="16" r="16" fill="#9a9aa3"/><circle cx="16" cy="12" r="6" fill="#fff"/><path d="M4 28c2-6 7-8 12-8s10 2 12 8z" fill="#fff"/></svg>');

  /* ---------- social store ---------- */
  const social = {
    mode: "local", uid: null, me: null, canWrite: true, likeCount: {}, commentCount: {}, myLikes: {}, comments: {}, myDoc: { items: [] },
    listeners: [], onChange(fn) { this.listeners.push(fn); }, emit() { this.listeners.forEach(fn => fn()); }
  };
  const LS = { get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  let db = null, userNs = null, profileCache = {};
  function recountLikes(docs) { const c = {}; docs.forEach(d => Object.keys(d.v || {}).forEach(id => { c[id] = (c[id] || 0) + 1; })); social.likeCount = c; }
  function recountComments(all) { const by = {}; const c = {}; all.forEach(x => { (by[x.v] = by[x.v] || []).push(x); c[x.v] = (c[x.v] || 0) + 1; }); Object.values(by).forEach(l => l.sort((a, b) => a.at - b.at)); social.comments = by; social.commentCount = c; }
  async function initSocial() {
    const use = window.claude && window.claude.use;
    if (use) {
      try { [db, userNs] = await Promise.all([window.claude.use("db"), window.claude.use("user")]); } catch (e) { db = null; }
    }
    if (db && userNs) {
      social.mode = "shared";
      social.me = await userNs.me(); social.uid = social.me.id;
      const cw = await userNs.can("data.write"); social.canWrite = !!social.uid && cw !== false;
      db.collection("likes").onSnapshot(snap => {
        const docs = []; snap.docs.forEach(d => { const data = d.data() || {}; docs.push(data); if (d.id === social.uid) social.myLikes = Object.assign({}, data.v || {}); });
        recountLikes(docs); social.emit();
      }, () => { social.canWrite = false; social.emit(); });
      db.collection("comments").onSnapshot(snap => {
        const all = []; snap.docs.forEach(d => { const data = d.data() || {}; (data.items || []).forEach(it => all.push({ id: it.id, v: it.v, t: it.t, at: it.at, u: d.id })); if (d.id === social.uid) social.myDoc = { items: (data.items || []).slice() }; });
        recountComments(all); social.emit();
      }, () => {});
    } else {
      social.mode = "local"; social.uid = "me"; social.me = { id: "me", name: "You", avatarUrl: GENERIC_AVATAR };
      social.myLikes = LS.get("bm_likes", {}); social.myDoc = { items: LS.get("bm_comments", []) };
      recountLikes([{ v: social.myLikes }]); recountComments(social.myDoc.items.map(it => Object.assign({ u: "me" }, it)));
      social.emit();
    }
  }
  let likeBusy = false, commentBusy = false;
  async function toggleLike(vid) {
    if (!social.uid || likeBusy) return false;
    const next = Object.assign({}, social.myLikes); if (next[vid]) delete next[vid]; else next[vid] = true;
    if (social.mode === "shared") {
      likeBusy = true;
      try { await db.doc("likes/" + social.uid).set({ v: next }); social.myLikes = next; }
      catch (e) { social.canWrite = false; social.emit(); toast("You can't like on this page. Ask for contributor access."); likeBusy = false; return false; }
      likeBusy = false;
    } else { social.myLikes = next; LS.set("bm_likes", next); recountLikes([{ v: next }]); social.emit(); }
    return true;
  }
  async function postComment(vid, text) {
    if (!social.uid || commentBusy) return false;
    const item = { id: Date.now().toString(36) + Math.random().toString(36).slice(2, 7), v: vid, t: text, at: Date.now() };
    const items = social.myDoc.items.concat([item]);
    if (social.mode === "shared") {
      commentBusy = true;
      try { await db.doc("comments/" + social.uid).set({ items }); social.myDoc = { items }; }
      catch (e) { commentBusy = false; social.canWrite = false; social.emit(); toast("You can't comment on this page. Ask for contributor access."); return false; }
      commentBusy = false;
    } else { social.myDoc = { items }; LS.set("bm_comments", items); recountComments(items.map(it => Object.assign({ u: "me" }, it))); social.emit(); }
    return true;
  }
  async function deleteComment(id) {
    const items = social.myDoc.items.filter(it => it.id !== id);
    if (social.mode === "shared") { try { await db.doc("comments/" + social.uid).set({ items }); social.myDoc = { items }; } catch (e) { toast("Couldn't delete that."); } }
    else { social.myDoc = { items }; LS.set("bm_comments", items); recountComments(items.map(it => Object.assign({ u: "me" }, it))); social.emit(); }
  }
  async function profilesFor(ids) {
    if (social.mode !== "shared") return Object.fromEntries(ids.map(id => [id, { name: "You", avatarUrl: GENERIC_AVATAR }]));
    try { return await userNs.profiles(ids); } catch (e) { return {}; }
  }

  /* ---------- profile ---------- */
  function mountProfile() {
    const name = P.name || "Brandon Molina";
    $("#hero-name").textContent = name; $("#top-name").textContent = name; $("#footer-name").textContent = name;
    $("#hero-bio").textContent = P.bio || ""; $("#hero-location").textContent = P.location || "";
    $("#year").textContent = new Date().getFullYear();
    const h = $("#hero-handle"); h.textContent = "@" + handle; h.href = tiktokUrl;
    ["#follow-top", "#follow-hero"].forEach(id => { $(id).href = tiktokUrl; });
    document.title = name;
    const st = P.stats || {};
    const totals = { followers: st.followers || 0, likes: st.likes || 0, videos: st.videos || VIDEOS.length, views: st.views || VIDEOS.reduce((a, v) => a + v.views, 0) };
    $$("[data-count]").forEach(el => { el.textContent = fmt(totals[el.dataset.count] || 0); });
  }


  /* ---------- list ---------- */
  const state = { q: "", cat: "all", sort: "newest", shown: {} };
  let visible = [];
  function filtered() {
    const q = state.q.trim().toLowerCase();
    const list = VIDEOS.filter(v => (state.cat === "all" || v.category === state.cat) && (!q || v.title.toLowerCase().includes(q) || v.music.toLowerCase().includes(q) || v.tags.some(t => t.includes(q)) || (catById[v.category] || {}).name.toLowerCase().includes(q) || v.date.includes(q)));
    const byDate = (a, b) => b.date.localeCompare(a.date) || a._i - b._i;
    const sorts = { newest: byDate, oldest: (a, b) => -byDate(a, b), views: (a, b) => b.views - a.views, liked: (a, b) => (social.likeCount[b.id] || 0) - (social.likeCount[a.id] || 0) || byDate(a, b), commented: (a, b) => (social.commentCount[b.id] || 0) - (social.commentCount[a.id] || 0) || byDate(a, b), longest: (a, b) => b.dur - a.dur };
    list.sort(sorts[state.sort] || byDate);
    if (state.sort === "newest") list.sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0));
    return list;
  }
  function metaHtml(v) {
    const lc = social.likeCount[v.id] || 0, cc = social.commentCount[v.id] || 0;
    return `<span>${EYE}${fmt(v.views)}</span><span class="${social.myLikes[v.id] ? "liked" : ""}">${HEART}${lc}</span><span>${BUBBLE}${cc}</span>`;
  }
  function cardFor(v) {
    const b = document.createElement("button"); b.className = "card"; b.type = "button"; b.dataset.id = v.id;
    b.innerHTML = `<div class="thumb"><img src="${v.poster}" alt="" loading="lazy" decoding="async" width="360" height="640">${v.pinned ? '<span class="top-badge">Most viewed</span>' : ""}<span class="views">${fmt(v.views)} views</span><span class="dur">${v.slide ? "Slides " : ""}${mmss(v.dur)}</span></div><div class="title">${esc(v.title)}</div><div class="meta" data-meta>${metaHtml(v)}</div>`;
    b.addEventListener("click", () => openModal(v._i));
    return b;
  }
  function render(keepShown) {
    if (!keepShown) state.shown = {};
    visible = filtered();
    const grid = $("#feed"); grid.textContent = "";
    const lim = state.shown.all || 36;
    visible.slice(0, lim).forEach(v => grid.appendChild(cardFor(v)));
    const more = $("#more"); more.hidden = visible.length <= lim;
    more.textContent = "Show " + Math.min(36, visible.length - lim) + " more of " + (visible.length - lim);
    more.onclick = () => { state.shown.all = lim + 36; render(true); };
    $("#empty").hidden = visible.length > 0;
    $("#result-count").textContent = visible.length ? visible.length + " video" + (visible.length === 1 ? "" : "s") + (state.q ? ' matching "' + state.q + '"' : "") : "";
  }
  function refreshMeta() { $$(".card").forEach(el => { const v = byId[el.dataset.id]; if (v) el.querySelector("[data-meta]").innerHTML = metaHtml(v); }); }

  /* ---------- player and panel ---------- */
  const video = $("#player"); let current = -1;
  function openModal(i) {
    const v = VIDEOS[i]; if (!v) return;
    current = i; const c = catById[v.category] || {};
    const wrap = $("#modal-player"), ph = $("#modal-photo");
    if (v.photo || !v.src) { video.pause(); video.removeAttribute("src"); video.load(); video.hidden = true; ph.hidden = false; ph.src = v.poster; wrap.classList.add("paused", "is-photo"); }
    else { ph.hidden = true; video.hidden = false; wrap.classList.remove("is-photo"); video.src = v.src; video.poster = v.poster; video.load(); }
    $("#modal-title").textContent = v.title;
    $("#modal-stats").textContent = fmt(v.views) + " views on TikTok, " + fmt(v.likes) + " likes on TikTok, " + mmss(v.dur) + ", " + niceDate(v.date);
    $("#modal-music").textContent = "Sound: " + (v.music || "original sound");
    $("#modal-open").href = v.url;
    const pos = visible.findIndex(x => x._i === i);
    $("#modal-prev").disabled = pos <= 0; $("#modal-next").disabled = pos < 0 || pos >= visible.length - 1;
    $("#modal").hidden = false; document.body.style.overflow = "hidden";
    try { history.replaceState(null, "", "#v" + v.id); } catch (e) {}
    renderSocial();
    if (!v.photo && v.src) video.play().catch(() => wrap.classList.add("paused"));
    $(".modal-close").focus();
  }
  function closeModal() { video.pause(); video.removeAttribute("src"); video.load(); $("#modal").hidden = true; document.body.style.overflow = ""; current = -1; try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {} }
  function step(d) { const pos = visible.findIndex(x => x._i === current); const nx = visible[pos + d]; if (nx) openModal(nx._i); }
  async function renderSocial() {
    const v = VIDEOS[current]; if (!v) return;
    const lc = social.likeCount[v.id] || 0, mine = !!social.myLikes[v.id];
    $("#like-count").textContent = lc; $("#like-btn").setAttribute("aria-pressed", String(mine)); $("#like-btn").disabled = !social.uid;
    const list = social.comments[v.id] || [];
    $("#comment-count").textContent = list.length;
    const ol = $("#comment-list"); ol.textContent = "";
    if (!list.length) { const li = document.createElement("li"); li.className = "comment-empty"; li.textContent = "No comments yet."; ol.appendChild(li); }
    else {
      const ps = await profilesFor(Array.from(new Set(list.map(x => x.u))));
      if (VIDEOS[current] !== v) return;
      list.forEach(x => {
        const p = ps[x.u] || {}; const li = document.createElement("li"); li.className = "comment";
        const img = document.createElement("img"); img.src = p.avatarUrl || GENERIC_AVATAR; img.alt = "";
        const body = document.createElement("div");
        const who = document.createElement("div"); who.className = "who"; const nm = document.createElement("span"); nm.textContent = (x.u === social.uid ? (social.mode === "local" ? "You" : (p.name || "You")) : (p.name || "Someone")); const tm = document.createElement("time"); tm.textContent = ago(x.at); who.append(nm, tm);
        const text = document.createElement("p"); text.className = "text"; text.textContent = x.t;
        body.append(who, text);
        if (x.u === social.uid) { const del = document.createElement("button"); del.className = "del"; del.type = "button"; del.textContent = "Delete"; del.addEventListener("click", () => deleteComment(x.id)); body.appendChild(del); }
        li.append(img, body); ol.appendChild(li);
      });
    }
    const note = $("#comment-note"), form = $("#composer");
    if (!social.uid) { note.hidden = false; note.textContent = "Sign in to like and comment."; form.hidden = true; }
    else if (!social.canWrite) { note.hidden = false; note.textContent = "You can read comments here. Liking and commenting needs contributor access from Brandon."; form.hidden = true; }
    else { note.hidden = true; form.hidden = false; $("#composer-avatar").src = (social.me && social.me.avatarUrl) || GENERIC_AVATAR; }
  }
  function bindPlayer() {
    const wrap = $("#modal-player"), fill = $("#p-fill"), buf = $("#p-buf"), time = $("#p-time"), bar = $("#p-bar");
    const toggle = () => { if (video.hidden) return; video.paused ? video.play() : video.pause(); };
    $("#p-cover").addEventListener("click", toggle); $("#p-play").addEventListener("click", toggle);
    video.addEventListener("play", () => { wrap.classList.remove("paused"); $("#p-play-icon").setAttribute("d", "M6 5h4v14H6zm8 0h4v14h-4z"); });
    video.addEventListener("pause", () => { wrap.classList.add("paused"); $("#p-play-icon").setAttribute("d", "M8 5v14l11-7z"); });
    video.addEventListener("timeupdate", () => { const p = video.duration ? video.currentTime / video.duration : 0; fill.style.width = p * 100 + "%"; time.textContent = mmss(video.currentTime) + " / " + mmss(video.duration || 0); });
    video.addEventListener("progress", () => { try { const b = video.buffered; if (b.length && video.duration) buf.style.width = (b.end(b.length - 1) / video.duration) * 100 + "%"; } catch (e) {} });
    video.addEventListener("ended", () => { if ($("#autonext").checked && !$("#modal-next").disabled) step(1); });
    video.addEventListener("error", () => { if (video.getAttribute("src")) { wrap.classList.add("paused"); toast("This video couldn't load. Open it on TikTok instead."); } });
    bar.addEventListener("click", e => { const r = bar.getBoundingClientRect(); if (video.duration) video.currentTime = ((e.clientX - r.left) / r.width) * video.duration; });
    $("#p-mute").addEventListener("click", () => { video.muted = !video.muted; $("#p-mute-icon").setAttribute("d", video.muted ? "M3 9v6h4l5 5V4L7 9H3zm13 .4L14.6 8 13 9.6 14.4 11 13 12.4l1.6 1.6 1.4-1.4 1.4 1.4 1.6-1.6L17.6 11 19 9.6 17.4 8z" : "M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0 0 14 8v8a4.5 4.5 0 0 0 2.5-4z"); });
    $("#p-full").addEventListener("click", () => { const f = wrap.requestFullscreen || wrap.webkitRequestFullscreen; if (f) { try { const r = f.call(wrap); if (r && r.catch) r.catch(() => {}); } catch (e) {} } });
    $("#modal-share").addEventListener("click", async () => { const v = VIDEOS[current]; if (!v) return; const url = location.href.split("#")[0] + "#v" + v.id; try { await navigator.clipboard.writeText(url); toast("Link copied"); } catch (e) { const ta = document.createElement("textarea"); ta.value = url; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); toast("Link copied"); } catch (e2) { toast(url); } ta.remove(); } });
    $("#like-btn").addEventListener("click", async () => { const v = VIDEOS[current]; if (!v) return; const ok = await toggleLike(v.id); if (ok && social.mode === "local") renderSocial(); });
    const form = $("#composer"), ta = $("#comment-text");
    form.addEventListener("submit", async e => { e.preventDefault(); const v = VIDEOS[current]; const text = ta.value.trim(); if (!v || !text) return; $("#comment-post").disabled = true; const ok = await postComment(v.id, text); $("#comment-post").disabled = false; if (ok) { ta.value = ""; ta.style.height = ""; if (social.mode === "local") renderSocial(); } });
    ta.addEventListener("input", () => { ta.style.height = "auto"; ta.style.height = Math.min(120, ta.scrollHeight) + "px"; });
    ta.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
  }

  /* ---------- wiring ---------- */
  function bind() {
    let t; $("#search").addEventListener("input", e => { clearTimeout(t); t = setTimeout(() => { state.q = e.target.value; render(); }, 120); });
    $("#sort").addEventListener("change", e => { state.sort = e.target.value; render(); });
    $("#clear-filters").addEventListener("click", () => { state.q = ""; $("#search").value = ""; render(); });
    $("#shuffle-btn").addEventListener("click", () => { visible = filtered(); openModal(VIDEOS[Math.floor(Math.random() * VIDEOS.length)]._i); });
    $$("[data-close]").forEach(el => el.addEventListener("click", closeModal));
    $("#modal-prev").addEventListener("click", () => step(-1)); $("#modal-next").addEventListener("click", () => step(1));
    addEventListener("keydown", e => { if ($("#modal").hidden) { if (e.key === "/" && document.activeElement !== $("#search")) { e.preventDefault(); $("#search").focus(); } return; } const typing = /TEXTAREA|INPUT/.test(document.activeElement.tagName); if (e.key === "Escape") closeModal(); if (typing) return; if (e.key === "ArrowLeft") step(-1); if (e.key === "ArrowRight") step(1); if (e.key === " ") { e.preventDefault(); $("#p-play").click(); } if (e.key === "m") $("#p-mute").click(); });
    social.onChange(() => { refreshMeta(); if (current >= 0) renderSocial(); if (state.sort === "liked" || state.sort === "commented") render(true); });
  }

  document.addEventListener("DOMContentLoaded", () => {
    mountProfile(); render(); bind(); bindPlayer();
    initSocial();
    const m = /#v(\d+)/.exec(location.hash); if (m && byId[m[1]]) { visible = filtered(); openModal(byId[m[1]]._i); }
  });
})();
