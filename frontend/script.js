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
  sprout: '<path d="M12 21v-9"/><path d="M12 12C5 12 3 8 3 4c6 0 9 3 9 8Z"/><path d="M12 16c0-6 3-10 9-10 0 5-2 10-9 10Z"/>',
  'shield-check': '<path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z"/><path d="m9 12 2 2 4-4"/>',
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

function normalizeChatWhitespace(source) {
  return String(source ?? "")
    // Some model responses contain encoded spaces. Normalize only whitespace
    // entities before Markdown parsing so they do not appear as literal text.
    .replace(/&amp;#(?:x0*20|0*32|0*160);|&amp;nbsp;/gi, " ")
    .replace(/&#(?:x0*20|0*32|0*160);|&(?:nbsp|ensp|emsp|thinsp);/gi, " ");
}

function renderRichText(source, options = {}) {
  const lines = normalizeChatWhitespace(source).replace(/\r\n?/g, "\n").split("\n");
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

    const heading = line.match(/^\s*(#{1,3})\s+(.+?)\s*$/);
    const standaloneLabel = line.trim().match(/^\*\*([^*\n]{2,60})\*\*:?$|^__([^_\n]{2,60})__:?$/);
    if (heading || (standaloneLabel && !options.headingPrefix)) {
      flushParagraph();
      flushList();
      const level = heading ? heading[1].length : 3;
      const label = heading ? heading[2] : (standaloneLabel[1] || standaloneLabel[2]).replace(/:$/, "");
      const id = options.headingPrefix ? ` id="${options.headingPrefix}-section-${++sectionNumber}"` : "";
      output.push(`<h${level} class="rich-heading"${id}>${renderInline(label)}</h${level}>`);
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
let currentUser = null;
let csrfToken = "";
let authLoaded = false;
let authMode = "login";
let pendingWorkspaceTab = null;
let pendingSearch = "";
let pendingChatPrompt = null;
const chats = {};

async function api(path, opts = {}) {
  const method = String(opts.method || "GET").toUpperCase();
  const headers = new Headers(opts.headers || {});
  if (csrfToken && ["POST", "PATCH", "DELETE", "PUT"].includes(method) && !path.startsWith("/auth/login") && !path.startsWith("/auth/register")) {
    headers.set("X-CSRF-Token", csrfToken);
  }
  const res = await fetch(API + "/api" + path, { credentials: "include", ...opts, method, headers });
  if (!res.ok) {
    let d = res.statusText;
    try { const j = await res.json(); d = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail || d); } catch {}
    if (res.status === 401 && currentUser && !path.startsWith("/auth/")) {
      currentUser = null;
      csrfToken = "";
      authLoaded = true;
      updateShell();
      renderAuthScreen("login", "Your session expired. Sign in again.");
    }
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
  const seq = ++routeSeq;
  const routeParts = location.hash.replace(/^#\/?/, "").split("/");
  const page = routeParts[0] || "dashboard";
  const id = routeParts[1] ? decodeURIComponent(routeParts[1]) : null;
  document.querySelector(".app")?.classList.toggle("workspace-mode", page === "workspace");
  const isLegalPage = page === "privacy" || page === "terms";
  document.querySelector(".app")?.classList.toggle("legal-mode", isLegalPage);
  const labels = { dashboard: "Overview", lectures: "My Lectures", workspace: "Study Workspace", privacy: "Privacy policy", terms: "Terms and conditions", farms: "Farm data", admin: "Administration" };
  $("#top-page").textContent = labels[page] || "Overview";
  if (isLegalPage) {
    updateShell();
    viewLegalPage(page);
    return;
  }
  if (!authLoaded) return;
  if (!currentUser) {
    updateShell();
    renderAuthScreen(authMode);
    return;
  }
  if (currentUser.role === "farmer" && page !== "farms") {
    location.hash = "#/farms";
    return;
  }
  if (currentUser.role === "student" && (page === "farms" || page === "admin")) {
    location.hash = "#/dashboard";
    return;
  }
  if (currentUser.role === "admin" && page === "farms") {
    location.hash = "#/admin";
    return;
  }
  if (currentUser.role !== "admin" && page === "admin") {
    location.hash = currentUser.role === "farmer" ? "#/farms" : "#/dashboard";
    return;
  }
  updateShell();
  document.querySelectorAll("#nav a").forEach((a) => a.classList.toggle("on", a.dataset.r === page));
  if (page === "farms") {
    await viewFarms();
    return;
  }
  if (page === "admin") {
    await viewAdmin();
    return;
  }
  if (id) { current = id; store.set("lecture", id); }
  let loadError = null;
  try {
    const data = await api("/lectures");
    if (seq !== routeSeq) return;
    lectures = data;
    serverOnline = true;
  } catch (e) {
    if (seq !== routeSeq) return;
    lectures = [];
    serverOnline = false;
    loadError = e.message || "Unknown error";
  }
  if (loadError) {
    if (!currentUser) return;
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
const newLectureNav = document.querySelector(".new-lecture-nav");
newLectureNav?.addEventListener("click", (event) => {
  if (location.hash === "#/dashboard" || location.hash === "") {
    event.preventDefault();
    document.querySelector("#choose-file")?.click();
  }
});

function updateShell() {
  const signedIn = Boolean(currentUser);
  document.body.classList.toggle("auth-screen", !signedIn);
  const links = {
    dashboard: signedIn && currentUser.role !== "farmer",
    lectures: signedIn && currentUser.role !== "farmer",
    workspace: signedIn && currentUser.role !== "farmer",
    farms: signedIn && currentUser.role === "farmer",
    admin: signedIn && currentUser.role === "admin",
  };
  Object.entries(links).forEach(([name, visible]) => {
    const node = document.querySelector(`#nav [data-r="${name}"]`);
    if (node) node.hidden = !visible;
  });
  $("#logout").hidden = !signedIn;
  $(".global-search").hidden = signedIn && currentUser.role === "farmer";
  $("#notify").hidden = signedIn && currentUser.role === "farmer";
  if (signedIn) {
    $("#profile-name").textContent = currentUser.display_name;
    $("#profile-role").textContent = currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1);
    $("#profile-avatar").textContent = (currentUser.display_name || currentUser.email || "U").trim().charAt(0).toUpperCase();
    $(".topbar-context > span:nth-of-type(2)").textContent = currentUser.role === "admin" ? "ADMIN PORTAL" : currentUser.role === "farmer" ? "FARMER PORTAL" : "STUDENT PORTAL";
  }
}

function renderAuthScreen(mode = "login", message = "") {
  authMode = mode === "register" ? "register" : "login";
  document.body.classList.add("auth-screen");
  const isRegister = authMode === "register";
  $("#view").innerHTML = `
    <section class="auth-layout">
      <a class="auth-brand" href="#/dashboard"><span class="auth-brand-mark">C</span><span><strong>Campus Study Desk</strong><small>STUDY ASSISTANT</small></span></a>
      <div class="auth-card">
        <h1>${isRegister ? "Create your account" : "Welcome back"}</h1>
        <p class="auth-intro">${isRegister ? "Create an account to get started." : "Sign in to continue to your study space."}</p>
        <div class="auth-switch" role="group" aria-label="Authentication option"><button type="button" data-auth-mode="login" class="${!isRegister ? "active" : ""}">Sign in</button><button type="button" data-auth-mode="register" class="${isRegister ? "active" : ""}">Create account</button></div>
        <form id="auth-form" class="auth-form">
          ${isRegister ? `<label>Full name<input name="display_name" required maxlength="100" autocomplete="name" placeholder="Your name"></label>` : ""}
          <label>Email address<input name="email" type="email" required maxlength="254" autocomplete="email" placeholder="you@example.com"></label>
          <label>Password<input name="password" type="password" required minlength="${isRegister ? 12 : 1}" maxlength="256" autocomplete="${isRegister ? "new-password" : "current-password"}" placeholder="${isRegister ? "At least 12 characters" : "Your password"}"></label>
          ${isRegister ? `<label>Account type<select name="role"><option value="student">Student</option><option value="farmer">Farmer</option></select></label>` : ""}
          <p class="auth-message" id="auth-message" role="alert" ${message ? "" : "hidden"}>${esc(message)}</p>
          <button class="btn auth-submit" type="submit">${isRegister ? "Create account" : "Sign in"}</button>
        </form>
        <p class="auth-footnote">Admin accounts are created by the site operator.</p>
        <p class="auth-legal"><a href="#/privacy">Privacy policy</a><a href="#/terms">Terms and conditions</a></p>
      </div>
      
    </section>`;
  document.querySelectorAll("[data-auth-mode]").forEach((button) => {
    button.onclick = () => renderAuthScreen(button.dataset.authMode);
  });
  $("#auth-form").onsubmit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const submit = form.querySelector("button[type=submit]");
    const messageNode = $("#auth-message");
    submit.disabled = true;
    submit.textContent = isRegister ? "Creating account..." : "Signing in...";
    messageNode.hidden = true;
    try {
      const fd = new FormData(form);
      const payload = {
        email: String(fd.get("email") || "").trim(),
        password: String(fd.get("password") || ""),
      };
      if (isRegister) {
        payload.display_name = String(fd.get("display_name") || "").trim();
        payload.role = String(fd.get("role") || "student");
      }
      const result = await api(isRegister ? "/auth/register" : "/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      currentUser = result.user;
      csrfToken = result.csrf_token;
      authLoaded = true;
      authMode = "login";
      updateShell();
      location.hash = currentUser.role === "farmer" ? "#/farms" : "#/dashboard";
      route();
    } catch (error) {
      messageNode.textContent = error.message || "Unable to authenticate. Please try again.";
      messageNode.hidden = false;
    } finally {
      submit.disabled = false;
      submit.textContent = isRegister ? "Create account" : "Sign in";
    }
  };
}

async function bootstrapAuth() {
  try {
    const result = await api("/auth/me");
    currentUser = result.user;
    csrfToken = result.csrf_token;
  } catch {
    currentUser = null;
    csrfToken = "";
  }
  authLoaded = true;
  updateShell();
  if (!location.hash) location.hash = currentUser?.role === "farmer" ? "#/farms" : "#/dashboard";
  await route();
}

$("#logout").onclick = async () => {
  try { await api("/auth/logout", { method: "POST" }); } catch {}
  currentUser = null;
  csrfToken = "";
  authLoaded = true;
  authMode = "login";
  updateShell();
  location.hash = "#/dashboard";
  renderAuthScreen("login", "You have signed out.");
};

function farmMetric(label, value, suffix = "") {
  const shown = value === null || value === undefined || value === "" ? "Not recorded" : `${esc(value)}${suffix}`;
  return `<div class="farm-metric"><span>${label}</span><strong>${shown}</strong></div>`;
}

async function viewFarms() {
  if (!currentUser || currentUser.role !== "farmer") {
    location.hash = currentUser?.role === "admin" ? "#/admin" : "#/dashboard";
    return;
  }
  document.querySelector(".app")?.classList.remove("workspace-mode");
  $("#info").innerHTML = "";
  $("#view").innerHTML = `
    <div class="page-head"><div><div class="eyebrow">PRIVATE FARM SPACE</div><h1>Your farm data</h1><p>Only your account's farm records are returned by the server. Add or update readings as your data changes.</p></div></div>
    <section class="farm-create-card"><h2>Add farm record</h2><p class="farm-form-intro">Enter the values you have. Blank readings remain marked as not recorded.</p>
      <form id="farm-create-form" class="farm-form">
        <label>Farm name<input name="name" required maxlength="120" placeholder="North field"></label>
        <label>Location<input name="location" maxlength="200" placeholder="Village or area"></label>
        <label>Crop<input name="crop" maxlength="120" placeholder="Current crop"></label>
        <label>Soil moisture (%)<input name="soil_moisture" type="number" min="0" max="100" step="0.1" placeholder="0 to 100"></label>
        <label>Temperature (°C)<input name="temperature_c" type="number" min="-50" max="80" step="0.1" placeholder="Recorded value"></label>
        <label>Humidity (%)<input name="humidity_pct" type="number" min="0" max="100" step="0.1" placeholder="0 to 100"></label>
        <label class="farm-notes-field">Notes<textarea name="notes" rows="2" maxlength="5000" placeholder="Optional observations"></textarea></label>
        <div class="farm-form-actions"><button class="btn" type="submit">Save farm record</button><span id="farm-form-status" role="status"></span></div>
      </form>
    </section>
    <section class="farm-records-section"><div class="section-head"><div class="section-title-wrap"><h2>Saved farm records</h2><p>Records available to this signed-in account.</p></div></div><div id="farm-list"><p class="empty">Loading farm data...</p></div></section>`;
  const seqAtStart = routeSeq;
  try {
    const items = await api("/farms");
    if (seqAtStart !== routeSeq || !$("#farm-list")) return;
    renderFarmCards(items);
  } catch (error) {
    if (seqAtStart !== routeSeq) return;
    $("#farm-list").innerHTML = `<p class="err">${esc(error.message)}</p>`;
  }
  $("#farm-create-form").onsubmit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const submit = form.querySelector("button[type=submit]");
    const status = $("#farm-form-status");
    submit.disabled = true;
    status.textContent = "Saving...";
    try {
      await api("/farms", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(farmPayload(new FormData(form))) });
      toast("Farm record saved.");
      await viewFarms();
    } catch (error) {
      status.textContent = error.message;
      submit.disabled = false;
    }
  };
}

function farmPayload(formData) {
  const payload = {};
  for (const field of ["name", "location", "crop", "notes"]) payload[field] = String(formData.get(field) || "").trim();
  for (const field of ["soil_moisture", "temperature_c", "humidity_pct"]) {
    const value = String(formData.get(field) || "").trim();
    payload[field] = value === "" ? null : Number(value);
  }
  return payload;
}

function renderFarmCards(items) {
  const target = $("#farm-list");
  if (!items.length) {
    target.innerHTML = `<div class="farm-empty"><h3>No farm records yet</h3><p>Save a farm record above to begin tracking its available readings.</p></div>`;
    return;
  }
  target.innerHTML = `<div class="farm-cards">${items.map((farm) => `
    <article class="farm-card">
      <div class="farm-card-head"><div><div class="eyebrow">YOUR FARM</div><h3>${esc(farm.name)}</h3><p>${esc(farm.location || "Location not recorded")}${farm.crop ? ` · ${esc(farm.crop)}` : ""}</p></div><button type="button" class="ghost danger" data-farm-delete="${esc(farm.id)}">Delete</button></div>
      <div class="farm-metrics">${farmMetric("Soil moisture", farm.soil_moisture, "%")}${farmMetric("Temperature", farm.temperature_c, " °C")}${farmMetric("Humidity", farm.humidity_pct, "%")}</div>
      <details class="farm-edit-details"><summary>Edit this record</summary><form class="farm-form farm-edit-form" data-farm-edit="${esc(farm.id)}">
        <label>Farm name<input name="name" required maxlength="120" value="${esc(farm.name)}"></label>
        <label>Location<input name="location" maxlength="200" value="${esc(farm.location || "")}"></label>
        <label>Crop<input name="crop" maxlength="120" value="${esc(farm.crop || "")}"></label>
        <label>Soil moisture (%)<input name="soil_moisture" type="number" min="0" max="100" step="0.1" value="${farm.soil_moisture ?? ""}"></label>
        <label>Temperature (°C)<input name="temperature_c" type="number" min="-50" max="80" step="0.1" value="${farm.temperature_c ?? ""}"></label>
        <label>Humidity (%)<input name="humidity_pct" type="number" min="0" max="100" step="0.1" value="${farm.humidity_pct ?? ""}"></label>
        <label class="farm-notes-field">Notes<textarea name="notes" rows="2" maxlength="5000">${esc(farm.notes || "")}</textarea></label>
        <div class="farm-form-actions"><button class="btn btn-sm" type="submit">Save changes</button><span role="status"></span></div>
      </form></details>
    </article>`).join("")}</div>`;
  target.querySelectorAll("form[data-farm-edit]").forEach((form) => {
    form.onsubmit = async (event) => {
      event.preventDefault();
      const submit = form.querySelector("button[type=submit]");
      const status = form.querySelector("[role=status]");
      submit.disabled = true;
      status.textContent = "Saving...";
      try {
        await api(`/farms/${encodeURIComponent(form.dataset.farmEdit)}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(farmPayload(new FormData(form))) });
        toast("Farm record updated.");
        await viewFarms();
      } catch (error) {
        status.textContent = error.message;
        submit.disabled = false;
      }
    };
  });
  target.querySelectorAll("[data-farm-delete]").forEach((button) => {
    button.onclick = async () => {
      if (!confirm("Delete this farm record? This cannot be undone.")) return;
      button.disabled = true;
      try {
        await api(`/farms/${encodeURIComponent(button.dataset.farmDelete)}`, { method: "DELETE" });
        toast("Farm record deleted.");
        await viewFarms();
      } catch (error) {
        toast(error.message);
        button.disabled = false;
      }
    };
  });
}

async function viewAdmin() {
  $("#info").innerHTML = "";
  $("#view").innerHTML = `<div class="page-head"><div><div class="eyebrow">SITE CONTROL</div><h1>Administration</h1><p>Review registered accounts and disable accounts that should no longer have access.</p></div></div><section class="admin-note"><strong>Admin access is provisioned from the server environment.</strong><p>Set <code>ADMIN_EMAIL</code> and <code>ADMIN_PASSWORD</code> before starting the API. Never create administrator accounts through public registration.</p></section><section class="admin-users-section"><h2>Registered accounts</h2><div id="admin-user-list"><p class="empty">Loading accounts...</p></div></section>`;
  const seqAtStart = routeSeq;
  try {
    const users = await api("/admin/users");
    if (seqAtStart !== routeSeq || !$("#admin-user-list")) return;
    if (!users.length) {
      $("#admin-user-list").innerHTML = `<p class="empty">No accounts found.</p>`;
      return;
    }
    $("#admin-user-list").innerHTML = `<div class="admin-user-list">${users.map((user) => `<article class="admin-user-row"><div class="admin-user-avatar">${esc((user.display_name || user.email).charAt(0).toUpperCase())}</div><div class="admin-user-copy"><strong>${esc(user.display_name)}</strong><span>${esc(user.email)}</span><small>${esc(user.role)} · Created ${esc(fmt(user.created_at))}</small></div><div class="admin-user-action"><span class="account-status ${user.is_active ? "active" : "disabled"}">${user.is_active ? "Active" : "Disabled"}</span>${user.id === currentUser.id ? `<span class="current-account-label">You</span>` : `<button type="button" class="ghost sm" data-user-active="${user.id}" data-next-active="${user.is_active ? "false" : "true"}">${user.is_active ? "Disable" : "Enable"}</button>`}</div></article>`).join("")}</div>`;
    $("#admin-user-list").querySelectorAll("[data-user-active]").forEach((button) => {
      button.onclick = async () => {
        const isActive = button.dataset.nextActive === "true";
        const action = isActive ? "enable" : "disable";
        if (!confirm(`Are you sure you want to ${action} this account?`)) return;
        button.disabled = true;
        try {
          await api(`/admin/users/${button.dataset.userActive}/active`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_active: isActive }) });
          toast(`Account ${isActive ? "enabled" : "disabled"}.`);
          await viewAdmin();
        } catch (error) {
          toast(error.message);
          button.disabled = false;
        }
      };
    });
  } catch (error) {
    if (seqAtStart !== routeSeq) return;
    $("#admin-user-list").innerHTML = `<p class="err">${esc(error.message)}</p>`;
  }
}


function viewLegalPage(page) {
  const isPrivacy = page === "privacy";
  const title = isPrivacy ? "Privacy policy" : "Terms and conditions";
  const intro = isPrivacy
    ? "This policy explains how Campus Study Desk handles information when you upload lecture material or use its study tools. The deployed operator must confirm the details below before making the service public."
    : "These terms cover your use of Campus Study Desk, including lecture uploads, generated notes, question answering, quizzes, and evaluation tools. The deployed operator must confirm the details below before making the service public.";
  const privacySections = `
    <section><h2>1. Information the service processes</h2><p>The application can process account details, farm names and manually entered farm readings, audio and video recordings, documents, lecture titles, extracted transcripts, text passages created for search, questions you submit, and generated study materials. Operational logs may also contain request details needed to run and troubleshoot the service.</p></section>
    <section><h2>2. How information is used</h2><p>Material is used to transcribe recordings, build searchable lecture indexes, answer questions, prepare summaries and detailed notes, generate quizzes, and evaluate answers. It may also be used to maintain service security and diagnose failures.</p></section>
    <section><h2>3. External service providers</h2><p>Depending on the enabled features and deployment configuration, the application can send recording content to Sarvam AI for transcription or translation, and send text prompts or evaluation content to Google Gemini or Groq for model-powered features. Review the current terms and privacy notices of each provider used in your deployment. Confirm the active providers before launch and update this section if the configuration changes.</p></section>
    <section><h2>4. Storage and retention</h2><p>Lecture files, transcripts, indexes, and generated material may be stored in the application's configured server storage. This code package does not define a complete automatic retention or deletion schedule. The operator must state how long each data type is kept, how a user can request deletion, and how backups are handled before public release.</p></section>
    <section><h2>5. Browser storage</h2><p>The frontend uses browser local storage for interface preferences and limited navigation state, such as the chosen colour theme and recently selected lecture. The API uses an HttpOnly, SameSite session cookie and a CSRF token for signed-in sessions. Account and farm records are stored in the configured server database. The operator should confirm and document the exact cookie and storage practices of the production hosting setup. The supplied frontend does not include an advertising tracker. Hosting, reverse proxies, or third-party services may apply their own logging or storage, which must be documented for the deployed service.</p></section>
    <section><h2>6. Your choices</h2><p>Do not upload material unless you have the right to use it for this purpose. Avoid including passwords, payment details, or unrelated sensitive personal information. To request access to or deletion of information, contact the operator using the contact details published on the deployed service.</p></section>
    <section><h2>7. Security</h2><p>The operator should restrict access to uploaded material, protect API credentials, configure transport security, maintain dependencies, and define a response process for incidents. No website or storage system can be guaranteed completely secure.</p></section>
    <section><h2>8. Changes to this policy</h2><p>This policy should be updated when data practices, service providers, hosting, or retention rules change. The operator must publish a working contact address and the date of the latest substantive revision.</p></section>`;
  const termsSections = `
    <section><h2>1. Purpose of the service</h2><p>Campus Study Desk provides student lecture tools, administrator account controls, and a farmer workspace for manually managing farm records and readings. Farm records in this release are not live sensor feeds.</p></section>
    <section><h2>2. Your material and permissions</h2><p>You remain responsible for the content you upload and for having the rights or permissions needed to process it. Do not upload material unlawfully, infringe another person's rights, or submit content you are not authorized to share with the service's configured providers.</p></section>
    <section><h2>3. Generated content and accuracy</h2><p>Transcripts, answers, summaries, quizzes, and evaluation results may contain omissions or errors. Check important claims against the original lecture and linked source passages. The service is a study aid, not a substitute for your course instructions, an instructor's judgment, or professional advice.</p></section>
    <section><h2>4. Acceptable use</h2><p>Do not attempt to disrupt the service, bypass access controls, upload malicious files, misuse other people's material, or use the service to violate applicable law. The operator may limit access to protect the service or respond to misuse, subject to applicable law.</p></section>
    <section><h2>5. Third-party services</h2><p>Some functions depend on external transcription or model providers. Their availability, processing, and terms may affect the service. The operator should identify the providers used in the deployed instance and link to their current notices in the privacy policy.</p></section>
    <section><h2>6. Availability and changes</h2><p>Features may be changed, interrupted, or unavailable because of maintenance, provider limits, network issues, or technical failures. The operator should not promise uninterrupted availability unless it can support that commitment.</p></section>
    <section><h2>7. Disclaimers and applicable law</h2><p>To the extent permitted by applicable law, the service is provided without a guarantee that every output will be accurate, complete, or available at all times. The operator must identify the contracting entity, applicable jurisdiction, and any legally required consumer notices before launch. Nothing in these terms removes rights that cannot lawfully be excluded.</p></section>
    <section><h2>8. Updates and contact</h2><p>These terms should be revised when the service or its legal requirements change. The operator must publish a valid contact address and the date of the latest substantive revision.</p></section>`;

  const sections = isPrivacy ? privacySections : termsSections;
  const notice = `<aside class="legal-review-notice" role="note"><strong>Required before public launch</strong><p>Add the real operator or business name, a monitored contact email, the applicable jurisdiction, and confirmed data-retention details. The application now provides student, farmer, and administrator accounts with role-based API checks. Test these controls in the deployed environment and use shared durable storage before exposing real student or farm records publicly. Review this page against the live hosting and API configuration. These details are not inferred or invented in this project.</p></aside>`;
  $("#view").innerHTML = `
    <article class="legal-page">
      <header class="legal-page-header"><p class="eyebrow">CAMPUS STUDY DESK</p><h1>${title}</h1><p class="legal-updated">Last reviewed: 20 October 2026</p><p class="legal-intro">${intro}</p></header>
      ${notice}
      <div class="legal-content">${sections}</div>
      <p class="legal-back"><a href="#/dashboard">Back to portal</a></p>
    </article>`;
}

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
    <section class="study-home">
      <div class="home-welcome">
        <h1>What would you like to study?</h1>
        <p>Add a lecture to chat with it, make notes, or practise.</p>
      </div>
      <section class="study-upload-area" aria-label="Add study material">
        <div class="study-composer">
          <div class="study-composer-label">Start with a lecture</div>
          <input type="file" id="file" accept="video/*,audio/*" hidden>
          <div class="study-composer-actions">
            <button type="button" class="btn study-upload-button" id="choose-file">${ico("plus")} <span>Upload audio or video</span></button>
            <button type="button" id="youtube-toggle" class="study-link-button" hidden>Use YouTube</button>
          </div>
          <div class="study-upload-note" id="hint">Audio and video files supported.</div>
        </div>
        <div id="ytrow" class="youtube-row" hidden><input id="yt" type="url" placeholder="Paste a YouTube URL" aria-label="YouTube lecture URL"><button type="button" class="btn btn-sm" id="ytb">Add link ${ico("arrow-up-right")}</button></div>
        <section id="picked-card" class="picked-upload" hidden>
          <div class="picked-file-icon">${ico("file-text")}</div><div class="picked-file-copy"><strong id="fname">Selected lecture</strong><small id="file-detail">Ready to process</small></div>
          <button type="button" id="up" class="btn btn-sm">Process ${ico("arrow-right")}</button><button type="button" id="cancel-file" class="ghost">Cancel</button>
        </section>
        <section id="reference-card" class="reference-upload-card" hidden>
          <div class="reference-upload-copy"><div class="reference-upload-heading"><strong>Add lecturer notes</strong> <span>Optional</span></div><p>Attach slides or handouts to ground answers in class material.</p><small id="reference-files-detail">PDF, DOCX, PPTX, TXT or Markdown</small></div>
          <input type="file" id="reference-files" accept=".pdf,.docx,.pptx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation,text/plain,text/markdown" multiple hidden>
          <button type="button" class="btn btn-sm" id="choose-reference-files">Add files</button>
        </section>
        <section id="prog" class="processing-card" hidden><div class="processing-heading"><span class="processing-spinner"></span><div><strong>Preparing your study space</strong><p id="stage">Uploading...</p></div></div><div class="bar"><i id="barfill"></i></div></section>
      </section>
      <section class="recent-study-section">
        <div class="recent-study-heading"><h2>Recent lectures</h2><a href="#/lectures" class="text-link">View all ${ico("arrow-right")}</a></div>
        ${recent.length ? `<div class="recent-list">${recent.map((l) => `
          <a class="recent-row" href="#/workspace/${encodeURIComponent(l.id)}"><span class="recent-mini-icon">${ico("file-text")}</span><span class="recent-row-copy"><strong>${esc(l.title)}</strong><small>Added ${esc(fmt(l.created_at) || "recently")}</small></span><span class="recent-open">${ico("arrow-up-right")}</span></a>`).join("")}</div>` : `<p class="recent-study-empty">Your lectures will appear here.</p>`}
      </section>
    </section>`

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
    pickedCard.scrollIntoView({ behavior: "auto", block: "nearest" });
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
    $("#hint").textContent = yt ? "Audio, video, or YouTube link." : "Audio and video files supported.";
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
    track(fetch(API + "/api/lectures/upload", { method: "POST", body: fd, credentials: "include", headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {} }));
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
    track(fetch(API + "/api/lectures/youtube", { method: "POST", body: fd, credentials: "include", headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {} }));
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
    $("#view").innerHTML = `<div class="workspace-empty"><h1>Choose a lecture</h1><p>Open a lecture to start chatting.</p><a class="btn" href="#/lectures">Browse lectures ${ico("arrow-right")}</a></div>`;
    return;
  }
  const tabs = { Chat: tabChat, Summary: tabSummary, "Detailed Notes": tabDetailedNotes, Quiz: tabQuiz, Evaluation: tabEval };
  const tabIcons = { Chat: "message-circle", Summary: "file-text", "Detailed Notes": "book-open", Quiz: "clipboard-check", Evaluation: "file-check" };
  $("#view").innerHTML = `
    <div class="workspace-page-head">
      <div class="workspace-title-group">
        <div class="eyebrow">YOUR LEARNING SPACE</div>
        <h1>${esc(lec.title)}</h1>
        <p>Ask questions about this lecture.</p>
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
      credentials: "include",
      headers: { "Content-Type": "application/json", "Accept": "application/x-ndjson", ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}) },
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
        <div class="chat-header-copy"><h2>${esc(lec.title)}</h2><p>Ask a question about this lecture.</p></div>
      </header>
      <div id="log" class="log polished-chat-log" role="log" aria-live="off" aria-label="Conversation"></div>
      <div id="chatStatus" class="sr-only" role="status" aria-live="polite"></div>
      <form id="ask" class="ask polished-composer">
        <div class="composer-box">
          <textarea id="q" rows="1" placeholder="Ask anything about this lecture…" autocomplete="off" maxlength="2000" aria-label="Your question"></textarea>
          <div class="composer-footer"><span>Lecture grounded</span><div class="composer-actions"><button type="button" class="ghost stop-message" id="stopAnswer" hidden>Stop</button><button class="btn send-message" id="sendQuestion" type="submit" aria-label="Send message">${ico("arrow-up-right")}</button></div></div>
        </div>
        <button type="button" id="reset" class="new-chat-button">${ico("plus")} <span>New chat</span></button>
      </form>
      <p class="chat-disclaimer">Check important answers against your lecture.</p>
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
      <h3>Ask anything about this lecture</h3>
      <div class="prompt-suggestions">
        <button type="button" data-prompt="Explain the main idea in simple terms.">Explain a concept</button>
        <button type="button" data-prompt="Give me a practical example from this lecture.">Show an example</button>
        <button type="button" data-prompt="Summarize the key points I should remember.">Summarize key points</button>
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
          target?.scrollIntoView({ behavior: "auto", block: "start" });
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
          target?.scrollIntoView({ behavior: "auto", block: "start" });
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
bootstrapAuth();
