import html

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def workbench(request: Request) -> HTMLResponse:
    root_path = str(request.scope.get("root_path") or "").rstrip("/")
    escaped_root_path = html.escape(root_path, quote=True)
    return HTMLResponse(
        f"""<!doctype html>
<html lang="zh-CN" data-root-path="{escaped_root_path}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AIPPT</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #1c2430;
      --muted: #667085;
      --line: #d8dee8;
      --accent: #176b5b;
      --accent-strong: #0f4e43;
      --warn: #9a3412;
      --ready: #126a3a;
      --shadow: 0 10px 30px rgba(18, 32, 50, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    button, input, textarea {{ font: inherit; }}
    a {{ color: var(--accent); }}
    .shell {{ max-width: 1180px; margin: 0 auto; padding: 28px 20px 44px; }}
    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 20px;
    }}
    .brand {{ display: flex; align-items: baseline; gap: 12px; min-width: 0; }}
    .brand h1 {{ margin: 0; font-size: 26px; line-height: 1.15; letter-spacing: 0; }}
    .brand span {{ color: var(--muted); white-space: nowrap; }}
    .userbar {{ display: flex; align-items: center; gap: 10px; color: var(--muted); }}
    .layout {{ display: grid; grid-template-columns: minmax(320px, 0.9fr) minmax(360px, 1.1fr); gap: 18px; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      min-width: 0;
    }}
    .panel header {{
      padding: 16px 18px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .panel h2 {{ margin: 0; font-size: 16px; line-height: 1.2; letter-spacing: 0; }}
    .form {{ padding: 18px; display: grid; gap: 14px; }}
    label {{ display: grid; gap: 7px; color: var(--muted); font-size: 13px; }}
    input, textarea {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      padding: 10px 11px;
      outline: none;
    }}
    textarea {{ min-height: 320px; resize: vertical; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    input:focus, textarea:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px rgba(23, 107, 91, 0.14); }}
    .btn {{
      appearance: none;
      border: 1px solid transparent;
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      padding: 10px 13px;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
    }}
    .btn:hover {{ background: var(--accent-strong); }}
    .btn.secondary {{ background: #fff; color: var(--text); border-color: var(--line); }}
    .btn.secondary:hover {{ border-color: #a8b3c4; }}
    .btn:disabled {{ opacity: 0.55; cursor: wait; }}
    .toolbar {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
    .empty {{ padding: 28px 18px; color: var(--muted); }}
    .list {{ display: grid; gap: 10px; padding: 12px; }}
    .deck {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
      display: grid;
      gap: 9px;
    }}
    .deck-title {{ font-weight: 650; overflow-wrap: anywhere; }}
    .meta {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; color: var(--muted); font-size: 13px; }}
    .pill {{ border: 1px solid var(--line); border-radius: 999px; padding: 2px 8px; background: #f8fafc; }}
    .pill.ready {{ color: var(--ready); border-color: rgba(18, 106, 58, 0.25); background: #f0f8f3; }}
    .pill.failed {{ color: var(--warn); border-color: rgba(154, 52, 18, 0.25); background: #fff4ed; }}
    .deck-actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .notice {{
      margin-bottom: 14px;
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 8px;
      padding: 12px 14px;
      color: var(--muted);
      display: none;
    }}
    .notice.show {{ display: block; }}
    .login {{
      margin: 80px auto 0;
      max-width: 460px;
      padding: 24px;
      text-align: center;
    }}
    .login h1 {{ margin: 0 0 10px; font-size: 26px; letter-spacing: 0; }}
    .login p {{ margin: 0 0 18px; color: var(--muted); }}
    @media (max-width: 820px) {{
      .shell {{ padding: 18px 12px 32px; }}
      .topbar {{ align-items: flex-start; }}
      .brand {{ display: grid; gap: 4px; }}
      .brand span {{ white-space: normal; }}
      .layout {{ grid-template-columns: 1fr; }}
      textarea {{ min-height: 260px; }}
    }}
  </style>
</head>
<body>
  <main id="app" class="shell" aria-live="polite"></main>
  <script>
    const rootPath = document.documentElement.dataset.rootPath || "";
    const api = rootPath + "/api";
    const app = document.getElementById("app");
    const sampleOutline = "请制作 5-6 页 PPT，关于机器学习的科普。";
    let decks = [];
    let filesByDeck = new Map();
    let busy = false;

    function escapeHtml(value) {{
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({{
        "&": "&amp;", "<": "&lt;", ">": "&gt;", "\\"": "&quot;", "'": "&#39;"
      }}[char]));
    }}

    async function request(path, options = {{}}) {{
      const response = await fetch(api + path, {{
        credentials: "same-origin",
        headers: {{ "Content-Type": "application/json", ...(options.headers || {{}}) }},
        ...options
      }});
      if (!response.ok) {{
        let detail = response.statusText;
        try {{ detail = (await response.json()).detail || detail; }} catch (_) {{}}
        throw new Error(detail);
      }}
      if (response.status === 204) return null;
      return response.json();
    }}

    async function boot() {{
      try {{
        const user = await request("/auth/me");
        await loadDecks();
        renderWorkbench(user);
        window.setInterval(refreshDecksQuietly, 5000);
      }} catch (error) {{
        renderLogin();
      }}
    }}

    function renderLogin() {{
      const next = encodeURIComponent(rootPath + "/");
      app.innerHTML = `
        <section class="panel login">
          <h1>AIPPT</h1>
          <p>上海交通大学 AI PPT 工作台</p>
          <a class="btn" href="${{api}}/auth/jaccount/login?next=${{next}}">jAccount 登录</a>
        </section>
      `;
    }}

    async function loadDecks() {{
      decks = await request("/decks");
      filesByDeck = new Map();
      await Promise.all(decks.map(async (deck) => {{
        try {{
          filesByDeck.set(deck.id, await request(`/files/decks/${{deck.id}}`));
        }} catch (_) {{
          filesByDeck.set(deck.id, []);
        }}
      }}));
    }}

    async function refreshDecksQuietly() {{
      if (busy) return;
      const hasActive = decks.some((deck) => ["generating", "outline_ready"].includes(deck.status));
      if (!hasActive && decks.length > 0) return;
      try {{
        await loadDecks();
        const me = await request("/auth/me");
        renderWorkbench(me);
      }} catch (_) {{}}
    }}

    function renderWorkbench(user) {{
      const userName = user.jaccount || user.display_name || "me";
      app.innerHTML = `
        <div class="topbar">
          <div class="brand">
            <h1>AIPPT</h1>
            <span>AI PPT 生成工作台</span>
          </div>
          <div class="userbar">
            <span>${{escapeHtml(userName)}}</span>
            <a class="btn secondary" href="${{api}}/auth/logout">退出</a>
          </div>
        </div>
        <div id="notice" class="notice"></div>
        <div class="layout">
          <section class="panel">
            <header><h2>新建 PPT</h2></header>
            <form id="deck-form" class="form">
              <label>标题
                <input id="title" name="title" maxlength="160" value="机器学习科普" required>
              </label>
              <label>需求或大纲
                <textarea id="outline" name="outline" required>${{sampleOutline}}</textarea>
              </label>
              <div class="toolbar">
                <button id="submit" class="btn" type="submit">生成 PPTX</button>
                <button class="btn secondary" type="button" id="refresh">刷新</button>
              </div>
            </form>
          </section>
          <section class="panel">
            <header>
              <h2>我的 PPT</h2>
              <span class="meta">${{decks.length}} 个</span>
            </header>
            ${{renderDeckList()}}
          </section>
        </div>
      `;
      document.getElementById("deck-form").addEventListener("submit", createDeck);
      document.getElementById("refresh").addEventListener("click", async () => {{
        await loadDecks();
        renderWorkbench(user);
      }});
    }}

    function renderDeckList() {{
      if (decks.length === 0) return `<div class="empty">暂无 PPT</div>`;
      return `<div class="list">${{decks.map(renderDeck).join("")}}</div>`;
    }}

    function renderDeck(deck) {{
      const files = filesByDeck.get(deck.id) || [];
      const pptx = files.find((file) => file.kind === "pptx");
      const preview = files.find((file) => file.kind === "preview");
      const review = files.find((file) => file.kind === "review");
      const created = new Date(deck.created_at).toLocaleString();
      return `
        <article class="deck">
          <div class="deck-title">${{escapeHtml(deck.title)}}</div>
          <div class="meta">
            <span class="pill ${{statusClass(deck.status)}}">${{statusLabel(deck.status)}}</span>
            <span>${{escapeHtml(created)}}</span>
          </div>
          <div class="deck-actions">
            ${{pptx ? `<a class="btn" href="${{api}}/files/${{pptx.id}}/download">下载 PPTX</a>` : ""}}
            ${{preview ? `<a class="btn secondary" href="${{api}}/files/${{preview.id}}/download">预览</a>` : ""}}
            ${{review ? `<a class="btn secondary" href="${{api}}/files/${{review.id}}/download">审稿报告</a>` : ""}}
            <button class="btn secondary" type="button" data-build="${{deck.id}}">重新生成</button>
            <button class="btn secondary" type="button" data-review="${{deck.id}}">AI 审稿</button>
          </div>
        </article>
      `;
    }}

    function statusClass(status) {{
      if (status === "ready") return "ready";
      if (status === "failed") return "failed";
      return "";
    }}

    function statusLabel(status) {{
      return {{
        draft: "草稿",
        outline_ready: "大纲完成",
        generating: "生成中",
        ready: "可下载",
        failed: "失败"
      }}[status] || status;
    }}

    async function createDeck(event) {{
      event.preventDefault();
      busy = true;
      setBusy(true);
      try {{
        const title = document.getElementById("title").value.trim();
        const outline = document.getElementById("outline").value;
        const deck = await request("/decks", {{
          method: "POST",
          body: JSON.stringify({{ title, outline_md: outline }})
        }});
        await request(`/jobs/decks/${{deck.id}}`, {{
          method: "POST",
          body: JSON.stringify({{ type: "build_pptx" }})
        }});
        showNotice("任务已创建");
        await loadDecks();
        const me = await request("/auth/me");
        renderWorkbench(me);
      }} catch (error) {{
        showNotice(error.message || "提交失败");
      }} finally {{
        busy = false;
        setBusy(false);
      }}
    }}

    app.addEventListener("click", async (event) => {{
      const button = event.target.closest("[data-build]");
      if (!button) return;
      button.disabled = true;
      try {{
        await request(`/jobs/decks/${{button.dataset.build}}`, {{
          method: "POST",
          body: JSON.stringify({{ type: "build_pptx" }})
        }});
        await loadDecks();
        const me = await request("/auth/me");
        renderWorkbench(me);
      }} catch (error) {{
        showNotice(error.message || "提交失败");
      }} finally {{
        button.disabled = false;
      }}
    }});

    app.addEventListener("click", async (event) => {{
      const button = event.target.closest("[data-review]");
      if (!button) return;
      button.disabled = true;
      try {{
        await request(`/jobs/decks/${{button.dataset.review}}`, {{
          method: "POST",
          body: JSON.stringify({{ type: "hermes_review" }})
        }});
        await loadDecks();
        const me = await request("/auth/me");
        renderWorkbench(me);
      }} catch (error) {{
        showNotice(error.message || "审稿失败");
      }} finally {{
        button.disabled = false;
      }}
    }});

    function setBusy(value) {{
      const submit = document.getElementById("submit");
      if (submit) submit.disabled = value;
    }}

    function showNotice(text) {{
      const notice = document.getElementById("notice");
      if (!notice) return;
      notice.textContent = text;
      notice.classList.add("show");
    }}

    boot();
  </script>
</body>
</html>"""
    )
