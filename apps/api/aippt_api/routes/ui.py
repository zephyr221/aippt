import html

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def workbench(request: Request) -> HTMLResponse:
    root_path = str(request.scope.get("root_path") or "").rstrip("/")
    escaped_root_path = html.escape(root_path, quote=True)
    return HTMLResponse(
        """<!doctype html>
<html lang="zh-CN" data-root-path="__ROOT_PATH__">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AIPPT</title>
  <style>
    :root {
      color-scheme: light;
      --canvas: #ffffff;
      --rail: #fafafa;
      --surface: #ffffff;
      --subtle: #f5f6f8;
      --line: rgba(15, 18, 28, 0.075);
      --line-soft: rgba(15, 18, 28, 0.045);
      --line-hard: rgba(15, 18, 28, 0.14);
      --ink: #0e1117;
      --ink-2: #3f4654;
      --ink-3: #6b7280;
      --ink-4: #a1a6b0;
      --accent: #2c3e78;
      --accent-2: #4659a0;
      --accent-soft: rgba(44, 62, 120, 0.07);
      --accent-line: rgba(44, 62, 120, 0.2);
      --ready: #127047;
      --ready-soft: rgba(18, 112, 71, 0.08);
      --warn: #a03a16;
      --warn-soft: rgba(160, 58, 22, 0.08);
      --shadow-soft: 0 1px 2px rgba(15, 18, 28, 0.04), 0 18px 44px -28px rgba(15, 18, 28, 0.18);
      --mono: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, monospace;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--canvas);
      color: var(--ink);
      font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Noto Sans SC", "Microsoft YaHei", sans-serif;
      letter-spacing: 0;
    }

    button,
    input,
    textarea {
      font: inherit;
      letter-spacing: 0;
    }

    button,
    a {
      -webkit-tap-highlight-color: transparent;
    }

    a {
      color: inherit;
      text-decoration: none;
    }

    svg {
      display: block;
      flex: 0 0 auto;
    }

    .app-root {
      min-height: 100vh;
    }

    .app-shell {
      display: grid;
      grid-template-columns: 268px minmax(0, 1fr);
      min-height: 100vh;
      height: 100vh;
      overflow: hidden;
      background: var(--canvas);
    }

    .side {
      min-width: 0;
      height: 100vh;
      background: var(--rail);
      box-shadow: 1px 0 0 var(--line);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .side-head {
      height: 58px;
      padding: 0 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex: 0 0 auto;
    }

    .brand {
      display: inline-flex;
      align-items: center;
      gap: 9px;
      min-width: 0;
      color: var(--ink);
      font-weight: 730;
      font-size: 17px;
      line-height: 1;
      white-space: nowrap;
    }

    .brand-mark {
      width: 24px;
      height: 24px;
      display: grid;
      place-items: center;
      color: var(--ink);
    }

    .side-create {
      width: 28px;
      height: 28px;
      border: 0;
      border-radius: 7px;
      background: transparent;
      color: var(--accent);
      display: grid;
      place-items: center;
      cursor: pointer;
    }

    .side-create:hover {
      background: var(--line-soft);
      color: var(--ink);
    }

    .side-nav,
    .side-section {
      padding: 8px 10px;
      display: grid;
      gap: 2px;
    }

    .side-section {
      border-top: 1px solid var(--line-soft);
      margin-top: 6px;
      padding-top: 16px;
      min-height: 0;
      overflow: auto;
    }

    .side-section-title {
      padding: 0 10px 8px;
      color: var(--ink-4);
      font-size: 12px;
      font-weight: 650;
    }

    .side-row,
    .side-deck {
      width: 100%;
      min-width: 0;
      border: 0;
      border-radius: 7px;
      background: transparent;
      color: var(--ink-3);
      display: grid;
      grid-template-columns: 18px minmax(0, 1fr) auto;
      align-items: center;
      gap: 9px;
      min-height: 34px;
      padding: 0 10px;
      text-align: left;
      cursor: pointer;
    }

    .side-row:hover,
    .side-deck:hover {
      background: var(--line-soft);
      color: var(--ink);
    }

    .side-row.is-active {
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 650;
    }

    .side-row span,
    .side-deck span {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .side-row em,
    .side-deck em {
      color: var(--ink-4);
      font-style: normal;
      font-size: 12px;
      white-space: nowrap;
    }

    .side-deck {
      font-size: 13px;
      min-height: 32px;
      grid-template-columns: 16px minmax(0, 1fr);
    }

    .side-empty {
      padding: 8px 10px;
      color: var(--ink-4);
      font-size: 13px;
    }

    .side-user {
      margin-top: auto;
      padding: 12px 14px 14px;
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr) 30px;
      align-items: center;
      gap: 10px;
      border-top: 1px solid var(--line-soft);
    }

    .avatar {
      width: 34px;
      height: 34px;
      border-radius: 999px;
      display: grid;
      place-items: center;
      background: #2f4d91;
      color: #fff;
      font-weight: 720;
      font-size: 14px;
    }

    .side-user-meta {
      min-width: 0;
      display: grid;
      gap: 1px;
    }

    .side-user-name {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: var(--ink);
      font-weight: 650;
      line-height: 1.2;
    }

    .side-user-sub {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: var(--ink-4);
      font-size: 12px;
    }

    .icon-link,
    .icon-button {
      width: 30px;
      height: 30px;
      border: 0;
      border-radius: 7px;
      background: transparent;
      color: var(--ink-4);
      display: grid;
      place-items: center;
      cursor: pointer;
    }

    .icon-link:hover,
    .icon-button:hover {
      background: var(--line-soft);
      color: var(--ink);
    }

    .workspace {
      position: relative;
      min-width: 0;
      height: 100vh;
      overflow-y: auto;
      overflow-x: hidden;
      background: var(--canvas);
    }

    .top-tools {
      position: absolute;
      top: 22px;
      right: 28px;
      display: flex;
      align-items: center;
      gap: 8px;
      z-index: 10;
    }

    .deck-search-wrap {
      width: min(340px, 38vw);
      height: 36px;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 0 12px;
      border-radius: 999px;
      background: var(--surface);
      color: var(--ink-4);
      box-shadow: 0 0 0 1px var(--line), 0 1px 2px rgba(15, 18, 28, 0.03);
      transition: box-shadow 0.15s ease;
    }

    .deck-search-wrap:focus-within,
    .deck-search-wrap:hover {
      box-shadow: 0 0 0 1px var(--line-hard), 0 1px 3px rgba(15, 18, 28, 0.05);
    }

    .deck-search {
      min-width: 0;
      width: 100%;
      border: 0;
      outline: 0;
      background: transparent;
      color: var(--ink);
      font-size: 13px;
    }

    .deck-search::placeholder {
      color: var(--ink-4);
    }

    .mobile-user {
      display: none;
      align-items: center;
      gap: 8px;
      color: var(--ink-3);
      font-size: 13px;
      white-space: nowrap;
    }

    .hero {
      width: 100%;
      max-width: 760px;
      min-height: 100vh;
      margin: 0 auto;
      padding: 92px 32px 54px;
      display: flex;
      flex-direction: column;
    }

    .scope-head {
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      margin: 0 0 36px;
    }

    .scope-eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--ink-3);
      font-size: 13px;
      font-weight: 500;
      margin-bottom: 14px;
    }

    .scope-eyebrow svg {
      color: var(--ink-4);
    }

    .scope-title {
      margin: 0;
      color: var(--ink);
      font-size: 44px;
      line-height: 1.08;
      font-weight: 680;
      letter-spacing: 0;
    }

    .scope-tabs {
      margin-top: 24px;
      padding: 4px;
      border-radius: 9px;
      background: var(--subtle);
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .scope-tab {
      height: 30px;
      border: 0;
      border-radius: 6px;
      background: transparent;
      color: var(--ink-3);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 0 12px;
      font-size: 13px;
      font-weight: 560;
      white-space: nowrap;
      cursor: pointer;
    }

    .scope-tab:hover {
      color: var(--ink);
    }

    .scope-tab.is-active {
      background: var(--surface);
      color: var(--ink);
      box-shadow: 0 1px 2px rgba(15, 18, 28, 0.05);
      font-weight: 680;
    }

    .scope-tab.is-active svg {
      color: var(--accent);
    }

    .tab-count {
      color: var(--ink-4);
      background: var(--subtle);
      border-radius: 4px;
      padding: 2px 5px;
      font: 650 10px/1 var(--mono);
    }

    .prompt-wrap {
      position: relative;
    }

    .prompt-card {
      background: var(--surface);
      border: 1px solid transparent;
      border-radius: 18px;
      padding: 16px 18px 14px;
      box-shadow: 0 0 0 1px var(--line), 0 1px 2px rgba(15, 18, 28, 0.04),
        0 14px 30px -24px rgba(15, 18, 28, 0.24);
      transition: box-shadow 0.18s ease;
    }

    .prompt-card:hover {
      box-shadow: 0 0 0 1px var(--line-hard), 0 1px 3px rgba(15, 18, 28, 0.06),
        0 18px 34px -24px rgba(15, 18, 28, 0.24);
    }

    .prompt-card:focus-within {
      box-shadow: 0 0 0 1px var(--accent-line), 0 0 0 4px var(--accent-soft),
        0 1px 3px rgba(15, 18, 28, 0.06);
    }

    .title-field {
      display: grid;
      grid-template-columns: 42px minmax(0, 1fr);
      align-items: center;
      gap: 10px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--line-soft);
      color: var(--ink-4);
      font-size: 13px;
      font-weight: 550;
    }

    .title-field input {
      min-width: 0;
      width: 100%;
      border: 0;
      outline: 0;
      background: transparent;
      color: var(--ink);
      font-weight: 650;
      padding: 4px 0;
    }

    .title-field input::placeholder,
    .prompt-card textarea::placeholder {
      color: var(--ink-4);
    }

    .prompt-card textarea {
      width: 100%;
      min-height: 148px;
      max-height: 320px;
      border: 0;
      outline: 0;
      resize: vertical;
      background: transparent;
      color: var(--ink);
      padding: 16px 0 8px;
      font-size: 16px;
      line-height: 1.58;
    }

    .prompt-tools {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      padding-top: 4px;
    }

    .prompt-chip {
      height: 30px;
      border: 0;
      border-radius: 7px;
      background: transparent;
      color: var(--ink-3);
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 0 10px;
      font-size: 13px;
      font-weight: 560;
      cursor: pointer;
      white-space: nowrap;
    }

    .prompt-chip:hover {
      background: var(--line-soft);
      color: var(--ink);
    }

    .spacer {
      flex: 1 1 auto;
      min-width: 10px;
    }

    .primary-action {
      min-height: 34px;
      border: 0;
      border-radius: 8px;
      background: var(--accent);
      color: #fff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 0 13px;
      font-weight: 680;
      cursor: pointer;
      box-shadow: 0 8px 20px -16px rgba(44, 62, 120, 0.8);
    }

    .primary-action:hover {
      background: var(--accent-2);
    }

    .primary-action:disabled {
      opacity: 0.58;
      cursor: wait;
      box-shadow: none;
    }

    .suggestions {
      margin-top: 20px;
      display: flex;
      gap: 8px;
      justify-content: center;
      flex-wrap: wrap;
    }

    .suggestion {
      min-height: 31px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--surface);
      color: var(--ink-2);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 0 13px;
      font-size: 13px;
      font-weight: 520;
      cursor: pointer;
      white-space: nowrap;
    }

    .suggestion:hover {
      border-color: var(--line-hard);
      color: var(--ink);
    }

    .notice {
      display: none;
      margin: 0 0 14px;
      border: 1px solid var(--line);
      background: var(--surface);
      border-radius: 8px;
      color: var(--ink-3);
      padding: 10px 12px;
      font-size: 13px;
    }

    .notice.show {
      display: block;
    }

    .deck-section {
      margin-top: 42px;
      display: grid;
      gap: 10px;
      padding-bottom: 28px;
    }

    .deck-section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 0 2px;
      color: var(--ink-3);
      font-size: 13px;
      font-weight: 560;
    }

    .deck-section-count {
      color: var(--ink-4);
      font-size: 12px;
      white-space: nowrap;
    }

    .deck-list {
      display: grid;
      gap: 10px;
    }

    .deck-row {
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      padding: 13px;
      display: grid;
      gap: 10px;
      box-shadow: 0 1px 2px rgba(15, 18, 28, 0.02);
    }

    .deck-main {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: start;
      gap: 12px;
    }

    .deck-title {
      margin: 0;
      color: var(--ink);
      font-size: 15px;
      font-weight: 690;
      overflow-wrap: anywhere;
      line-height: 1.35;
    }

    .deck-meta {
      margin-top: 5px;
      display: flex;
      align-items: center;
      gap: 7px;
      flex-wrap: wrap;
      color: var(--ink-4);
      font-size: 12px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      border-radius: 999px;
      padding: 0 8px;
      border: 1px solid var(--line);
      background: var(--subtle);
      color: var(--ink-3);
      font-size: 12px;
      font-weight: 650;
      white-space: nowrap;
    }

    .pill.running {
      color: var(--accent);
      border-color: var(--accent-line);
      background: var(--accent-soft);
    }

    .pill.ready {
      color: var(--ready);
      border-color: rgba(18, 112, 71, 0.22);
      background: var(--ready-soft);
    }

    .pill.failed {
      color: var(--warn);
      border-color: rgba(160, 58, 22, 0.22);
      background: var(--warn-soft);
    }

    .deck-actions {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      justify-content: flex-end;
      flex-wrap: wrap;
    }

    .row-action {
      min-height: 32px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      color: var(--ink-2);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      padding: 0 10px;
      font-size: 13px;
      font-weight: 650;
      white-space: nowrap;
    }

    .row-action:hover {
      border-color: var(--line-hard);
      color: var(--ink);
    }

    .row-action.primary {
      border-color: transparent;
      background: var(--ink);
      color: #fff;
    }

    .row-action.primary:hover {
      background: var(--accent);
      color: #fff;
    }

    .outline-preview {
      border-top: 1px solid var(--line-soft);
      padding-top: 8px;
      color: var(--ink-3);
      font-size: 13px;
    }

    .outline-preview summary {
      cursor: pointer;
      color: var(--ink-2);
      font-weight: 650;
    }

    .outline-preview pre {
      margin: 8px 0 0;
      max-height: 220px;
      overflow: auto;
      white-space: pre-wrap;
      color: var(--ink-2);
      background: #fbfcfd;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      font: 12px/1.55 var(--mono);
    }

    .agent-progress {
      border-top: 1px solid var(--line-soft);
      padding-top: 10px;
      display: grid;
      gap: 9px;
    }

    .agent-head {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 10px;
      color: var(--ink-4);
      font-size: 12px;
    }

    .agent-head strong {
      color: var(--ink-2);
      font-size: 13px;
    }

    .agent-steps {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 6px;
    }

    .agent-step {
      min-width: 0;
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
      color: var(--ink-3);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 7px 8px;
      text-align: center;
      font-size: 12px;
      font-weight: 620;
      overflow-wrap: anywhere;
    }

    .agent-step strong {
      width: 20px;
      height: 20px;
      border-radius: 999px;
      background: #e9edf3;
      color: var(--ink-3);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      flex: 0 0 auto;
    }

    .agent-step.done {
      border-color: rgba(18, 112, 71, 0.22);
      background: var(--ready-soft);
      color: var(--ready);
    }

    .agent-step.running {
      border-color: var(--accent-line);
      background: var(--accent-soft);
      color: var(--accent);
    }

    .agent-step.failed {
      border-color: rgba(160, 58, 22, 0.22);
      background: var(--warn-soft);
      color: var(--warn);
    }

    .agent-step.done strong {
      background: var(--ready);
      color: #fff;
    }

    .agent-step.running strong {
      background: var(--accent);
      color: #fff;
    }

    .agent-step.failed strong {
      background: var(--warn);
      color: #fff;
    }

    .agent-log {
      margin: 0;
      max-height: 142px;
      overflow: auto;
      white-space: pre-wrap;
      color: var(--ink-3);
      background: #fbfcfd;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 9px;
      font: 12px/1.5 var(--mono);
    }

    .empty {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      color: var(--ink-3);
      background: var(--surface);
      text-align: center;
    }

    .login-shell {
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 32px 18px;
      background: var(--canvas);
    }

    .login-card {
      width: min(100%, 430px);
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      box-shadow: var(--shadow-soft);
      padding: 26px;
      text-align: center;
      display: grid;
      gap: 14px;
    }

    .login-card .brand {
      justify-content: center;
      font-size: 21px;
    }

    .login-card p {
      margin: 0;
      color: var(--ink-3);
    }

    .login-action {
      justify-self: center;
      min-height: 38px;
      border-radius: 8px;
      background: var(--accent);
      color: #fff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 0 14px;
      font-weight: 680;
    }

    .login-action:hover {
      background: var(--accent-2);
    }

    @media (max-width: 900px) {
      .app-shell {
        grid-template-columns: 230px minmax(0, 1fr);
      }

      .agent-steps {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 760px) {
      .app-shell {
        display: block;
        height: auto;
        overflow: visible;
      }

      .side {
        display: none;
      }

      .workspace {
        min-height: 100vh;
        height: auto;
        overflow: visible;
      }

      .top-tools {
        position: static;
        padding: 14px 14px 0;
        justify-content: space-between;
      }

      .deck-search-wrap {
        width: min(100%, 280px);
        flex: 1 1 auto;
      }

      .mobile-user {
        display: inline-flex;
      }

      .hero {
        min-height: 0;
        padding: 46px 14px 34px;
      }

      .scope-head {
        margin-bottom: 28px;
      }

      .scope-title {
        font-size: 36px;
      }

      .prompt-card {
        border-radius: 14px;
        padding: 15px;
      }

      .title-field {
        grid-template-columns: 1fr;
        gap: 3px;
      }

      .prompt-card textarea {
        min-height: 160px;
      }

      .deck-main {
        grid-template-columns: 1fr;
      }

      .deck-actions {
        justify-content: flex-start;
      }
    }

    @media (max-width: 460px) {
      .top-tools {
        align-items: stretch;
      }

      .mobile-user span {
        display: none;
      }

      .scope-title {
        font-size: 32px;
      }

      .scope-tabs {
        max-width: 100%;
      }

      .scope-tab {
        padding: 0 10px;
      }

      .prompt-tools {
        display: grid;
        grid-template-columns: auto auto 1fr;
      }

      .prompt-tools .spacer {
        display: none;
      }

      .primary-action {
        grid-column: 1 / -1;
        width: 100%;
      }
    }
  </style>
</head>
<body>
  <main id="app" class="app-root" aria-live="polite"></main>
  <script>
    const rootPath = document.documentElement.dataset.rootPath || "";
    const api = rootPath + "/api";
    const app = document.getElementById("app");
    const sampleOutline = "请制作 5-6 页 PPT，关于机器学习的科普。";
    let draftTitle = "机器学习科普";
    let draftOutline = sampleOutline;
    let decks = [];
    let filesByDeck = new Map();
    let jobsByDeck = new Map();
    let jobLogs = new Map();
    let busy = false;
    let searchQuery = "";
    let noticeText = "";

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[char]));
    }

    function icon(name) {
      const icons = {
        brand: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v10A2.5 2.5 0 0 1 17.5 18H13l-4 3v-3H6.5A2.5 2.5 0 0 1 4 15.5z"/><path d="M8 8h8M8 11h5"/></svg>`,
        plus: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>`,
        spark: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/></svg>`,
        deck: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5h16v12H4z"/><path d="M8 21h8M12 17v4M8 9h8M8 12h5"/></svg>`,
        folder: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>`,
        search: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>`,
        history: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v4h4"/><path d="M12 7v5l3 2"/></svg>`,
        refresh: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 0 1-15.5 6.3"/><path d="M3 12A9 9 0 0 1 18.5 5.7"/><path d="M18 2v4h4M6 22v-4H2"/></svg>`,
        logout: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 17l5-5-5-5"/><path d="M15 12H3"/><path d="M21 19V5a2 2 0 0 0-2-2h-5"/></svg>`,
        arrowUp: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg>`,
        download: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></svg>`,
        file: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/></svg>`,
        quote: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 11V8a2 2 0 0 1 2-2h1"/><path d="M3 17h6v-6H3z"/><path d="M15 17h6v-6h-6z"/><path d="M15 11V8a2 2 0 0 1 2-2h1"/></svg>`,
        list: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h10"/></svg>`
      };
      return icons[name] || "";
    }

    async function request(path, options = {}) {
      const response = await fetch(api + path, {
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options
      });
      if (!response.ok) {
        let detail = response.statusText;
        try { detail = (await response.json()).detail || detail; } catch (_) {}
        throw new Error(detail);
      }
      if (response.status === 204) return null;
      return response.json();
    }

    async function boot() {
      try {
        const user = await request("/auth/me");
        await loadDecks();
        renderWorkbench(user);
        window.setInterval(refreshDecksQuietly, 5000);
      } catch (error) {
        renderLogin();
      }
    }

    function renderLogin() {
      const next = encodeURIComponent(rootPath + "/");
      app.innerHTML = `
        <section class="login-shell">
          <div class="login-card">
            <div class="brand">
              <span class="brand-mark">${icon("brand")}</span>
              <strong>AIPPT</strong>
            </div>
            <p>上海交通大学 AI PPT 生成工作台</p>
            <a class="login-action" href="${api}/auth/jaccount/login?next=${next}">
              ${icon("spark")} jAccount 登录
            </a>
          </div>
        </section>
      `;
    }

    async function loadDecks() {
      decks = await request("/decks");
      filesByDeck = new Map();
      jobsByDeck = new Map();
      jobLogs = new Map();
      await Promise.all(decks.map(async (deck) => {
        try {
          filesByDeck.set(deck.id, await request(`/files/decks/${deck.id}`));
        } catch (_) {
          filesByDeck.set(deck.id, []);
        }
        try {
          const jobs = await request(`/jobs/decks/${deck.id}`);
          jobsByDeck.set(deck.id, jobs);
          await Promise.all(jobs.slice(0, 3).map(async (job) => {
            try {
              const log = await request(`/jobs/${job.id}/log`);
              jobLogs.set(job.id, log.log_text || "");
            } catch (_) {
              jobLogs.set(job.id, "");
            }
          }));
        } catch (_) {
          jobsByDeck.set(deck.id, []);
        }
      }));
    }

    async function refreshDecksQuietly() {
      if (busy) return;
      const hasActive = decks.some((deck) => deck.status === "generating");
      if (!hasActive && decks.length > 0) return;
      try {
        await loadDecks();
        const me = await request("/auth/me");
        renderWorkbench(me);
      } catch (_) {}
    }

    function renderWorkbench(user) {
      const userName = user.jaccount || user.display_name || "me";
      const initial = String(userName || "A").trim().slice(0, 1).toUpperCase() || "A";
      app.innerHTML = `
        <div class="app-shell">
          <aside class="side" aria-label="AIPPT 工作区">
            <div class="side-head">
              <a class="brand" href="${rootPath || "/"}" aria-label="AIPPT 首页">
                <span class="brand-mark">${icon("brand")}</span>
                <strong>AIPPT</strong>
              </a>
              <button class="side-create" type="button" data-jump="compose" title="新建 PPT" aria-label="新建 PPT">${icon("plus")}</button>
            </div>
            <nav class="side-nav" aria-label="主导航">
              <button type="button" class="side-row is-active" data-jump="compose">
                ${icon("spark")}<span>生成</span><em>首页</em>
              </button>
              <button type="button" class="side-row" data-jump="deck-list">
                ${icon("deck")}<span>我的 PPT</span><em id="side-total-count">${decks.length}</em>
              </button>
            </nav>
            <div class="side-section">
              <div class="side-section-title">最近</div>
              <div id="side-recents">${renderSidebarDecks()}</div>
            </div>
            <div class="side-user">
              <div class="avatar" aria-hidden="true">${escapeHtml(initial)}</div>
              <div class="side-user-meta">
                <div class="side-user-name">${escapeHtml(userName)}</div>
                <div class="side-user-sub">AI PPT 生成工作台</div>
              </div>
              <a class="icon-link" href="${api}/auth/logout" title="退出" aria-label="退出">${icon("logout")}</a>
            </div>
          </aside>

          <section class="workspace">
            <div class="top-tools">
              <label class="deck-search-wrap">
                ${icon("search")}
                <input class="deck-search" id="deck-search" type="search" placeholder="搜索 PPT..." value="${escapeHtml(searchQuery)}" aria-label="搜索 PPT">
              </label>
              <a class="mobile-user" href="${api}/auth/logout" title="退出">
                <span>${escapeHtml(userName)}</span>${icon("logout")}
              </a>
            </div>

            <main class="hero" id="compose">
              <section class="scope-head">
                <div class="scope-eyebrow">${icon("folder")}<span>个人 · 我的工作区</span></div>
                <h1 class="scope-title">做一份 PPT</h1>
                <div class="scope-tabs" role="tablist" aria-label="AIPPT 视图">
                  <button class="scope-tab is-active" type="button" role="tab" aria-selected="true">
                    ${icon("spark")}生成
                  </button>
                  <button class="scope-tab" id="show-decks" type="button" role="tab" aria-selected="false">
                    ${icon("deck")}作品<span class="tab-count" id="tab-deck-count">${decks.length}</span>
                  </button>
                </div>
              </section>

              <div id="notice" class="notice ${noticeText ? "show" : ""}">${escapeHtml(noticeText)}</div>

              <div class="prompt-wrap">
                <form id="deck-form" class="prompt-card" autocomplete="off">
                  <label class="title-field">
                    <span>标题</span>
                    <input id="title" name="title" maxlength="160" value="${escapeHtml(draftTitle)}" placeholder="输入 PPT 标题" required>
                  </label>
                  <textarea id="outline" name="outline" required placeholder="告诉我主题、页数、使用场景，或直接粘贴 Markdown 大纲...">${escapeHtml(draftOutline)}</textarea>
                  <div class="prompt-tools">
                    <button class="prompt-chip suggestion-fill" type="button" data-title="课程汇报" data-outline="请制作 8 页 PPT，用于课程汇报。要求结构清晰，包含背景、核心概念、案例、总结与讨论问题。">
                      ${icon("folder")}SJTU 模板
                    </button>
                    <button class="icon-button" type="button" id="refresh" title="刷新列表" aria-label="刷新列表">${icon("refresh")}</button>
                    <span class="spacer"></span>
                    <button id="submit" class="primary-action" type="submit" ${busy ? "disabled" : ""}>
                      ${icon("arrowUp")}生成 PPT
                    </button>
                  </div>
                </form>

                <div class="suggestions" aria-label="示例需求">
                  <button class="suggestion suggestion-fill" type="button" data-title="机器学习科普" data-outline="请制作 5-6 页 PPT，关于机器学习的科普。">${icon("quote")}机器学习科普</button>
                  <button class="suggestion suggestion-fill" type="button" data-title="线性代数课程导入" data-outline="请制作 6 页 PPT，面向本科生介绍线性代数的学习价值，包含一个直观例子和课堂讨论。">${icon("list")}课程章节讲解</button>
                  <button class="suggestion suggestion-fill" type="button" data-title="项目阶段汇报" data-outline="请制作 7 页 PPT，用于项目阶段汇报，包含目标、已完成工作、关键数据、风险、下一步计划。">${icon("deck")}项目汇报</button>
                </div>
              </div>

              <section class="deck-section" id="deck-list" aria-labelledby="deck-list-title">
                <div class="deck-section-head">
                  <span id="deck-list-title">最近 · 我的 PPT</span>
                  <span class="deck-section-count" id="deck-section-count">${deckCountLabel()}</span>
                </div>
                <div id="deck-list-body">${renderDeckList()}</div>
              </section>
            </main>
          </section>
        </div>
      `;
      bindWorkbenchEvents(user);
      autosizeOutline();
    }

    function bindWorkbenchEvents(user) {
      document.getElementById("deck-form").addEventListener("submit", createDeck);
      document.getElementById("refresh").addEventListener("click", async () => {
        noticeText = "";
        await loadDecks();
        renderWorkbench(user);
      });
      document.getElementById("title").addEventListener("input", (event) => {
        draftTitle = event.target.value;
      });
      document.getElementById("outline").addEventListener("input", (event) => {
        draftOutline = event.target.value;
        autosizeOutline();
      });
      document.getElementById("deck-search").addEventListener("input", (event) => {
        searchQuery = event.target.value;
        updateDeckViews();
      });
      document.querySelectorAll("[data-jump]").forEach((button) => {
        button.addEventListener("click", () => {
          document.getElementById(button.dataset.jump)?.scrollIntoView({
            behavior: "smooth",
            block: "start"
          });
        });
      });
      document.getElementById("show-decks").addEventListener("click", () => {
        document.getElementById("deck-list").scrollIntoView({ behavior: "smooth", block: "start" });
      });
      document.querySelectorAll(".suggestion-fill").forEach((button) => {
        button.addEventListener("click", () => {
          draftTitle = button.dataset.title || draftTitle;
          draftOutline = button.dataset.outline || draftOutline;
          document.getElementById("title").value = draftTitle;
          document.getElementById("outline").value = draftOutline;
          autosizeOutline();
          document.getElementById("outline").focus();
        });
      });
    }

    function autosizeOutline() {
      const textarea = document.getElementById("outline");
      if (!textarea) return;
      textarea.style.height = "auto";
      const nextHeight = Math.min(Math.max(textarea.scrollHeight, 148), 320);
      textarea.style.height = `${nextHeight}px`;
    }

    function updateDeckViews() {
      const list = document.getElementById("deck-list-body");
      const side = document.getElementById("side-recents");
      const count = document.getElementById("deck-section-count");
      const tabCount = document.getElementById("tab-deck-count");
      const totalCount = document.getElementById("side-total-count");
      if (list) list.innerHTML = renderDeckList();
      if (side) side.innerHTML = renderSidebarDecks();
      if (count) count.textContent = deckCountLabel();
      if (tabCount) tabCount.textContent = decks.length;
      if (totalCount) totalCount.textContent = decks.length;
    }

    function filteredDecks() {
      const query = searchQuery.trim().toLowerCase();
      if (!query) return decks;
      return decks.filter((deck) => {
        const haystack = [
          deck.title,
          deck.outline_md,
          statusLabel(deck.status)
        ].join("\\n").toLowerCase();
        return haystack.includes(query);
      });
    }

    function deckCountLabel() {
      const visible = filteredDecks().length;
      if (!searchQuery.trim()) return `${decks.length} 个`;
      return `${visible} / ${decks.length} 个`;
    }

    function renderSidebarDecks() {
      const visible = filteredDecks().slice(0, 8);
      if (!visible.length) return `<div class="side-empty">${searchQuery.trim() ? "没有匹配的 PPT" : "暂无 PPT"}</div>`;
      return visible.map((deck) => `
        <button class="side-deck" type="button" data-jump="deck-list" title="${escapeHtml(deck.title)}">
          ${icon("file")}<span>${escapeHtml(deck.title)}</span>
        </button>
      `).join("");
    }

    function renderDeckList() {
      const visible = filteredDecks();
      if (visible.length === 0) {
        return `<div class="empty">${searchQuery.trim() ? "没有匹配的 PPT" : "暂无 PPT"}</div>`;
      }
      return `<div class="deck-list">${visible.map(renderDeck).join("")}</div>`;
    }

    function renderDeck(deck) {
      const files = filesByDeck.get(deck.id) || [];
      const pptx = files.find((file) => file.kind === "pptx");
      const jobs = jobsByDeck.get(deck.id) || [];
      const updated = formatTime(deck.updated_at || deck.created_at);
      return `
        <article class="deck-row">
          <div class="deck-main">
            <div>
              <h2 class="deck-title">${escapeHtml(deck.title)}</h2>
              <div class="deck-meta">
                <span class="pill ${statusClass(deck.status)}">${statusLabel(deck.status)}</span>
                <span>更新 ${escapeHtml(updated)}</span>
              </div>
            </div>
            <div class="deck-actions">
              ${pptx ? `<a class="row-action primary" href="${api}/files/${pptx.id}/download">${icon("download")}下载 PPTX</a>` : ""}
            </div>
          </div>
          ${renderAgentProgress(deck, jobs)}
          ${renderOutlinePreview(deck)}
        </article>
      `;
    }

    function renderOutlinePreview(deck) {
      if (!deck.outline_md) return "";
      return `
        <details class="outline-preview">
          <summary>需求或大纲</summary>
          <pre>${escapeHtml(deck.outline_md)}</pre>
        </details>
      `;
    }

    function renderAgentProgress(deck, jobs) {
      if (!jobs.length) return "";
      const plan = jobs.find((job) => job.type === "plan_outline");
      const build = jobs.find((job) => job.type === "build_pptx");
      if (!plan && !build) return "";
      const labels = ["理解需求", "规划结构", "渲染 PPTX", "完成下载"];
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
      const displayJob = build || plan;
      const steps = labels.map((label, index) => {
        let cls = "";
        if (isDone || index < activeIndex) cls = "done";
        else if (isFailed && index === activeIndex) cls = "failed";
        else if (index === activeIndex) cls = "running";
        return `<span class="agent-step ${cls}"><strong>${index + 1}</strong>${escapeHtml(label)}</span>`;
      }).join("");
      const log = formatAgentLog([plan, build].map((job) => job ? jobLogs.get(job.id) || "" : "").join("\\n"));
      return `
        <div class="agent-progress">
          <div class="agent-head">
            <strong>Agent 生成流程 · ${escapeHtml(statusText)}</strong>
            <span>${escapeHtml(formatTime(displayJob.created_at))}</span>
          </div>
          <div class="agent-steps">${steps}</div>
          ${log ? `<pre class="agent-log">${escapeHtml(log)}</pre>` : ""}
        </div>
      `;
    }

    function statusClass(status) {
      if (status === "generating") return "running";
      if (status === "ready") return "ready";
      if (status === "failed") return "failed";
      return "";
    }

    function statusLabel(status) {
      return {
        draft: "草稿",
        outline_ready: "规划完成",
        generating: "生成中",
        ready: "可下载",
        failed: "失败"
      }[status] || status;
    }

    async function createDeck(event) {
      event.preventDefault();
      await createDeckWithJob("plan_outline");
    }

    async function createDeckWithJob(jobType) {
      busy = true;
      setBusy(true);
      noticeText = "";
      try {
        const title = document.getElementById("title").value.trim();
        const outline = document.getElementById("outline").value;
        if (!title) throw new Error("请先写一个标题");
        if (!outline.trim()) throw new Error("请先写下需求或大纲");
        draftTitle = title;
        draftOutline = outline;
        const deck = await request("/decks", {
          method: "POST",
          body: JSON.stringify({ title, outline_md: outline })
        });
        await request(`/jobs/decks/${deck.id}`, {
          method: "POST",
          body: JSON.stringify({ type: jobType })
        });
        noticeText = "已开始生成，Agent 会先规划结构再渲染 PPTX。";
        await loadDecks();
        const me = await request("/auth/me");
        renderWorkbench(me);
      } catch (error) {
        showNotice(error.message || "提交失败");
      } finally {
        busy = false;
        setBusy(false);
      }
    }

    function setBusy(value) {
      const submit = document.getElementById("submit");
      if (submit) submit.disabled = value;
    }

    function formatTime(value) {
      return new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
      }).format(parseApiTime(value));
    }

    function parseApiTime(value) {
      const text = String(value || "");
      if (/[zZ]$|[+-]\\d{2}:?\\d{2}$/.test(text)) return new Date(text);
      return new Date(text + "Z");
    }

    function formatAgentLog(logText) {
      const lines = String(logText || "")
        .split("\\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => line.startsWith("AIPPT_AGENT:") ? line.slice("AIPPT_AGENT:".length).trim() : "")
        .filter(Boolean);
      return lines.slice(-8).join("\\n");
    }

    function showNotice(text) {
      noticeText = text;
      const notice = document.getElementById("notice");
      if (!notice) return;
      notice.textContent = text;
      notice.classList.add("show");
    }

    boot();
  </script>
</body>
</html>""".replace("__ROOT_PATH__", escaped_root_path)
    )
