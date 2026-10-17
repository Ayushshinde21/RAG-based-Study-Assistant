const API = window.API_BASE || "";
const $ = (s) => document.querySelector(s);
// localStorage can throw (private mode, blocked cookies, quota). Never let that break the app.
const store = {
  get(key) { try { return localStorage.getItem(key); } catch { return null; } },
  set(key, value) { try { localStorage.setItem(key, value); } catch {} },
  remove(key) { try { localStorage.removeItem(key); } catch {} }
};
const ICONS = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  library: '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 5.5v15A2.5 2.5 0 0 1 6.5 18H20M8 7h8M8 10h8"/>',
  brain: '<path d="M12 18V5.5a3.5 3.5 0 0 0-6.8-1.1A4 4 0 0 0 3.5 11a4 4 0 0 0 2 6.7A3.5 3.5 0 0 0 12 18Z"/><path d="M12 8a3 3 0 0 1 3-3 3.5 3.5 0 0 1 3.8 3.4A4 4 0 0 1 20 15a3.5 3.5 0 0 1-5 3.1A3.5 3.5 0 0 1 12 15M8 8l2 1M7 14l2-1M16 10l-2 1M16 15l-2-1"/>',
  moon: '<path d="M20.9 13A8.5 8.5 0 0 1 11 3.1 8.5 8.5 0 1 0 20.9 13Z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/>',
  sparkles: '<path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z"/><path d="m19 14 1.1 2.9L23 18l-2.9 1.1L19 22l-1.1-2.9L15 18l2.9-1.1L19 14ZM5 2l.8 2.2L8 5l-2.2.8L5 8l-.8-2.2L2 5l2.2-.8L5 2Z"/>',
  'arrow-up-right': '<path d="M7 17 17 7M7 7h10v10"/>',
  'arrow-right': '<path d="M5 12h14m-7-7 7 7-7 7"/>',
  search: '<circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4.5 4.5"/>',
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
  'chevron-down': '<path d="m6 9 6 6 6-6"/>',
  'calendar-days': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18M8 14h.01M12 14h.01M16 14h.01M8 17h.01M12 17h.01"/>',
  upload: '<path d="M12 16V4m-5 5 5-5 5 5"/><path d="M4 16v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
  'book-open': '<path d="M12 7v14M3 5.5A2.5 2.5 0 0 1 5.5 3H12v18H5.5A2.5 2.5 0 0 0 3 23z"/><path d="M21 5.5A2.5 2.5 0 0 0 18.5 3H12v18h6.5A2.5 2.5 0 0 1 21 23z"/>',
  'check-circle': '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>',
  'file-text': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h8"/>',
  'clipboard-check': '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4.5V3h6v1.5M8.5 13l2.2 2.2 4.8-4.8"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/>',
  'message-circle': '<path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5Z"/>',
  compass: '<circle cx="12" cy="12" r="10"/><path d="m16.2 7.8-2.7 5.7-5.7 2.7 2.7-5.7 5.7-2.7Z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  'external-link': '<path d="M14 3h7v7M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  download: '<path d="M12 3v12m-5-5 5 5 5-5"/><path d="M4 17v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
  'book-mark': '<path d="M6 3h12a2 2 0 0 1 2 2v16l-8-4-8 4V5a2 2 0 0 1 2-2Z"/>',
  lightbulb: '<path d="M9 18h6M10 22h4M8 14c-1.2-1-2-2.4-2-4a6 6 0 1 1 12 0c0 1.6-.8 3-2 4-.6.5-1 1.2-1 2h-6c0-.8-.4-1.5-1-2Z"/>',
  'circle-help': '<circle cx="12" cy="12" r="10"/><path d="M9.5 9a2.6 2.6 0 1 1 4.7 1.5c-1.2 1.1-2.2 1.4-2.2 3M12 17h.01"/>',
  'file-check': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6m-12 5 2 2 4-4"/>',
  'panel-right': '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M15 4v16"/>',
  'play-circle': '<circle cx="12" cy="12" r="9"/><path d="m10 8 6 4-6 4z"/>',
};
const ico = (name, cls = "") => `<svg${cls ? ` class="${cls}"` : ""} viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ICONS.sparkles}</svg>`;
const paintIcons = (scope = document) => scope.querySelectorAll("[data-icon]").forEach((el) => { el.innerHTML = ico(el.dataset.icon); });
paintIcons();
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function renderInline(source) {
  let html = esc(source);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/__(.+?)__/g, "<strong>$1</strong>");
  html = html.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1<em>$2</em>");
  html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  return html;
}

// ---- Markdown table helpers ----
function splitTableRow(line) {
  let text = line.trim();
  if (text.startsWith("|")) text = text.slice(1);
  if (text.endsWith("|") && !text.endsWith("\\|")) text = text.slice(0, -1);
  const cells = [];
  let cell = "", inCode = false;
  for (let k = 0; k < text.length; k++) {
    const ch = text[k];
    if (ch === "\\" && text[k + 1] === "|") { cell += "|"; k++; continue; }
    if (ch === "`") inCode = !inCode;
    if (ch === "|" && !inCode) { cells.push(cell.trim()); cell = ""; continue; }
    cell += ch;
  }
  cells.push(cell.trim());
  return cells;
}
const isTableSeparator = (line) => line.includes("|") && /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$/.test(line);
const looksLikeTableRow = (line) => line.includes("|") && line.trim().length > 1;

function renderRichText(source, options = {}) {
  const lines = String(source ?? "").replace(/\r\n?/g, "\n").split("\n");
  const output = [];
  let paragraph = [];
  let listItems = [];
  let codeLines = [];
  let inCode = false;
  let codeLanguage = "";
  let sectionNumber = 0;

  const flushParagraph = () => {
    if (!paragraph.length) return;
    const text = paragraph.join(" ").trim();
    if (text) output.push(`<p class="rich-paragraph">${renderInline(text)}</p>`);
    paragraph = [];
  };

  const flushList = () => {
    if (!listItems.length) return;
    const ordered = listItems[0].ordered;
    const tag = ordered ? "ol" : "ul";
    const items = listItems.map((item) => {
      const depth = Math.min(3, item.depth);
      const id = options.headingPrefix && options.listItemAnchors !== false && depth === 0 ? ` id="${options.headingPrefix}-section-${++sectionNumber}"` : "";
      return `<li class="rich-list-item depth-${depth}"${id}>${renderInline(item.text)}</li>`;
    }).join("");
    output.push(`<${tag} class="rich-list${ordered ? " is-ordered" : ""}">${items}</${tag}>`);
    listItems = [];
  };

  const flushCode = () => {
    const lang = codeLanguage ? ` data-language="${esc(codeLanguage)}"` : "";
    output.push(`<pre class="rich-code"${lang}><code>${esc(codeLines.join("\n"))}</code></pre>`);
    codeLines = [];
    codeLanguage = "";
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (inCode) {
      if (/^\s*```/.test(line)) {
        flushCode();
        inCode = false;
      } else {
        codeLines.push(line);
      }
      continue;
    }

    const fence = line.match(/^\s*```([\w.+-]*)\s*$/);
    if (fence) {
      flushParagraph();
      flushList();
      inCode = true;
      codeLanguage = fence[1] || "";
      continue;
    }

    if (looksLikeTableRow(line) && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const head = splitTableRow(line);
      const aligns = splitTableRow(lines[i + 1]).map((c) => (c.startsWith(":") && c.endsWith(":") ? "center" : c.endsWith(":") ? "right" : c.startsWith(":") ? "left" : ""));
      if (head.length === aligns.length) {
        flushParagraph();
        flushList();
        const cellTag = (tag, text, idx) => `<${tag}${aligns[idx] ? ` style="text-align:${aligns[idx]}"` : ""}>${renderInline(text)}</${tag}>`;
        const bodyRows = [];
        let r = i + 2;
        while (r < lines.length && lines[r].trim() && looksLikeTableRow(lines[r])) {
          const cells = splitTableRow(lines[r]);
          bodyRows.push(`<tr>${head.map((_, idx) => cellTag("td", cells[idx] ?? "", idx)).join("")}</tr>`);
          r++;
        }
        output.push(`<div class="rich-table-wrap" tabindex="0" role="region" aria-label="Table"><table class="rich-table"><thead><tr>${head.map((h, idx) => cellTag("th", h, idx)).join("")}</tr></thead><tbody>${bodyRows.join("")}</tbody></table></div>`);
        i = r - 1;
        continue;
      }
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      flushList();
      const level = heading[1].length;
      const id = options.headingPrefix ? ` id="${options.headingPrefix}-section-${++sectionNumber}"` : "";
      output.push(`<h${level} class="rich-heading"${id}>${renderInline(heading[2])}</h${level}>`);
      continue;
    }

    if (/^\s*(?:---+|\*\*\*+)\s*$/.test(line)) {
      flushParagraph();
      flushList();
      output.push('<hr class="rich-divider">');
      continue;
    }

    const listMatch = line.match(/^(\s*)([-*•▪◦]|\d+[.)])\s+(.+)$/);
    if (listMatch) {
      flushParagraph();
      const ordered = /^\d/.test(listMatch[2]);
      if (listItems.length && listItems[0].ordered !== ordered) flushList();
      listItems.push({
        ordered,
        depth: Math.floor(listMatch[1].replace(/\t/g, "  ").length / 2),
        text: listMatch[3]
      });
      continue;
    }

    const quote = line.match(/^\s*>\s?(.*)$/);
    if (quote) {
      flushParagraph();
      flushList();
      output.push(`<blockquote class="rich-quote">${renderInline(quote[1])}</blockquote>`);
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }

    flushList();
    paragraph.push(line.trim());
  }

  if (inCode) flushCode();
  flushParagraph();
  flushList();
  return output.join("") || '<p class="rich-paragraph">No content available yet.</p>';
}

function extractSummarySections(source) {
  const lines = String(source ?? "").replace(/\r\n?/g, "\n").split("\n");
  const sections = [];
  let inFence = false;
  for (const line of lines) {
    // Lines inside ``` fences are code, not headings or list items (the renderer skips them too).
    if (/^\s*```/.test(line)) { inFence = !inFence; continue; }
    if (inFence) continue;
    const heading = line.match(/^#{1,3}\s+(.+)$/);
    if (heading) {
      sections.push(heading[1].replace(/\*\*/g, "").replace(/`/g, "").trim());
      continue;
    }
    const item = line.match(/^(\s*)(?:[-*•▪◦]|\d+[.)])\s+(.+)$/);
    if (!item || item[1].replace(/\t/g, "  ").length >= 2) continue;
    const boldLead = item[2].match(/^\*\*(.+?)\*\*/);
    const label = (boldLead ? boldLead[1] : item[2]).replace(/`/g, "").replace(/\*\*/g, "").replace(/\s+[–—:-].*$/, "").trim();
    if (label) sections.push(label);
  }
  return sections.slice(0, 8);
}

async function copyText(text, successMessage = "Copied to clipboard") {
  try {
    await navigator.clipboard.writeText(String(text ?? ""));
    toast(successMessage);
  } catch {
    const field = document.createElement("textarea");
    field.value = String(text ?? "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.append(field);
    field.select();
    const copied = document.execCommand("copy");
    field.remove();
    toast(copied ? successMessage : "Copy is unavailable in this browser");
  }
}
const fmt = (d) => (d ? new Date(d).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "");
const sid = store.get("sid") || (() => { const v = Math.random().toString(36).slice(2, 14); store.set("sid", v); return v; })();
let current = store.get("lecture") || null;
let lectures = [];
let serverOnline = false;
let pendingWorkspaceTab = null;
let pendingSearch = "";
let pendingChatPrompt = null;
const chats = {};

async function api(path, opts = {}) {
  const res = await fetch(API + "/api" + path, opts);
  if (!res.ok) {
    let d = res.statusText;
    try { const j = await res.json(); d = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail || d); } catch {}
    throw new Error(d);
  }
  return res.json();
}
const send = (method, path, body) => api(path, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
const post = (p, b) => send("POST", p, b);

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toast.t);
  toast.t = setTimeout(() => t.classList.remove("show"), 3500);
}

// Theme
const root = document.documentElement;
const themeBtn = $("#theme");
const themeBtnMobile = $("#themeMobile");
const syncTheme = () => {
  const dark = root.classList.contains("dark");
  const next = dark ? "Light appearance" : "Dark appearance";
  $(".theme-label").textContent = next;
  themeBtn.querySelector("[data-icon]").innerHTML = ico(dark ? "sun" : "moon");
  themeBtn.setAttribute("aria-pressed", dark ? "true" : "false");
  themeBtnMobile.querySelector("[data-icon]").innerHTML = ico(dark ? "sun" : "moon");
  themeBtnMobile.setAttribute("aria-pressed", dark ? "true" : "false");
  themeBtnMobile.setAttribute("aria-label", "Switch to " + next.toLowerCase());
};
if (store.get("theme") === "dark") root.classList.add("dark");
syncTheme();
const toggleTheme = () => {
  root.classList.toggle("dark");
  store.set("theme", root.classList.contains("dark") ? "dark" : "light");
  syncTheme();
};
themeBtn.onclick = toggleTheme;
themeBtnMobile.onclick = toggleTheme;
$("#year").textContent = new Date().getFullYear();
$("#notify").onclick = () => toast("You're all caught up. Your latest study materials appear here after processing.");
const searchBox = $(".global-search");
const searchInput = $("#globalSearch");
const searchToggle = $("#searchToggle");
const closeSearch = () => searchBox.classList.remove("open");
// On phones the input is collapsed to an icon; tapping the icon opens it as an overlay.
searchToggle.addEventListener("click", () => {
  searchBox.classList.add("open");
  searchInput.focus();
});
searchInput.addEventListener("blur", () => setTimeout(closeSearch, 150));
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Escape") { closeSearch(); searchToggle.focus(); return; }
  if (e.key !== "Enter" || e.isComposing) return;
  pendingSearch = e.currentTarget.value.trim();
  closeSearch();
  e.currentTarget.blur();
  if (location.hash.startsWith("#/lectures")) viewLibrary();
  else location.hash = "#/lectures";
});

// Router
let routeSeq = 0;
async function route() {
  const seq = ++routeSeq; // a newer navigation invalidates this one
  const [, page = "dashboard", id] = location.hash.split("/");
  document.querySelector(".app")?.classList.toggle("workspace-mode", page === "workspace");
  const labels = { dashboard: "Overview", lectures: "My Lectures", workspace: "Study Workspace" };
  $("#top-page").textContent = labels[page] || "Overview";
  document.querySelectorAll("#nav a").forEach((a) => a.classList.toggle("on", a.dataset.r === page));
  if (id) { current = id; store.set("lecture", id); }
  let loadError = null;
  try {
    const data = await api("/lectures");
    if (seq !== routeSeq) return; // user already navigated somewhere else
    lectures = data;
    serverOnline = true;
  } catch (e) {
    if (seq !== routeSeq) return;
    lectures = [];
    serverOnline = false;
    loadError = e.message || "Unknown error";
  }
  if (loadError) {
    $("#view").innerHTML = `<section class="load-error" role="alert"><h2>We couldn't load your lectures</h2><p>${esc(loadError)}</p><button type="button" class="btn" id="retry-load">Try again</button></section>`;
    $("#retry-load").onclick = () => route();
    renderInfo();
    $("#nav-count").textContent = "–";
    return;
  }
  const views = { dashboard: viewDashboard, lectures: viewLibrary, workspace: viewWorkspace };
  (views[page] || viewDashboard)();
  renderInfo();
  $("#nav-count").textContent = lectures.length;
}
window.addEventListener("hashchange", route);

function renderInfo() {
  const lec = lectures.find((l) => l.id === current);
  const totalChunks = lectures.reduce((sum, l) => sum + (Number(l.num_chunks) || 0), 0);
  const date = new Date().toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  $("#info").innerHTML = `
    <div class="info-head"><h2>Your study space</h2><span class="info-date">${esc(date)}</span></div>
    <section class="info-card">
      <div class="info-label">Current session</div>
      ${lec ? `
        <div class="info-lecture-title">${esc(lec.title)}</div>
        <div class="info-lecture-stats">
          <span class="info-pill">${ico("layers")} ${Number(lec.num_chunks) || 0} chunks</span>
          <span class="info-pill">${ico("calendar-days")} ${esc(fmt(lec.created_at) || "Saved lecture")}</span>
        </div>
        <a class="btn btn-sm" href="#/workspace/${encodeURIComponent(lec.id)}">Open workspace ${ico("arrow-right")}</a>
      ` : `
        <div class="current-lecture-empty"><div class="blank-art">${ico("book-open")}</div><div><strong>No lecture selected yet</strong><p>Choose a lecture to start chatting, revising or practising.</p></div></div>
        <a class="text-link" href="#/lectures" style="margin-top:13px">Browse my lectures ${ico("arrow-right")}</a>
      `}
    </section>
    <section class="info-card">
      <div class="info-kicker"><span class="info-kicker-icon">${ico("compass")}</span><span><strong>A simple study flow</strong><small>Make the most of each lecture</small></span></div>
      <div class="study-steps">
        <div class="study-step"><span class="step-no">01</span><div><strong>Review the key ideas</strong><p>Start with a lecture summary to see the big picture.</p></div></div>
        <div class="study-step"><span class="step-no">02</span><div><strong>Ask better questions</strong><p>Use AI chat to clarify concepts from your material.</p></div></div>
        <div class="study-step"><span class="step-no">03</span><div><strong>Test your memory</strong><p>Finish with a short quiz and revisit weak topics.</p></div></div>
      </div>
    </section>
    <section class="info-card tip-card">
      <div class="tip-top">${ico("lightbulb")} Study tip</div>
      <p>Try explaining one idea in your own words before checking the summary. It helps reveal what you understand and what to review next.</p>
    </section>
    <section class="info-card">
      <div class="info-label">Your lecture library</div>
      <div class="library-health"><div><strong>${lectures.length}</strong><div><span>saved lecture${lectures.length === 1 ? "" : "s"}</span></div></div><div style="text-align:right"><strong>${totalChunks}</strong><div><span>indexed chunks</span></div></div></div>
      <div class="server-status ${serverOnline ? "" : "offline"}" style="margin-top:13px"><span class="status-dot"></span><span>${serverOnline ? "Study library connected" : "Waiting for API connection"}</span></div>
    </section>`;
}

function lectureList(items, manage = false) {
  if (!items.length) return `<p class="empty">No lectures here yet. Upload one from the dashboard to get started.</p>`;
  return `<ul class="lecs">${items.map((l) => `<li class="lec"><div><b>${esc(l.title)}</b><small>${l.num_chunks} chunk${l.num_chunks === 1 ? "" : "s"}, added ${fmt(l.created_at)}</small></div><div class="acts"><a class="btn sm" href="#/workspace/${esc(l.id)}">Open</a>${manage ? `<button class="ghost sm" data-ren="${esc(l.id)}">Rename</button><button class="ghost sm danger" data-del="${esc(l.id)}">Delete</button>` : ""}</div></li>`).join("")}</ul>`;
}

// Dashboard + processing
function viewDashboard() {
  const ordered = [...lectures].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
  const latest = ordered[0];
  const totalChunks = lectures.reduce((sum, l) => sum + (Number(l.num_chunks) || 0), 0);
  const today = new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
  const recent = ordered.slice(0, 3);
  const continueBlock = latest ? `
    <article class="continue-card">
      <div class="continue-main">
        <div class="lecture-cover">${ico("book-open")}</div>
        <div class="lecture-info">
          <div class="lecture-kicker">PICK UP WHERE YOU LEFT OFF</div>
          <h3>${esc(latest.title)}</h3>
          <div class="lecture-meta"><span>${Number(latest.num_chunks) || 0} indexed chunks</span><span class="bullet"></span><span>Added ${esc(fmt(latest.created_at) || "recently")}</span></div>
        </div>
      </div>
      <div class="continue-actions"><a class="btn btn-sm" href="#/workspace/${encodeURIComponent(latest.id)}">Continue learning ${ico("arrow-right")}</a></div>
    </article>` : `
    <div class="empty-state">
      <div class="empty-icon">${ico("book-open")}</div>
      <div><h3>Your next learning session starts here</h3><p>Add your first lecture to unlock AI chat, summaries and practice quizzes.</p></div>
      <button type="button" class="btn btn-sm" id="empty-upload">${ico("plus")} Add a lecture</button>
    </div>`;
  const recentBlock = recent.length ? `<div class="recent-list">${recent.map((l) => `
    <a class="recent-row" href="#/workspace/${encodeURIComponent(l.id)}">
      <span class="recent-mini-icon">${ico("file-text")}</span>
      <span class="recent-row-copy"><strong>${esc(l.title)}</strong><small>${Number(l.num_chunks) || 0} chunks · Added ${esc(fmt(l.created_at) || "recently")}</small></span>
      <span class="recent-open">${ico("arrow-up-right")}</span>
    </a>`).join("")}</div>` : `<div class="recent-empty">Your saved lectures will appear here after you process one.</div>`;

  $("#view").innerHTML = `
    <div class="page-head">
      <div><div class="eyebrow">YOUR PERSONAL LEARNING HUB</div><h1>Welcome back, learner <span aria-hidden="true">✦</span></h1><p>Small steps today. Strong understanding tomorrow.</p></div>
      <div class="today-label">${ico("calendar-days")} ${esc(today)}</div>
    </div>
    <section class="welcome-hero">
      <div class="hero-copy">
        <div class="hero-tag">${ico("sparkles")} YOUR STUDY SPACE, SUPERCHARGED</div>
        <h1>Make today a little smarter.</h1>
        <p>Turn class recordings into clear notes, ask questions about your lectures, and check what you have learned — all in one place.</p>
        <div class="hero-actions">
          <button type="button" class="btn btn-white" id="choose-file">${ico("upload")} Add a lecture</button>
          <a href="#/lectures" class="btn btn-translucent">Explore library ${ico("arrow-up-right")}</a>
        </div>
        <input type="file" id="file" accept="video/*,audio/*" hidden>
      </div>
      <div class="hero-art" aria-hidden="true"><div class="art-glow"></div><div class="study-illustration"><div class="book"><span></span><span></span><span></span><span></span><span></span></div><div class="mini-card check">${ico("check-circle")}</div><div class="mini-card spark">${ico("sparkles")}</div><div class="pencil"></div></div></div>
    </section>
    <section id="picked-card" class="info-card picked-upload" hidden>
      <div class="picked-file-icon">${ico("file-text")}</div><div class="picked-file-copy"><strong id="fname">Selected lecture</strong><small id="file-detail">Ready to process</small></div>
      <button type="button" id="up" class="btn btn-sm">Process lecture ${ico("arrow-right")}</button><button type="button" id="cancel-file" class="ghost">Cancel</button>
    </section>
    <div id="ytrow" class="youtube-row" hidden><input id="yt" type="url" placeholder="Paste a YouTube lecture URL" aria-label="YouTube lecture URL"><button type="button" class="btn btn-sm" id="ytb">Process link ${ico("arrow-right")}</button></div>
    <div class="upload-options"><span id="hint">Audio files (MP3, M4A) are smaller and work best.</span><button type="button" id="youtube-toggle" class="text-link" hidden>Use a YouTube link ${ico("arrow-up-right")}</button></div>
    <section id="reference-card" class="reference-upload-card" hidden>
      <div class="reference-upload-copy"><div class="reference-upload-heading">${ico("book-open")} <strong>Have notes or documents from your lecturer?</strong> <span>Optional, but recommended</span></div><p>Add lecture slides, handouts, or class notes so answers, summaries, and detailed notes can use both the recording and the lecturer's material.</p><small id="reference-files-detail">PDF, DOCX, PPTX, TXT or Markdown · Up to 5 files</small></div>
      <input type="file" id="reference-files" accept=".pdf,.docx,.pptx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation,text/plain,text/markdown" multiple hidden>
      <button type="button" class="btn btn-sm" id="choose-reference-files">${ico("upload")} Add lecturer files</button>
    </section>
    <section id="prog" class="processing-card" hidden><div class="processing-heading"><span class="processing-spinner"></span><div><strong>Preparing your study workspace</strong><p id="stage">Uploading...</p></div></div><div class="bar"><i id="barfill"></i></div></section>

    <section class="metrics-grid" aria-label="Study library statistics">
      <article class="metric-card"><div class="metric-icon purple">${ico("library")}</div><div class="metric-copy"><div class="metric-label">Saved lectures</div><div class="metric-value">${lectures.length}</div><div class="metric-foot">${lectures.length ? "Ready when you are" : "Your library starts here"}</div></div></article>
      <article class="metric-card"><div class="metric-icon mint">${ico("layers")}</div><div class="metric-copy"><div class="metric-label">Knowledge chunks</div><div class="metric-value">${totalChunks.toLocaleString()}</div><div class="metric-foot">Searchable lecture passages</div></div></article>
      <article class="metric-card"><div class="metric-icon peach">${ico("brain")}</div><div class="metric-copy"><div class="metric-label">Study tools</div><div class="metric-value">5</div><div class="metric-foot">Chat, summary, detailed notes, quiz and evaluation</div></div></article>
    </section>

    <section class="section-block">
      <div class="section-head"><div class="section-title-wrap"><h2>Continue learning</h2><p>Jump back into a lecture and keep your momentum.</p></div>${lectures.length ? `<a href="#/lectures" class="text-link">All lectures ${ico("arrow-right")}</a>` : ""}</div>
      ${continueBlock}
    </section>

    <section class="section-block">
      <div class="section-head"><div class="section-title-wrap"><h2>Your learning toolkit</h2><p>Choose the next step that works for you.</p></div></div>
      <div class="tool-grid">
        <button class="tool-card" type="button" data-tool-tab="Chat"><span class="tool-icon chat">${ico("message-circle")}</span><span class="tool-title">Ask your lecture</span><span class="tool-desc">Get answers grounded in your study material.</span><span class="tool-arrow">${ico("arrow-up-right")}</span></button>
        <button class="tool-card" type="button" data-tool-tab="Summary"><span class="tool-icon notes">${ico("file-text")}</span><span class="tool-title">Smart summaries</span><span class="tool-desc">Review the main ideas in less time.</span><span class="tool-arrow">${ico("arrow-up-right")}</span></button>
        <button class="tool-card" type="button" data-tool-tab="Quiz"><span class="tool-icon quiz">${ico("clipboard-check")}</span><span class="tool-title">Practice quiz</span><span class="tool-desc">Check understanding with generated questions.</span><span class="tool-arrow">${ico("arrow-up-right")}</span></button>
        <button class="tool-card" type="button" data-tool-tab="Evaluation"><span class="tool-icon eval">${ico("compass")}</span><span class="tool-title">Evaluate answers</span><span class="tool-desc">Test answers against expected responses.</span><span class="tool-arrow">${ico("arrow-up-right")}</span></button>
      </div>
    </section>

    <section class="section-block">
      <div class="section-head"><div class="section-title-wrap"><h2>Recently added</h2><p>Your latest learning materials, all in one place.</p></div><a href="#/lectures" class="text-link">Open library ${ico("arrow-right")}</a></div>
      ${recentBlock}
    </section>`;

  const fileInput = $("#file");
  const referenceInput = $("#reference-files");
  const pickedCard = $("#picked-card");
  const referenceCard = $("#reference-card");
  const choose = () => fileInput.click();
  let maxReferenceMB = 15;
  let maxReferenceFiles = 5;
  const syncReferenceCard = () => {
    referenceCard.hidden = !fileInput.files.length && $("#ytrow").hidden;
  };
  const selectedReferenceFiles = () => Array.from(referenceInput.files || []);
  const addReferencesToForm = (form) => selectedReferenceFiles().forEach((item) => form.append("reference_files", item));
  $("#choose-file").onclick = choose;
  $("#empty-upload")?.addEventListener("click", choose);
  fileInput.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) { pickedCard.hidden = true; syncReferenceCard(); return; }
    $("#fname").textContent = file.name;
    $("#file-detail").textContent = `${(file.size / 1048576).toFixed(1)} MB · Ready to process`;
    pickedCard.hidden = false;
    syncReferenceCard();
    pickedCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };
  $("#cancel-file").onclick = () => {
    fileInput.value = "";
    pickedCard.hidden = true;
    if ($("#ytrow").hidden) { referenceInput.value = ""; $("#reference-files-detail").textContent = "PDF, DOCX, PPTX, TXT or Markdown · Up to 5 files"; }
    syncReferenceCard();
  };
  $("#choose-reference-files").onclick = () => referenceInput.click();
  referenceInput.onchange = () => {
    const files = selectedReferenceFiles();
    if (files.length > maxReferenceFiles) {
      referenceInput.value = "";
      $("#reference-files-detail").textContent = `Choose at most ${maxReferenceFiles} files.`;
      return toast(`Add no more than ${maxReferenceFiles} lecturer files.`);
    }
    const tooLarge = files.find((item) => item.size > maxReferenceMB * 1048576);
    if (tooLarge) {
      referenceInput.value = "";
      $("#reference-files-detail").textContent = `Each lecturer file must be ${maxReferenceMB} MB or smaller.`;
      return toast(`"${tooLarge.name}" is larger than ${maxReferenceMB} MB.`);
    }
    const totalSize = files.reduce((total, item) => total + item.size, 0);
    const sourceSize = $("#ytrow").hidden ? (fileInput.files[0]?.size || 0) : 0;
    if (sourceSize + totalSize > maxMB * 1048576) {
      referenceInput.value = "";
      $("#reference-files-detail").textContent = `The combined upload must be ${maxMB} MB or smaller.`;
      return toast(`The lecture and lecturer files together must stay under ${maxMB} MB.`);
    }
    $("#reference-files-detail").textContent = files.length
      ? `${files.length} file${files.length === 1 ? "" : "s"} selected · ${(totalSize / 1048576).toFixed(1)} MB · ${files.map((item) => item.name).join(", ")}`
      : "PDF, DOCX, PPTX, TXT or Markdown · Up to 5 files";
  };

  let maxMB = 200;
  api("/health").then((h) => {
    maxMB = h.max_upload_mb || maxMB;
    maxReferenceMB = h.max_reference_file_mb || maxReferenceMB;
    maxReferenceFiles = h.max_reference_files || maxReferenceFiles;
    const yt = h.youtube_enabled !== false;
    $("#youtube-toggle").hidden = !yt;
    $("#reference-files-detail").textContent = `PDF, DOCX, PPTX, TXT or Markdown · Up to ${maxReferenceFiles} files, ${maxReferenceMB} MB each`;
    $("#hint").textContent = `Combined upload up to ${maxMB} MB. Audio files (MP3, M4A) are smaller and work best.` +
      (yt ? " You can also add a YouTube lecture link." : " YouTube links are disabled on this server; upload the audio or video file instead.");
  }).catch(() => {});
  $("#youtube-toggle").onclick = () => {
    $("#ytrow").hidden = !$("#ytrow").hidden;
    syncReferenceCard();
    if (!$("#ytrow").hidden) $("#yt").focus();
  };
  $("#up").onclick = () => {
    const f = fileInput.files[0];
    if (!f) return toast("Choose a file first");
    if (f.size > maxMB * 1048576) return toast(`That file is over ${maxMB} MB. Extract the audio (MP3) and upload that instead.`);
    const fd = new FormData();
    fd.append("file", f);
    const references = selectedReferenceFiles();
    if (references.some((item) => item.size > maxReferenceMB * 1048576)) return toast(`Each lecturer file must be ${maxReferenceMB} MB or smaller.`);
    if (f.size + references.reduce((total, item) => total + item.size, 0) > maxMB * 1048576) return toast(`The lecture and lecturer files together must stay under ${maxMB} MB.`);
    addReferencesToForm(fd);
    track(fetch(API + "/api/lectures/upload", { method: "POST", body: fd }));
  };
  $("#ytb").onclick = () => {
    const url = $("#yt").value.trim();
    if (!url) return toast("Paste a YouTube link first");
    const references = selectedReferenceFiles();
    if (references.some((item) => item.size > maxReferenceMB * 1048576)) return toast(`Each lecturer file must be ${maxReferenceMB} MB or smaller.`);
    if (references.reduce((total, item) => total + item.size, 0) > maxMB * 1048576) return toast(`Lecturer files together must stay under ${maxMB} MB.`);
    const fd = new FormData();
    fd.append("url", url);
    addReferencesToForm(fd);
    track(fetch(API + "/api/lectures/youtube", { method: "POST", body: fd }));
  };
  document.querySelectorAll("[data-tool-tab]").forEach((button) => {
    button.onclick = () => {
      const tab = button.dataset.toolTab;
      const target = lectures.find((l) => l.id === current) || latest;
      if (!target) return toast("Add or choose a lecture first to use this study tool.");
      pendingWorkspaceTab = tab;
      const targetHash = `#/workspace/${encodeURIComponent(target.id)}`;
      if (location.hash === targetHash) route();
      else location.hash = targetHash;
    };
  });
}

async function track(request) {
  $("#prog").hidden = false;
  $("#stage").className = "";
  $("#stage").textContent = "Uploading...";
  $("#barfill").style.width = "3%";
  const btns = document.querySelectorAll("#picked-card .btn, #ytb, #choose-file, #choose-reference-files");
  btns.forEach((b) => (b.disabled = true));
  let finished = false;
  try {
    const res = await request;
    if (!res.ok) {
      let d = res.statusText;
      try { const j = await res.json(); if (typeof j.detail === "string") d = j.detail; } catch {}
      throw new Error(res.status === 413 ? "That file is too large for this server. Upload a smaller or audio-only file." : d);
    }
    // The server keeps this request open and streams one JSON line per progress update.
    const reader = res.body.getReader(), dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();
      for (const ln of lines.filter(Boolean)) {
        const j = JSON.parse(ln);
        if (!$("#stage")) return; // user left the page; the server keeps going
        $("#stage").textContent = j.status === "queued" ? "Waiting for the server to start..." : `${j.stage} · step ${j.step} of ${j.total}`;
        $("#barfill").style.width = (j.step / j.total) * 100 + "%";
        if (j.status === "error") throw new Error(j.error);
        if (j.status === "done") {
          finished = true;
          const warnings = Array.isArray(j.warnings) ? j.warnings : [];
          toast(warnings.length ? `Workspace ready. ${warnings.length} lecturer-file warning${warnings.length === 1 ? "" : "s"}: ${String(warnings[0]).slice(0, 110)}` : "Workspace ready");
          location.hash = "#/workspace/" + j.lecture_id;
          return;
        }
      }
    }
    if (!finished) throw new Error("The connection closed before processing finished. Check My Lectures in a minute, or try again.");
  } catch (e) {
    if ($("#stage")) { $("#stage").textContent = e.message; $("#stage").className = "err"; }
  } finally {
    btns.forEach((b) => (b.disabled = false));
  }
}

// Library
function viewLibrary() {
  $("#view").innerHTML = `<h1>My lectures</h1><input id="q" class="search" placeholder="Search by title" aria-label="Search lectures"><div id="list"></div>`;
  if (pendingSearch) { $("#q").value = pendingSearch; pendingSearch = ""; }
  const draw = () => {
    const q = $("#q").value.toLowerCase();
    $("#list").innerHTML = lectureList(lectures.filter((l) => l.title.toLowerCase().includes(q)), true);
  };
  $("#q").oninput = draw;
  draw();
  $("#list").onclick = async (e) => {
    const { ren, del } = e.target.dataset;
    try {
      if (ren) {
        const t = prompt("New title", lectures.find((l) => l.id === ren)?.title);
        if (t && t.trim()) { await send("PATCH", "/lectures/" + ren, { title: t.trim() }); route(); }
      }
      if (del && confirm("Delete this lecture and its search index? This can't be undone.")) {
        await send("DELETE", "/lectures/" + del);
        store.remove(chatKey(del));
        delete chats[del];
        if (current === del) { current = null; store.remove("lecture"); }
        route();
      }
    } catch (err) { toast(err.message); }
  };
}

// Workspace
function viewWorkspace() {
  const lec = lectures.find((l) => l.id === current);
  if (!lec) {
    $("#view").innerHTML = `<div class="workspace-empty"><div class="workspace-empty-icon">${ico("brain")}</div><div class="eyebrow">YOUR LEARNING SPACE</div><h1>Study workspace</h1><p>Open a lecture from your library to chat with your materials, create focused notes, or practise what you've learned.</p><a class="btn" href="#/lectures">Browse my lectures ${ico("arrow-right")}</a></div>`;
    return;
  }
  const tabs = { Chat: tabChat, Summary: tabSummary, "Detailed Notes": tabDetailedNotes, Quiz: tabQuiz, Evaluation: tabEval };
  const tabIcons = { Chat: "message-circle", Summary: "file-text", "Detailed Notes": "book-open", Quiz: "clipboard-check", Evaluation: "file-check" };
  $("#view").innerHTML = `
    <div class="workspace-page-head">
      <div class="workspace-title-group">
        <div class="eyebrow">YOUR LEARNING SPACE</div>
        <h1>${esc(lec.title)}</h1>
        <p>Ask questions, turn concepts into clear notes, and check your understanding.</p>
      </div>
      <a class="workspace-back" href="#/lectures">${ico("library")} <span>All lectures</span></a>
    </div>
    <div class="tabs workspace-tabs" role="tablist" aria-label="Study tools">${Object.keys(tabs).map((t) => `<button role="tab" aria-selected="false" data-tab="${t}"><span class="workspace-tab-icon">${ico(tabIcons[t])}</span><span>${t === "Evaluation" ? "Answer evaluation" : t}</span></button>`).join("")}</div>
    <div id="tab" class="workspace-tab-panel"></div>`;
  const panel = $("#tab");
  let tabSeq = 0;
  const show = (t) => {
    const token = ++tabSeq;
    document.querySelectorAll(".workspace-tabs button").forEach((b) => {
      const active = b.dataset.tab === t;
      b.classList.toggle("on", active);
      b.setAttribute("aria-selected", active ? "true" : "false");
    });
    // Tabs call alive() after any await; it is false once the user switched tab or left the page.
    const alive = () => token === tabSeq && panel.isConnected;
    tabs[t](panel, alive);
  };
  document.querySelector(".workspace-tabs").onclick = (e) => {
    const button = e.target.closest("[data-tab]");
    if (button) show(button.dataset.tab);
  };
  const initialTab = pendingWorkspaceTab || "Chat";
  pendingWorkspaceTab = null;
  show(initialTab);
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------
const CHAT_STORE_LIMIT = 40;          // messages kept per lecture in the browser
const chatKey = (id) => "chat:" + id;
const streams = {};                   // lectureId -> { controller, answer } while an answer is streaming
const chatViews = {};                 // lectureId -> currently mounted chat view
const liveView = (id) => { const v = chatViews[id]; return v && v.box.isConnected ? v : null; };

function loadChat(id) {
  if (chats[id]) return chats[id];
  let list = [];
  try {
    const parsed = JSON.parse(store.get(chatKey(id)) || "[]");
    if (Array.isArray(parsed)) {
      list = parsed.filter((m) => m && (m.role === "you" || m.role === "ai")).map((m) => ({
        role: m.role,
        text: String(m.text || ""),
        sources: Array.isArray(m.sources) ? m.sources : [],
        error: m.error || null,
        status: m.status || "done",
        question: m.question || ""
      }));
    }
  } catch {}
  // A page refresh mid-answer leaves a "streaming" message that can never finish.
  list.forEach((m) => {
    if (m.role === "ai" && m.status === "streaming") {
      if (m.text) m.status = "stopped";
      else { m.status = "error"; m.error = "This answer was interrupted. Try again."; }
    }
  });
  return (chats[id] = list);
}

function saveChat(id) {
  const log = chats[id];
  if (!log) return;
  if (!log.length) { store.remove(chatKey(id)); return; }
  let tail = log.slice(-CHAT_STORE_LIMIT);
  if (tail[0] && tail[0].role === "ai") tail = tail.slice(1); // never start mid-exchange
  store.set(chatKey(id), JSON.stringify(tail.map(({ role, text, sources, error, status, question }) => ({ role, text, sources, error, status, question }))));
}

const plainText = (md) => String(md || "").replace(/```[\s\S]*?```/g, " code block ").replace(/[`*_#>|]/g, "").replace(/\s+/g, " ").trim();

const THINKING_HTML = '<div class="thinking-state"><span></span><span></span><span></span><em>Finding an answer in your lecture…</em></div>';
const messageContentHtml = (m) => m.text ? renderRichText(m.text) : (m.status === "streaming" ? THINKING_HTML : "");
const messageSourcesHtml = (m) => m.sources?.length ? `
  <details class="source-panel">
    <summary><span class="source-summary-icon">${ico("book-open")}</span><span><strong>Sources from your lecture</strong><small>${m.sources.length} supporting passage${m.sources.length === 1 ? "" : "s"}</small></span><span class="source-chevron">${ico("chevron-down")}</span></summary>
    <div class="source-list">${m.sources.map((source, sourceIndex) => `<article class="source-item"><div class="source-item-head"><span>PASSAGE ${String(sourceIndex + 1).padStart(2, "0")}</span>${source.time ? `<b>${ico("clock")} ${esc(source.time)}</b>` : ""}</div><p>${esc(source.text)}</p></article>`).join("")}</div>
  </details>` : "";
const messageErrorHtml = (m, index, canRetry) => {
  if (m.role !== "ai" || (m.status !== "error" && m.status !== "stopped")) return "";
  const stopped = m.status === "stopped";
  const note = stopped ? (m.text ? "Answer stopped. What you see is only part of the answer." : "Stopped before an answer arrived.") : (m.error || "Something went wrong while generating the answer.");
  const retry = canRetry ? `<button type="button" class="message-retry" data-retry="${index}">Try again</button>` : "";
  return `<div class="message-error${stopped ? " is-note" : ""}" role="${stopped ? "status" : "alert"}">${ico("circle-help")}<span>${esc(note)}</span>${retry}</div>`;
};
const messageToolsHtml = (m, index) => m.role === "ai" && m.text && m.status !== "streaming"
  ? `<div class="message-tools"><button type="button" class="message-tool" data-copy-answer="${index}">${ico("clipboard-check")} Copy answer</button></div>` : "";

const msgHtml = (m, index, log) => {
  const isUser = m.role === "you";
  const canRetry = index === log.length - 1;
  return `<article class="chat-message ${isUser ? "is-user" : "is-assistant"}" data-i="${index}">
    <div class="chat-avatar ${isUser ? "user-avatar" : "assistant-avatar"}">${isUser ? '<span class="chat-user-mark">Y</span>' : ico("sparkles")}</div>
    <div class="chat-message-main">
      <div class="chat-message-meta"><strong>${isUser ? "You" : "Study assistant"}</strong>${!isUser ? '<span class="assistant-label">LECTURE-GROUNDED</span>' : ""}</div>
      <div class="chat-bubble ${isUser ? "user-bubble" : "assistant-bubble"}"><div class="rich-content">${messageContentHtml(m)}</div><div class="js-error">${messageErrorHtml(m, index, canRetry)}</div></div>
      <div class="js-sources">${messageSourcesHtml(m)}</div><div class="js-tools">${messageToolsHtml(m, index)}</div>
    </div>
  </article>`;
};

// Streams one answer into `answer`. Lives outside the tab so switching tabs doesn't cancel it.
async function streamAnswer(lectureId, answer) {
  const controller = new AbortController();
  streams[lectureId] = { controller, answer };
  answer.status = "streaming";
  answer.error = null;
  answer.text = "";
  answer.sources = [];
  liveView(lectureId)?.setBusy(true);

  let frame = 0;
  const paintText = () => {
    if (frame) return;
    frame = requestAnimationFrame(() => { frame = 0; liveView(lectureId)?.update(answer, { text: true }); });
  };
  let sawDone = false;
  const handle = (line) => {
    const ev = JSON.parse(line);
    if (ev.type === "sources") { answer.sources = ev.data || []; liveView(lectureId)?.update(answer, { sources: true }); }
    else if (ev.type === "token") { answer.text += ev.data; paintText(); }
    else if (ev.type === "error") throw new Error(ev.data);
    else if (ev.type === "done") sawDone = true;
  };

  try {
    const response = await fetch(`${API}/api/lectures/${lectureId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: answer.question, session_id: sid }),
      signal: controller.signal
    });
    if (!response.ok) {
      const j = await response.json().catch(() => ({}));
      throw new Error(typeof j.detail === "string" ? j.detail : response.statusText || "Request failed");
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      lines.filter(Boolean).forEach(handle);
    }
    if (buffer.trim()) handle(buffer);
    if (!sawDone) throw new Error("The connection closed before the answer finished.");
    answer.status = "done";
  } catch (error) {
    if (error.name === "AbortError" || controller.signal.aborted) {
      answer.status = "stopped";
    } else {
      answer.status = "error";
      answer.error = error.message || "Something went wrong while generating the answer.";
    }
  } finally {
    if (frame) cancelAnimationFrame(frame);
    if (streams[lectureId]?.controller === controller) delete streams[lectureId];
    saveChat(lectureId);
    const view = liveView(lectureId);
    if (view) {
      view.update(answer, { text: true, sources: true, footer: true });
      view.setBusy(false);
      view.announce(answer);
    }
  }
}

function tabChat(el) {
  const lectureId = current;
  const log = loadChat(lectureId);
  const lec = lectures.find((l) => l.id === lectureId);
  el.innerHTML = `
    <section class="chat-workspace">
      <header class="chat-workspace-header">
        <div class="chat-header-symbol">${ico("message-circle")}</div>
        <div class="chat-header-copy"><h2>Ask your lecture</h2><p>Get clear answers backed by the material you uploaded.</p></div>
        <div class="chat-grounding-badge"><span></span> Based on this lecture</div>
      </header>
      <div id="log" class="log polished-chat-log" role="log" aria-live="off" aria-label="Conversation"></div>
      <div id="chatStatus" class="sr-only" role="status" aria-live="polite"></div>
      <form id="ask" class="ask polished-composer">
        <div class="composer-box">
          <textarea id="q" rows="1" placeholder="Ask anything about this lecture…" autocomplete="off" maxlength="2000" aria-label="Your question"></textarea>
          <div class="composer-footer"><span>${ico("book-open")} Answers are based on <b>${esc(lec?.title || "your lecture")}</b></span><div class="composer-actions"><button type="button" class="ghost stop-message" id="stopAnswer" hidden>Stop</button><button class="btn send-message" id="sendQuestion" type="submit">Send question ${ico("arrow-up-right")}</button></div></div>
        </div>
        <button type="button" id="reset" class="new-chat-button">${ico("plus")} <span>New chat</span></button>
      </form>
      <p class="chat-disclaimer">AI can make mistakes. Check the linked lecture passages when accuracy matters.</p>
    </section>`;

  const box = el.querySelector("#log");
  const input = el.querySelector("#q");
  const form = el.querySelector("#ask");
  const sendButton = el.querySelector("#sendQuestion");
  const stopButton = el.querySelector("#stopAnswer");
  const statusEl = el.querySelector("#chatStatus");

  const nearBottom = () => box.scrollHeight - box.scrollTop - box.clientHeight < 80;
  const toBottom = () => { box.scrollTop = box.scrollHeight; };
  const articleFor = (m) => { const i = log.indexOf(m); return i < 0 ? null : box.querySelector(`article[data-i="${i}"]`); };

  const emptyState = () => `
    <div class="chat-empty-state">
      <div class="chat-empty-art"><span>${ico("sparkles")}</span><i></i><b></b></div>
      <div class="chat-empty-eyebrow">START A CONVERSATION</div>
      <h3>What would you like to understand?</h3>
      <p>Choose a prompt to get started, or write your own question below.</p>
      <div class="prompt-suggestions">
        <button type="button" data-prompt="Explain the key concepts in this lecture in simple terms."><span class="suggestion-icon">${ico("lightbulb")}</span><span class="suggestion-copy"><strong>Explain a concept</strong><small>Simple language, step by step</small></span>${ico("arrow-up-right", "suggestion-arrow")}</button>
        <button type="button" data-prompt="Give me a practical example from this lecture."><span class="suggestion-icon">${ico("compass")}</span><span class="suggestion-copy"><strong>Show an example</strong><small>Connect theory to practice</small></span>${ico("arrow-up-right", "suggestion-arrow")}</button>
        <button type="button" data-prompt="What are the most important points I should remember from this lecture?"><span class="suggestion-icon">${ico("book-mark")}</span><span class="suggestion-copy"><strong>Revise key points</strong><small>Focus on what matters most</small></span>${ico("arrow-up-right", "suggestion-arrow")}</button>
      </div>
    </div>`;

  // Full render: only on mount and "New chat". Streaming never goes through here.
  const drawAll = () => {
    box.innerHTML = log.length ? log.map((m, i) => msgHtml(m, i, log)).join("") : emptyState();
    toBottom();
  };

  // The view other code (streamAnswer) talks to. It touches only the parts of the DOM that changed.
  const view = {
    box,
    update(m, parts) {
      const art = articleFor(m);
      if (!art) return;
      const i = log.indexOf(m);
      const stick = nearBottom();
      if (parts.text) art.querySelector(".rich-content").innerHTML = messageContentHtml(m);
      if (parts.sources) {
        const slot = art.querySelector(".js-sources");
        const count = String(m.sources?.length || 0);
        // Only rebuild when the set of sources changed, so an opened <details> stays open while streaming.
        if (slot.dataset.count !== count) { slot.innerHTML = messageSourcesHtml(m); slot.dataset.count = count; }
      }
      if (parts.footer) {
        art.querySelector(".js-error").innerHTML = messageErrorHtml(m, i, i === log.length - 1);
        art.querySelector(".js-tools").innerHTML = messageToolsHtml(m, i);
      }
      if (stick) toBottom();
    },
    replace(m) {
      const art = articleFor(m);
      if (!art) return;
      const i = log.indexOf(m);
      art.outerHTML = msgHtml(m, i, log);
    },
    refreshFooter(index) {
      const m = log[index];
      if (m) this.update(m, { footer: true });
    },
    setBusy(busy) {
      sendButton.hidden = busy;
      stopButton.hidden = !busy;
      box.setAttribute("aria-busy", busy ? "true" : "false");
    },
    // Screen readers hear one short message when an answer finishes, not every streamed token.
    announce(m) {
      let text = "";
      if (m.status === "done") text = "Answer ready. " + plainText(m.text).slice(0, 300);
      else if (m.status === "error") text = "The answer could not be completed. " + (m.error || "");
      else if (m.status === "stopped") text = "Answer stopped.";
      statusEl.textContent = "";
      setTimeout(() => { statusEl.textContent = text; }, 60);
    }
  };
  chatViews[lectureId] = view;

  drawAll();
  if (streams[lectureId]) view.setBusy(true); // an answer started before the tab was re-opened is still streaming

  const resize = () => { input.style.height = "auto"; input.style.height = `${Math.min(input.scrollHeight, 150)}px`; };
  if (pendingChatPrompt) { input.value = pendingChatPrompt; pendingChatPrompt = null; resize(); }
  input.addEventListener("input", resize);

  const touchDevice = window.matchMedia("(pointer: coarse)").matches;
  input.addEventListener("keydown", (event) => {
    // Ignore Enter that confirms an IME composition (Japanese, Chinese, Korean, etc.).
    if (event.isComposing || event.keyCode === 229) return;
    // On phones Enter inserts a newline; the Send button submits.
    if (event.key === "Enter" && !event.shiftKey && !touchDevice) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  // One delegated handler for everything clickable inside the log.
  box.addEventListener("click", (event) => {
    const copy = event.target.closest("[data-copy-answer]");
    if (copy) { copyText(log[Number(copy.dataset.copyAnswer)]?.text || "", "Answer copied"); return; }
    const retry = event.target.closest("[data-retry]");
    if (retry) {
      const i = Number(retry.dataset.retry);
      const m = log[i];
      if (!m || m.role !== "ai" || streams[lectureId] || i !== log.length - 1 || !m.question) return;
      m.text = ""; m.sources = []; m.error = null; m.status = "streaming";
      view.replace(m);
      toBottom();
      saveChat(lectureId);
      streamAnswer(lectureId, m);
      return;
    }
    const prompt = event.target.closest("[data-prompt]");
    if (prompt) { input.value = prompt.dataset.prompt; form.requestSubmit(); }
  });

  stopButton.onclick = () => { streams[lectureId]?.controller.abort(); };

  el.querySelector("#reset").onclick = async () => {
    streams[lectureId]?.controller.abort();
    log.length = 0;
    saveChat(lectureId);
    view.setBusy(false);
    drawAll();
    try { await post(`/lectures/${lectureId}/chat/reset?session_id=${sid}`); } catch {}
    input.focus();
  };

  form.onsubmit = (event) => {
    event.preventDefault();
    if (streams[lectureId]) return;
    const q = input.value.trim();
    if (!q) return;
    input.value = "";
    input.style.height = "auto";
    const previousLast = log.length - 1;
    const userMsg = { role: "you", text: q };
    const answer = { role: "ai", text: "", sources: [], question: q, status: "streaming" };
    log.push(userMsg, answer);
    if (previousLast >= 0) view.refreshFooter(previousLast); // older failed answers lose their Retry button
    if (previousLast < 0) box.innerHTML = "";               // clear the empty-state prompts
    box.insertAdjacentHTML("beforeend", msgHtml(userMsg, log.length - 2, log) + msgHtml(answer, log.length - 1, log));
    toBottom();                                              // your own message always scrolls into view
    saveChat(lectureId);
    streamAnswer(lectureId, answer);
    input.focus();
  };
}

function tabSummary(el, alive = () => true) {
  const lectureId = current;
  const lec = lectures.find((l) => l.id === lectureId);
  let loadSeq = 0;
  const load = async (refresh) => {
    const mine = ++loadSeq;
    const stale = () => mine !== loadSeq || !alive();
    el.innerHTML = `
      <section class="summary-loading-card">
        <div class="summary-loading-icon"><span class="processing-spinner"></span></div>
        <div><strong>${refresh ? "Refreshing your study notes" : "Preparing your study notes"}</strong><p>Organising the lecture into a clear, easy-to-review summary…</p></div>
        <div class="summary-skeleton"><i></i><i></i><i></i><i></i></div>
      </section>`;
    try {
      const { summary } = await api(`/lectures/${lectureId}/summary${refresh ? "?refresh=true" : ""}`);
      if (stale()) return;
      const text = String(summary || "").trim();
      const words = text ? text.match(/\S+/g).length : 0;
      const readingMinutes = Math.max(1, Math.ceil(words / 220));
      const sections = extractSummarySections(text);
      const outline = sections.length ? sections.map((name, index) => `<a href="#summary-section-${index + 1}" data-summary-target="summary-section-${index + 1}"><span>${String(index + 1).padStart(2, "0")}</span><b>${esc(name)}</b></a>`).join("") : `<a href="#summary-document" data-summary-target="summary-document"><span>01</span><b>Key ideas</b></a>`;
      el.innerHTML = `
        <section class="summary-page">
          <header class="summary-hero-card">
            <div class="summary-title-row">
              <div class="summary-title-icon">${ico("file-text")}</div>
              <div class="summary-title-copy"><div class="summary-kicker"><span></span> YOUR REVISION NOTES</div><h2>Lecture summary</h2><p>The key concepts, explained in a format that is easy to scan and revise.</p></div>
            </div>
            <div class="summary-actions"><button type="button" class="summary-action-button" id="copy-summary">${ico("clipboard-check")}<span>Copy notes</span></button><button type="button" class="summary-action-button" id="download-summary">${ico("download")}<span>Download .md</span></button><button type="button" class="btn" id="re">${ico("sparkles")} Refresh</button></div>
            <div class="summary-meta-row"><span>${ico("clock")} About ${readingMinutes} min read</span><i></i><span>${ico("layers")} ${words.toLocaleString()} words</span><i></i><span>${ico("book-open")} Lecture-based notes</span></div>
          </header>
          <div class="summary-reading-layout">
            <aside class="summary-outline-card"><div class="summary-outline-heading">IN THIS SUMMARY</div><nav class="summary-outline">${outline}</nav><div class="summary-outline-tip"><span>${ico("lightbulb")}</span><div><strong>Study tip</strong><p>Read one section, then try to explain the idea without looking at your notes.</p></div></div></aside>
            <article id="summary-document" class="summary-document">${renderRichText(text, { headingPrefix: "summary" })}</article>
          </div>
          <footer class="summary-bottom-card"><div class="summary-bottom-icon">${ico("message-circle")}</div><div class="summary-bottom-copy"><strong>Want to understand a concept more deeply?</strong><p>Ask the study assistant to explain a point or walk through an example from this lecture.</p></div><button type="button" class="ghost" id="discuss-summary">Discuss with AI ${ico("arrow-up-right")}</button></footer>
        </section>`;
      el.querySelectorAll("[data-summary-target]").forEach((link) => {
        link.addEventListener("click", (event) => {
          event.preventDefault();
          const target = el.querySelector(`[id="${link.dataset.summaryTarget}"]`);
          target?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      });
      el.querySelector("#copy-summary").onclick = () => copyText(text, "Summary copied");
      el.querySelector("#download-summary").onclick = () => {
        const safeTitle = String(lec?.title || "lecture").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toLowerCase() || "lecture";
        const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${safeTitle}-summary.md`;
        document.body.append(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        toast("Summary download started");
      };
      el.querySelector("#re").onclick = () => load(true);
      el.querySelector("#discuss-summary").onclick = () => {
        pendingWorkspaceTab = null;
        pendingChatPrompt = "Help me understand the main ideas in the lecture summary. Explain them step by step and use examples where useful.";
        const chatTab = document.querySelector('.workspace-tabs [data-tab="Chat"]');
        if (chatTab) chatTab.click();
      };
    } catch (error) {
      if (stale()) return;
      el.innerHTML = `<section class="summary-error-card"><div class="summary-error-icon">${ico("circle-help")}</div><div><h3>We couldn't prepare your summary</h3><p>${esc(error.message)}</p><button type="button" class="btn" id="re">Try again</button></div></section>`;
      el.querySelector("#re").onclick = () => load(false);
    }
  };
  load(false);
}

function tabDetailedNotes(el, alive = () => true) {
  const lectureId = current;
  const lec = lectures.find((l) => l.id === lectureId);
  let loadSeq = 0;
  const load = async (refresh) => {
    const mine = ++loadSeq;
    const stale = () => mine !== loadSeq || !alive();
    el.innerHTML = `
      <section class="summary-loading-card">
        <div class="summary-loading-icon"><span class="processing-spinner"></span></div>
        <div><strong>${refresh ? "Refreshing detailed notes" : "Building detailed lecture notes"}</strong><p>Connecting the lecture's concepts into a fuller, step-by-step study guide…</p></div>
        <div class="summary-skeleton"><i></i><i></i><i></i><i></i></div>
      </section>`;
    try {
      const { detailed_notes: result } = await api(`/lectures/${lectureId}/detailed-notes${refresh ? "?refresh=true" : ""}`);
      if (stale()) return;
      const text = String(result || "").trim();
      const words = text ? text.match(/\S+/g).length : 0;
      const readingMinutes = Math.max(1, Math.ceil(words / 220));
      const sections = extractSummarySections(text);
      const outline = sections.length
        ? sections.map((name, index) => `<a href="#detailed-section-${index + 1}" data-detailed-target="detailed-section-${index + 1}"><span>${String(index + 1).padStart(2, "0")}</span><b>${esc(name)}</b></a>`).join("")
        : `<a href="#detailed-notes-document" data-detailed-target="detailed-notes-document"><span>01</span><b>Detailed notes</b></a>`;
      el.innerHTML = `
        <section class="summary-page detailed-notes-page">
          <header class="summary-hero-card">
            <div class="summary-title-row">
              <div class="summary-title-icon">${ico("book-open")}</div>
              <div class="summary-title-copy"><div class="summary-kicker"><span></span> IN-DEPTH STUDY GUIDE</div><h2>Detailed lecture notes</h2><p>Step-by-step explanations, definitions, examples, and revision checkpoints drawn from your lecture material.</p></div>
            </div>
            <div class="summary-actions"><button type="button" class="summary-action-button" id="copy-detailed-notes">${ico("clipboard-check")}<span>Copy notes</span></button><button type="button" class="summary-action-button" id="download-detailed-notes">${ico("download")}<span>Download .md</span></button><button type="button" class="btn" id="refresh-detailed-notes">${ico("sparkles")} Refresh</button></div>
            <div class="summary-meta-row"><span>${ico("clock")} About ${readingMinutes} min read</span><i></i><span>${ico("layers")} ${words.toLocaleString()} words</span><i></i><span>${ico("book-open")} Lecture-grounded guide</span></div>
          </header>
          <div class="summary-reading-layout">
            <aside class="summary-outline-card"><div class="summary-outline-heading">IN THESE NOTES</div><nav class="summary-outline">${outline}</nav><div class="summary-outline-tip"><span>${ico("lightbulb")}</span><div><strong>Study tip</strong><p>Pause after each section and explain the concept without looking at the notes.</p></div></div></aside>
            <article id="detailed-notes-document" class="summary-document">${renderRichText(text, { headingPrefix: "detailed", listItemAnchors: false })}</article>
          </div>
          <footer class="summary-bottom-card"><div class="summary-bottom-icon">${ico("message-circle")}</div><div class="summary-bottom-copy"><strong>Need help with a difficult section?</strong><p>Ask the study assistant to explain it step by step or create a worked example based on this lecture.</p></div><button type="button" class="ghost" id="discuss-detailed-notes">Discuss with AI ${ico("arrow-up-right")}</button></footer>
        </section>`;
      el.querySelectorAll("[data-detailed-target]").forEach((link) => {
        link.addEventListener("click", (event) => {
          event.preventDefault();
          const target = el.querySelector(`[id="${link.dataset.detailedTarget}"]`);
          target?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      });
      el.querySelector("#copy-detailed-notes").onclick = () => copyText(text, "Detailed notes copied");
      el.querySelector("#download-detailed-notes").onclick = () => {
        const safeTitle = String(lec?.title || "lecture").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toLowerCase() || "lecture";
        const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${safeTitle}-detailed-notes.md`;
        document.body.append(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        toast("Detailed-notes download started");
      };
      el.querySelector("#refresh-detailed-notes").onclick = () => load(true);
      el.querySelector("#discuss-detailed-notes").onclick = () => {
        pendingChatPrompt = "Walk me through the detailed lecture notes step by step. Start with the hardest or most important concepts, use only the lecture material, and give examples where supported.";
        const chatTab = document.querySelector('.workspace-tabs [data-tab="Chat"]');
        if (chatTab) chatTab.click();
      };
    } catch (error) {
      if (stale()) return;
      el.innerHTML = `<section class="summary-error-card"><div class="summary-error-icon">${ico("circle-help")}</div><div><h3>We couldn't prepare detailed notes</h3><p>${esc(error.message)}</p><button type="button" class="btn" id="retry-detailed-notes">Try again</button></div></section>`;
      el.querySelector("#retry-detailed-notes").onclick = () => load(false);
    }
  };
  load(false);
}

function tabQuiz(el, alive = () => true) {
  const lectureId = current;
  el.innerHTML = `<div class="row"><label>Questions <select id="n">${[3, 5, 8, 10].map((n) => `<option ${n === 5 ? "selected" : ""}>${n}</option>`).join("")}</select></label><button class="btn" id="gen">Generate quiz</button></div><div id="qz"></div>`;
  const out = el.querySelector("#qz");
  const gen = el.querySelector("#gen");
  const count = el.querySelector("#n");
  gen.onclick = async () => {
    gen.disabled = true;
    out.innerHTML = `<p class="empty">Generating questions...</p>`;
    try {
      const { questions } = await post(`/lectures/${lectureId}/quiz`, { num_questions: +count.value });
      if (!alive()) return;
      renderQuiz(out, questions.filter((q) => q.question && q.options && q.answer));
    } catch (e) {
      if (alive()) out.innerHTML = `<p class="err">${esc(e.message)}</p>`;
    } finally { gen.disabled = false; }
  };
}

function renderQuiz(out, qs) {
  if (!out || !out.isConnected) return;
  if (!qs.length) { out.innerHTML = `<p class="err">No usable questions came back. Generate the quiz again.</p>`; return; }
  out.innerHTML = `<form id="qf">${qs.map((q, i) => `<fieldset class="card"><legend>${i + 1}. ${esc(q.question)}</legend>${Object.entries(q.options).map(([k, v]) => `<label class="opt"><input type="radio" name="q${i}" value="${esc(k)}"> <b>${esc(k)}.</b> ${esc(v)}</label>`).join("")}<p class="why" hidden></p></fieldset>`).join("")}<button class="btn">Check answers</button> <span id="score"></span></form>`;
  const form = out.querySelector("#qf");
  form.onsubmit = (e) => {
    e.preventDefault();
    let ok = 0;
    const sets = form.querySelectorAll("fieldset");
    qs.forEach((q, i) => {
      const pick = sets[i].querySelector("input:checked")?.value;
      const right = pick === q.answer;
      ok += right;
      sets[i].classList.toggle("right", right);
      sets[i].classList.toggle("wrong", !right);
      const w = sets[i].querySelector(".why");
      w.hidden = false;
      w.textContent = (right ? "Correct. " : `Answer: ${q.answer}. `) + (q.explanation || "");
    });
    const score = form.querySelector("#score");
    if (score) score.textContent = `You got ${ok} of ${qs.length}.`;
  };
}

function tabEval(el, alive = () => true) {
  const lectureId = current;
  el.innerHTML = `<p class="sub">Add test questions with the answer you expect. Rows missing either part are ignored.</p><div id="rows"></div><div class="row"><button class="ghost" id="add" type="button">Add row</button><button class="btn" id="run">Run evaluation</button></div><div id="res"></div>`;
  const rows = el.querySelector("#rows");
  const res = el.querySelector("#res");
  const run = el.querySelector("#run");
  const addRow = () => {
    const d = document.createElement("div");
    d.className = "erow";
    d.innerHTML = `<input placeholder="Question" aria-label="Question"><input placeholder="Expected answer" aria-label="Expected answer">`;
    rows.append(d);
  };
  addRow(); addRow();
  el.querySelector("#add").onclick = addRow;
  run.onclick = async () => {
    const items = [...rows.querySelectorAll(".erow")].map((r) => { const [a, b] = r.querySelectorAll("input"); return { question: a.value.trim(), ground_truth: b.value.trim() }; }).filter((i) => i.question && i.ground_truth);
    if (!items.length) return toast("Add at least one question with an expected answer");
    run.disabled = true;
    res.innerHTML = `<p class="empty">Running the evaluation. This can take a few minutes.</p>`;
    try {
      const { scores, n } = await post(`/lectures/${lectureId}/evaluate`, { items });
      if (!alive()) return;
      const tiles = [["Faithfulness", "faithfulness"], ["Answer relevancy", "answer_relevancy"], ["Context precision", "context_precision"], ["Context recall", "context_recall"]];
      res.innerHTML = `<p class="sub">Calculated from ${n} question${n === 1 ? "" : "s"}.</p><div class="tiles">${tiles.map(([l, k]) => `<div class="tile"><b>${Number.isFinite(scores[k]) ? Math.round(scores[k] * 100) + "%" : "N/A"}</b><span>${l}</span></div>`).join("")}</div>`;
    } catch (e) {
      if (alive()) res.innerHTML = `<p class="err">${esc(e.message)}</p>`;
    } finally { run.disabled = false; }
  };
}

route();