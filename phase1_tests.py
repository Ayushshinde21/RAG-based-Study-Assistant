import sys, json, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright

SITE = sys.argv[1]
LECTURES = [{"id": "aaa", "title": "Binary Trees", "num_chunks": 12, "created_at": "2026-10-01T10:00:00"}]

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=SITE))
URL = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
threading.Thread(target=srv.serve_forever, daemon=True).start()

results = []
def record(name, ok, detail=""):
    results.append((name, ok))
    print(("PASS" if ok else "FAIL"), "-", name, ("| " + detail) if detail else "")

CHAT_MOCK = """
window.__chat = {mode:'ok', tokens:8, interval:100, paragraphs:false, fixed:null, calls:[], aborted:0};
const __of = window.fetch;
window.fetch = function(u, o) {
  if (!/\\/api\\/lectures\\/[^/]+\\/chat$/.test(String(u))) return __of.apply(this, arguments);
  const cfg = window.__chat; cfg.calls.push(JSON.parse(o.body));
  if (cfg.mode === 'fail') return Promise.resolve(new Response(JSON.stringify({detail:'Model is overloaded'}), {status:500, headers:{'Content-Type':'application/json'}}));
  const enc = new TextEncoder(); let i = 0, timer;
  const total = cfg.fixed ? cfg.fixed.length : cfg.tokens;
  const stream = new ReadableStream({ start(ctrl) {
    const line = (x) => ctrl.enqueue(enc.encode(JSON.stringify(x) + '\\n'));
    line({type:'sources', data:[{text:'Passage one text', time:'00:01:10'},{text:'Passage two text', time:'00:02:00'}]});
    timer = setInterval(() => {
      if (i < total) { line({type:'token', data: cfg.fixed ? cfg.fixed[i] : (cfg.paragraphs ? ('Paragraph ' + i + ' of the answer.\\n\\n') : ('word' + i + ' '))}); i++; }
      else { clearInterval(timer); if (cfg.mode !== 'nodone') line({type:'done'}); ctrl.close(); }
    }, cfg.interval);
    if (o.signal) o.signal.addEventListener('abort', () => { clearInterval(timer); cfg.aborted++; ctrl.error(new DOMException('aborted','AbortError')); });
  }});
  return Promise.resolve(new Response(stream, {status:200, headers:{'Content-Type':'application/x-ndjson'}}));
};
"""

def install(page):
    def handle(route):
        path = route.request.url.split("/api", 1)[1].split("?")[0]
        ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
        if path == "/lectures": return ok(LECTURES)
        if path == "/health": return ok({"max_upload_mb": 200, "youtube_enabled": True})
        if path.endswith("/summary"): return ok({"summary": "# Heading\n\n- a\n- b"})
        if path.endswith("/chat/reset"): return ok({})
        route.fulfill(status=404, body="{}")
    page.route("**/api/**", handle)

def fresh(browser, **cfg):
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.add_init_script(CHAT_MOCK)
    install(page)
    page.goto(URL + "#/workspace/aaa"); page.wait_for_timeout(700)
    if cfg: page.evaluate("c => Object.assign(window.__chat, c)", cfg)
    return ctx, page, errors

def ask(page, text="what is a tree"):
    page.fill("#q", text); page.press("#q", "Enter")

def guarded(name, fn):
    try: fn()
    except Exception as e: record(name, False, "crashed: " + str(e).splitlines()[0][:100])

with sync_playwright() as p:
    browser = p.chromium.launch()

    def t_incremental():
        ctx, page, errors = fresh(browser, tokens=8)
        ask(page); page.wait_for_timeout(250)
        page.evaluate("document.querySelectorAll('.chat-message').forEach(n => n.__keep = 1)")
        page.wait_for_timeout(1400)
        kept = page.evaluate("[...document.querySelectorAll('.chat-message')].every(n => n.__keep === 1)")
        n = page.locator(".chat-message").count()
        txt = page.locator(".is-assistant .rich-content").inner_text()
        record("1 Streaming updates only the last message's DOM (nodes never rebuilt)", kept and n == 2 and "word7" in txt, f"nodesKept={kept} count={n}")
        ctx.close()
    guarded("1", t_incremental)

    def t_details():
        ctx, page, errors = fresh(browser, tokens=12)
        ask(page); page.wait_for_selector(".source-panel summary"); page.wait_for_timeout(250)
        page.evaluate("document.querySelector('.source-panel').__keep = 1")
        page.click(".source-panel summary"); page.wait_for_timeout(100)
        was_open = page.evaluate("document.querySelector('.source-panel').open")
        page.wait_for_timeout(1300)
        still = page.evaluate("(d => !!d && d.open && d.__keep === 1)(document.querySelector('.source-panel'))")
        record("2 Sources <details> stays open while the answer streams", was_open and still, f"openBefore={was_open} openAfter={still}")
        ctx.close()
    guarded("2", t_details)

    def t_scroll_up():
        ctx, page, errors = fresh(browser, tokens=40, paragraphs=True, interval=60)
        ask(page); page.wait_for_timeout(1000)
        page.evaluate("document.querySelector('#log').scrollTop = 0")
        page.wait_for_timeout(1200)
        top = page.evaluate("document.querySelector('#log').scrollTop")
        scrollable = page.evaluate("(l => l.scrollHeight - l.clientHeight)(document.querySelector('#log'))")
        record("3a Auto-scroll respects a user who scrolled up", top < 40 and scrollable > 200, f"scrollTop={top} scrollable={scrollable}")
        ctx.close()
    guarded("3a", t_scroll_up)

    def t_scroll_follow():
        ctx, page, errors = fresh(browser, tokens=40, paragraphs=True, interval=40)
        ask(page); page.wait_for_timeout(2600)
        dist = page.evaluate("(l => l.scrollHeight - l.scrollTop - l.clientHeight)(document.querySelector('#log'))")
        record("3b Auto-scroll follows the answer when already at the bottom", dist < 5, f"distanceFromBottom={dist}")
        ctx.close()
    guarded("3b", t_scroll_follow)

    def t_a11y():
        ctx, page, errors = fresh(browser, tokens=8)
        smooth = page.evaluate("getComputedStyle(document.querySelector('#log')).scrollBehavior")
        live = page.get_attribute("#log", "aria-live")
        ask(page); page.wait_for_timeout(400)
        during = page.evaluate("(document.querySelector('#chatStatus')||{}).textContent || ''")
        page.wait_for_timeout(1200)
        after = page.evaluate("(document.querySelector('#chatStatus')||{}).textContent || ''")
        record("4 Log: no smooth-scroll, aria-live off; one announcement only when answer finishes",
               smooth == "auto" and live == "off" and during == "" and "Answer ready" in after, f"scrollBehavior={smooth} logLive={live} duringStream={during!r} afterDone={after[:30]!r}")
        ctx.close()
    guarded("4", t_a11y)

    def t_stop():
        ctx, page, errors = fresh(browser, tokens=60)
        ask(page); page.wait_for_timeout(450)
        stop_visible = page.locator("#stopAnswer").is_visible() and not page.locator("#sendQuestion").is_visible()
        page.click("#stopAnswer"); page.wait_for_timeout(350)
        aborted = page.evaluate("window.__chat.aborted")
        note = page.locator(".message-error.is-note").inner_text() if page.locator(".message-error.is-note").count() else ""
        partial = "word0" in page.locator(".is-assistant .rich-content").inner_text()
        back = page.locator("#sendQuestion").is_visible() and not page.locator("#stopAnswer").is_visible()
        page.evaluate("window.__chat.tokens = 3")
        ask(page, "second question"); page.wait_for_timeout(900)
        n = page.locator(".chat-message").count()
        record("5 Stop button aborts the request, keeps partial text, UI recovers", stop_visible and aborted == 1 and "stopped" in note.lower() and partial and back and n == 4,
               f"stopShown={stop_visible} aborted={aborted} note={note[:24]!r} partial={partial} recovered={back} msgs={n}")
        ctx.close()
    guarded("5", t_stop)

    def t_retry():
        ctx, page, errors = fresh(browser, mode="fail")
        ask(page, "why is the sky blue"); page.wait_for_timeout(500)
        err = page.locator(".message-error").inner_text() if page.locator(".message-error").count() else ""
        has_retry = page.locator(".message-retry").count() == 1
        page.evaluate("Object.assign(window.__chat, {mode:'ok', tokens:3})")
        page.click(".message-retry"); page.wait_for_timeout(900)
        n = page.locator(".chat-message").count()
        txt = page.locator(".is-assistant .rich-content").inner_text()
        calls = page.evaluate("window.__chat.calls.map(c => c.question)")
        gone = page.locator(".message-error").count() == 0
        record("6a Retry re-asks the same question in place after a failure", "overloaded" in err and has_retry and n == 2 and "word2" in txt and gone and calls == ["why is the sky blue"] * 2,
               f"err={err[:30]!r} retryShown={has_retry} msgs={n} calls={len(calls)}")
        ctx.close()
    guarded("6a", t_retry)

    def t_retry_last_only():
        ctx, page, errors = fresh(browser, mode="fail")
        ask(page, "first"); page.wait_for_timeout(400)
        page.evaluate("Object.assign(window.__chat, {mode:'ok', tokens:2})")
        ask(page, "second"); page.wait_for_timeout(800)
        retries = page.locator(".message-retry").count()
        record("6b Older failed answers lose their Retry button once you ask something new", retries == 0 and page.locator(".chat-message").count() == 4, f"retryButtons={retries}")
        ctx.close()
    guarded("6b", t_retry_last_only)

    def t_nodone():
        ctx, page, errors = fresh(browser, mode="nodone", tokens=3)
        ask(page); page.wait_for_timeout(900)
        err = page.locator(".message-error").inner_text() if page.locator(".message-error").count() else ""
        partial = "word0" in page.locator(".is-assistant .rich-content").inner_text()
        record("7 Connection that drops before 'done' shows an error, keeps partial answer + Retry", "closed before" in err and partial and page.locator(".message-retry").count() == 1, f"err={err[:40]!r}")
        ctx.close()
    guarded("7", t_nodone)

    def t_persist():
        ctx, page, errors = fresh(browser, tokens=4)
        ask(page, "persist me"); page.wait_for_timeout(900)
        page.reload(); page.wait_for_timeout(800)
        n = page.locator(".chat-message").count()
        txt = page.locator(".is-user").inner_text() + page.locator(".is-assistant").inner_text()
        kept = n == 2 and "persist me" in txt and "word3" in txt
        page.click("#reset"); page.wait_for_timeout(300)
        cleared = page.locator(".chat-message").count() == 0 and page.locator(".chat-empty-state").count() == 1
        page.reload(); page.wait_for_timeout(800)
        still_cleared = page.locator(".chat-message").count() == 0
        record("8a Chat history persists per lecture across refresh; New chat clears it for good", kept and cleared and still_cleared, f"kept={kept} cleared={cleared} afterReload={still_cleared}")
        ctx.close()
    guarded("8a", t_persist)

    def t_interrupted():
        ctx, page, errors = fresh(browser, tokens=60)
        ask(page); page.wait_for_timeout(400)
        page.reload(); page.wait_for_timeout(800)
        err = page.locator(".message-error").inner_text() if page.locator(".message-error").count() else ""
        record("8b Refreshing mid-answer restores an 'interrupted' message with Retry (no stuck spinner)", "interrupted" in err.lower() and page.locator(".message-retry").count() == 1 and page.locator(".thinking-state").count() == 0, f"err={err[:40]!r}")
        ctx.close()
    guarded("8b", t_interrupted)

    def t_tabswitch():
        ctx, page, errors = fresh(browser, tokens=40)
        ask(page); page.wait_for_timeout(350)
        page.click('[data-tab="Summary"]'); page.wait_for_timeout(300)
        page.click('[data-tab="Chat"]'); page.wait_for_timeout(200)
        busy = page.locator("#stopAnswer").is_visible()
        page.wait_for_function("document.querySelector('.is-assistant .rich-content').innerText.includes('word39')", timeout=8000)
        page.wait_for_timeout(200)
        txt = page.locator(".is-assistant .rich-content").inner_text()
        record("9 Leaving and returning to Chat mid-answer keeps streaming into the new view", busy and "word39" in txt and page.locator("[data-copy-answer]").count() == 1 and not errors, f"stopVisibleOnReturn={busy} errors={errors[:1]}")
        ctx.close()
    guarded("9", t_tabswitch)

    def t_table_chat():
        tbl = ["| Traversal | Order |\n", "|:--|--:|\n", "| BFS | level |\n", "| DFS | depth |\n\n", "Done."]
        ctx, page, errors = fresh(browser, fixed=tbl, interval=50)
        ask(page); page.wait_for_timeout(1000)
        ths = page.locator(".rich-table th").count(); trs = page.locator(".rich-table tbody tr").count()
        align = page.evaluate("document.querySelectorAll('.rich-table th')[1].style.textAlign")
        record("10a Chat answers render Markdown tables (header, rows, alignment)", ths == 2 and trs == 2 and align == "right", f"th={ths} rows={trs} align={align}")
        ctx.close()
    guarded("10a", t_table_chat)

    def t_table_unit():
        ctx, page, errors = fresh(browser)
        r = page.evaluate("""() => {
          const t1 = renderRichText("| Name | Score |\\n|:---|---:|\\n| `a|b` | **9** |\\n| x | 10 |\\n\\nAfter");
          const t2 = renderRichText("a | b\\nsome text");
          const t3 = renderRichText("x | y\\n---");
          const t4 = renderRichText("| a \\\\| b | c |\\n|---|---|\\n| 1 | 2 |");
          const d = new DOMParser().parseFromString(t1, 'text/html');
          return {rows: d.querySelectorAll('tbody tr').length, code: (d.querySelector('td code')||{}).textContent, strong: !!d.querySelector('td strong'),
                  after: t1.includes('After'), t2: t2.includes('<table'), t3: t3.includes('<table'), t3hr: t3.includes('<hr'),
                  h4: [...new DOMParser().parseFromString(t4,'text/html').querySelectorAll('th')].map(x=>x.textContent)};
        }""")
        ok = r["rows"] == 2 and r["code"] == "a|b" and r["strong"] and r["after"] and not r["t2"] and not r["t3"] and r["t3hr"] and r["h4"] == ["a | b", "c"]
        record("10b Table parser: pipes in `code`, escaped pipes, no false positives", ok, str(r))
        ctx.close()
    guarded("10b", t_table_unit)

    def t_outline():
        ctx, page, errors = fresh(browser)
        r = page.evaluate("""() => {
          const md = "# Intro\\n\\n```python\\n# not a heading\\n- not an item\\n1. nor this\\n```\\n\\n- Real item one\\n- Real item two\\n\\n## Second";
          const names = extractSummarySections(md);
          const html = renderRichText(md, {headingPrefix: 'summary'});
          const ids = (html.match(/id="summary-section-\\d+"/g) || []).length;
          return {names, ids};
        }""")
        record("11 Summary outline skips code fences and matches the rendered headings", r["names"] == ["Intro", "Real item one", "Real item two", "Second"] and r["ids"] == len(r["names"]), str(r))
        ctx.close()
    guarded("11", t_outline)

    def t_user_bubble():
        ctx, page, errors = fresh(browser, tokens=2)
        ask(page, "Explain trees"); page.wait_for_timeout(500)
        w = page.evaluate("document.querySelector('.user-bubble').getBoundingClientRect().width")
        ctx.close()
        ctx, page, errors = fresh(browser, tokens=2)
        page.set_viewport_size({"width": 390, "height": 800}); page.reload(); page.wait_for_timeout(700)
        ask(page, "Explain trees"); page.wait_for_timeout(500)
        wm = page.evaluate("document.querySelector('.user-bubble').getBoundingClientRect().width")
        record("12 Your own question bubble is readable (was squeezed to ~50px by a CSS override)", w > 100 and wm > 100, f"desktop={w:.0f}px mobile={wm:.0f}px")
        ctx.close()
    guarded("12", t_user_bubble)

    browser.close()

srv.shutdown()
failed = [r for r in results if not r[1]]
print(f"\n{len(results)-len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)