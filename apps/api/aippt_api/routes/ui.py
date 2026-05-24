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
    .pill.running {{ color: var(--accent-strong); border-color: rgba(23, 107, 91, 0.25); background: #edf7f4; }}
    .pill.ready {{ color: var(--ready); border-color: rgba(18, 106, 58, 0.25); background: #f0f8f3; }}
    .pill.failed {{ color: var(--warn); border-color: rgba(154, 52, 18, 0.25); background: #fff4ed; }}
    .deck-actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .outline-preview {{
      border-top: 1px solid var(--line);
      padding-top: 8px;
      color: var(--muted);
      font-size: 13px;
    }}
    .outline-preview summary {{ cursor: pointer; color: var(--text); font-weight: 650; }}
    .outline-preview pre {{
      margin: 8px 0 0;
      max-height: 240px;
      overflow: auto;
      white-space: pre-wrap;
      color: var(--text);
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      font: 12px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace;
    }}
    .agent-progress {{
      border-top: 1px solid var(--line);
      padding-top: 10px;
      display: grid;
      gap: 9px;
    }}
    .agent-head {{ display: flex; justify-content: space-between; gap: 10px; color: var(--muted); font-size: 13px; }}
    .agent-head strong {{ color: var(--text); }}
    .agent-steps {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; }}
    .agent-step {{
      border: 1px solid var(--line);
      background: #f8fafc;
      color: var(--muted);
      border-radius: 6px;
      padding: 7px 8px;
      min-height: 34px;
      font-size: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      text-align: center;
    }}
    .agent-step strong {{
      width: 20px;
      height: 20px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: #e8edf3;
      color: var(--muted);
      font-size: 11px;
      flex: 0 0 auto;
    }}
    .agent-step.done {{ border-color: rgba(18, 106, 58, 0.25); background: #f0f8f3; color: var(--ready); }}
    .agent-step.running {{ border-color: rgba(23, 107, 91, 0.35); background: #edf7f4; color: var(--accent-strong); }}
    .agent-step.failed {{ border-color: rgba(154, 52, 18, 0.25); background: #fff4ed; color: var(--warn); }}
    .agent-step.done strong {{ background: var(--ready); color: #fff; }}
    .agent-step.running strong {{ background: var(--accent); color: #fff; }}
    .agent-step.failed strong {{ background: var(--warn); color: #fff; }}
    .agent-log {{
      margin: 0;
      max-height: 150px;
      overflow: auto;
      white-space: pre-wrap;
      color: var(--muted);
      background: #fbfcfe;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px;
      font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
    }}
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
      .agent-steps {{ grid-template-columns: 1fr 1fr; }}
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
    let jobsByDeck = new Map();
    let jobLogs = new Map();
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
      jobsByDeck = new Map();
      jobLogs = new Map();
      await Promise.all(decks.map(async (deck) => {{
        try {{
          filesByDeck.set(deck.id, await request(`/files/decks/${{deck.id}}`));
        }} catch (_) {{
          filesByDeck.set(deck.id, []);
        }}
        try {{
          const jobs = await request(`/jobs/decks/${{deck.id}}`);
          jobsByDeck.set(deck.id, jobs);
          await Promise.all(jobs.slice(0, 3).map(async (job) => {{
            const log = await request(`/jobs/${{job.id}}/log`);
            jobLogs.set(job.id, log.log_text || "");
          }}));
        }} catch (_) {{
          jobsByDeck.set(deck.id, []);
        }}
      }}));
    }}

    async function refreshDecksQuietly() {{
      if (busy) return;
      const hasActive = decks.some((deck) => deck.status === "generating");
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
                <button id="submit" class="btn" type="submit">生成 PPT</button>
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
      const jobs = jobsByDeck.get(deck.id) || [];
      const created = formatTime(deck.created_at);
      return `
        <article class="deck">
          <div class="deck-title">${{escapeHtml(deck.title)}}</div>
          <div class="meta">
            <span class="pill ${{statusClass(deck.status)}}">${{statusLabel(deck.status)}}</span>
            <span>${{escapeHtml(created)}}</span>
          </div>
          ${{pptx ? `<div class="deck-actions"><a class="btn" href="${{api}}/files/${{pptx.id}}/download">下载 PPTX</a></div>` : ""}}
          ${{renderAgentProgress(deck, jobs)}}
        </article>
      `;
    }}

    function renderAgentProgress(deck, jobs) {{
      if (!jobs.length) return "";
      const plan = jobs.find((job) => job.type === "plan_outline");
      const build = jobs.find((job) => job.type === "build_pptx");
      if (!plan && !build) return "";
      const labels = ["理解需求", "Hermes/MiMo 规划", "PPTX 渲染", "完成下载"];
      const failedJob = [plan, build].find((job) => job && job.status === "failed");
      const isDone = Boolean(build && build.status === "succeeded");
      const isFailed = Boolean(failedJob);
      let activeIndex = 0;
      if (plan && plan.status === "running") activeIndex = 1;
      if (plan && plan.status === "succeeded") activeIndex = 2;
      if (build && ["queued", "running"].includes(build.status)) activeIndex = 2;
      if (isDone) activeIndex = 3;
      if (isFailed && failedJob.type === "build_pptx") activeIndex = 2;
      const statusText = isDone ? "完成" : isFailed ? "失败" : "进行中";
      const title = "Agent 生成流程";
      const displayJob = build || plan;
      const steps = labels.map((label, index) => {{
        let cls = "";
        if (isDone || index < activeIndex) cls = "done";
        else if (isFailed && index === activeIndex) cls = "failed";
        else if (index === activeIndex) cls = "running";
        return `<span class="agent-step ${{cls}}"><strong>${{index + 1}}</strong>${{escapeHtml(label)}}</span>`;
      }}).join("");
      const log = formatAgentLog([plan, build].map((job) => job ? jobLogs.get(job.id) || "" : "").join("\\n"));
      return `
        <div class="agent-progress">
          <div class="agent-head">
            <strong>${{escapeHtml(title)}} · ${{escapeHtml(statusText)}}</strong>
            <span>${{escapeHtml(formatTime(displayJob.created_at))}}</span>
          </div>
          <div class="agent-steps">${{steps}}</div>
          ${{log ? `<pre class="agent-log">${{escapeHtml(log)}}</pre>` : ""}}
        </div>
      `;
    }}

    function statusClass(status) {{
      if (status === "generating") return "running";
      if (status === "ready") return "ready";
      if (status === "failed") return "failed";
      return "";
    }}

    function statusLabel(status) {{
      return {{
        draft: "草稿",
        outline_ready: "规划完成",
        generating: "生成中",
        ready: "可下载",
        failed: "失败"
      }}[status] || status;
    }}

    function jobStatusLabel(status) {{
      return {{
        queued: "排队中",
        running: "进行中",
        succeeded: "完成",
        failed: "失败",
        canceled: "已取消"
      }}[status] || status;
    }}

    async function createDeck(event) {{
      event.preventDefault();
      await createDeckWithJob("plan_outline");
    }}

    async function createDeckWithJob(jobType) {{
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
          body: JSON.stringify({{ type: jobType }})
        }});
        showNotice(jobType === "plan_outline" ? "已开始深度规划" : "任务已创建");
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

    function setBusy(value) {{
      const submit = document.getElementById("submit");
      if (submit) submit.disabled = value;
    }}

    function formatTime(value) {{
      return new Intl.DateTimeFormat("zh-CN", {{
        timeZone: "Asia/Shanghai",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
      }}).format(new Date(value));
    }}

    function formatAgentLog(logText) {{
      const lines = String(logText || "")
        .split("\\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => line.startsWith("AIPPT_AGENT:") ? line.slice("AIPPT_AGENT:".length).trim() : "")
        .filter(Boolean);
      return lines.slice(-8).join("\\n");
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
