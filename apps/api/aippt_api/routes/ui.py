import html
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlmodel import Session

from ..auth import get_current_user
from ..config import Settings, get_settings
from ..db import get_session


router = APIRouter()


def _root_path(request: Request) -> str:
    return str(request.scope.get("root_path") or "").rstrip("/")


def _login_redirect(request: Request) -> RedirectResponse:
    root_path = _root_path(request)
    next_url = f"{root_path}/" if root_path else "/"
    login_url = f"{root_path}/api/auth/jaccount/login?next={quote(next_url, safe='/')}"
    return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)


@router.get("/", response_class=HTMLResponse, response_model=None)
def workbench(
    request: Request,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    try:
        get_current_user(request, session=session, settings=settings)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return _login_redirect(request)
        raise

    root_path = _root_path(request)
    escaped_root_path = html.escape(root_path, quote=True)
    return HTMLResponse(
        """<!doctype html>
<html lang="zh-CN" data-root-path="__ROOT_PATH__">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AIPPT</title>
  <link rel="icon" type="image/x-icon" href="__ROOT_PATH__/static/img/favicons/favicon.ico?v=20260531">
  <link rel="icon" type="image/png" sizes="32x32" href="__ROOT_PATH__/static/img/favicons/favicon-32.png?v=20260531">
  <link rel="icon" type="image/png" sizes="16x16" href="__ROOT_PATH__/static/img/favicons/favicon-16.png?v=20260531">
  <style>
    :root {
      color-scheme: light;
      --canvas: #f7f8fb;
      --rail: #ffffff;
      --surface: #ffffff;
      --subtle: #f6f8fb;
      --line: #e8ecf3;
      --line-soft: #f0f3f8;
      --line-hard: #d7dde8;
      --ink: #111827;
      --ink-2: #475467;
      --ink-3: #667085;
      --ink-4: #98a2b3;
      --accent: #3157c8;
      --accent-2: #2448b8;
      --accent-soft: #eef3ff;
      --accent-line: #dce6ff;
      --ready: #22a06b;
      --ready-soft: #eaf8f1;
      --ready-line: #cfefdd;
      --warn: #b42318;
      --warn-soft: #fff1f0;
      --shadow-soft: 0 10px 30px rgba(15, 23, 42, 0.04);
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
      grid-template-columns: 284px minmax(0, 1fr);
      min-height: 100vh;
      height: 100vh;
      overflow: hidden;
      background: var(--canvas);
    }

    .side {
      min-width: 0;
      height: 100vh;
      background: var(--rail);
      box-shadow: 1px 0 0 #eef1f5;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .side-head {
      height: 78px;
      padding: 0 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex: 0 0 auto;
    }

    .brand {
      display: inline-flex;
      align-items: center;
      gap: 11px;
      min-width: 0;
      color: var(--ink);
      font-weight: 730;
      font-size: 20px;
      line-height: 1;
      white-space: nowrap;
    }

    .brand-mark {
      width: 32px;
      height: 32px;
      display: grid;
      place-items: center;
      color: var(--accent);
      position: relative;
    }

    .brand-mark::before,
    .brand-mark::after {
      content: "";
      position: absolute;
    }

    .brand-mark::before {
      content: "A";
      inset: 0;
      display: grid;
      place-items: center;
      color: var(--accent);
      font-size: 30px;
      line-height: 1;
      font-weight: 900;
      font-style: italic;
      letter-spacing: 0;
      transform: skewX(-7deg);
      text-shadow: 8px 0 0 rgba(88, 166, 255, 0.24);
    }

    .brand-mark::after {
      display: none;
    }

    .brand-mark i {
      display: none;
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
      padding: 8px 16px;
      display: grid;
      gap: 8px;
    }

    .side-section {
      border-top: 1px solid var(--line-soft);
      margin-top: 8px;
      padding-top: 22px;
      min-height: 0;
      overflow: auto;
    }

    .side-section-title {
      padding: 0 8px 10px;
      color: var(--ink-4);
      font-size: 12px;
      font-weight: 650;
    }

    .side-row,
    .side-deck {
      width: 100%;
      min-width: 0;
      border: 0;
      border-radius: 8px;
      background: transparent;
      color: var(--ink-3);
      display: grid;
      grid-template-columns: 20px minmax(0, 1fr) auto;
      align-items: center;
      gap: 9px;
      min-height: 44px;
      padding: 0 12px;
      text-align: left;
      cursor: pointer;
    }

    .side-row:hover,
    .side-deck:hover {
      background: var(--accent-soft);
      color: var(--ink);
    }

    .side-row.is-active {
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 650;
      box-shadow: inset 0 0 0 1px var(--accent-line);
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

    .side-badge {
      min-width: 24px;
      height: 22px;
      border-radius: 8px;
      display: inline-grid;
      place-items: center;
      background: #eef0f4;
      color: var(--ink-3);
      padding: 0 7px;
      font-weight: 650;
    }

    .side-deck {
      font-size: 14px;
      min-height: 38px;
      grid-template-columns: 16px minmax(0, 1fr) auto;
    }

    .side-deck em {
      font-variant-numeric: tabular-nums;
    }

    .side-empty {
      padding: 8px;
      color: var(--ink-4);
      font-size: 13px;
    }

    .side-user {
      margin-top: auto;
      margin: auto 16px 18px;
      padding: 12px;
      display: grid;
      grid-template-columns: 32px minmax(0, 1fr) 24px;
      align-items: center;
      gap: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      box-shadow: none;
    }

    .avatar {
      width: 32px;
      height: 32px;
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
      max-width: 900px;
      min-height: 100vh;
      margin: 0 auto;
      padding: 46px 32px 44px;
      display: flex;
      flex-direction: column;
    }

    .scope-head {
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      margin: 0 0 18px;
    }

    .scope-eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--ink-3);
      font-size: 13px;
      font-weight: 500;
      margin-bottom: 12px;
    }

    .scope-eyebrow svg {
      color: var(--ink-4);
    }

    .scope-title {
      margin: 0;
      color: var(--ink);
      font-size: 48px;
      line-height: 1.08;
      font-weight: 740;
      letter-spacing: 0;
    }

    .scope-tabs {
      margin-top: 18px;
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
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px 20px;
      box-shadow: var(--shadow-soft);
      transition: box-shadow 0.18s ease;
    }

    .prompt-card:hover {
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }

    .prompt-card:focus-within {
      box-shadow: 0 0 0 1px var(--accent-line), 0 0 0 4px rgba(49, 87, 200, 0.06),
        var(--shadow-soft);
    }

    .prompt-card textarea::placeholder {
      color: var(--ink-4);
    }

    .prompt-card textarea {
      width: 100%;
      min-height: 70px;
      max-height: 180px;
      border: 0;
      outline: 0;
      resize: vertical;
      background: transparent;
      color: var(--ink);
      padding: 4px 0 10px;
      font-size: 17px;
      line-height: 1.58;
    }

    .prompt-insights {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin: 2px 0 16px;
    }

    .insight-chip {
      min-height: 32px;
      border: 0;
      border-radius: 8px;
      background: #f6f8fc;
      color: var(--ink-3);
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 0 11px;
      font-size: 13px;
      font-weight: 620;
      white-space: nowrap;
      border: 1px solid var(--line);
    }

    .insight-chip svg {
      color: var(--ink-4);
    }

    .prompt-divider {
      height: 1px;
      margin: 0 0 16px;
      background: var(--line-soft);
    }

    .prompt-footer {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, max-content)) minmax(120px, 1fr);
      align-items: center;
      gap: 10px;
    }

    .prompt-control {
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      color: var(--ink-3);
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 0 11px;
      font-size: 13px;
      white-space: nowrap;
      cursor: default;
    }

    .prompt-control strong {
      color: var(--ink-2);
      font-weight: 650;
    }

    .prompt-control svg {
      color: var(--ink-4);
    }

    .primary-action {
      justify-self: end;
      min-height: 42px;
      border: 0;
      border-radius: 8px;
      background: var(--accent);
      color: #fff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 0 15px;
      font-weight: 680;
      cursor: pointer;
      box-shadow: none;
    }

    .primary-action[aria-busy="true"] svg {
      animation: spin 1.4s linear infinite;
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
      margin-top: 16px;
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

    .side-row:focus-visible,
    .side-deck:focus-visible,
    .scope-tab:focus-visible,
    .suggestion:focus-visible,
    .primary-action:focus-visible,
    .prompt-control:focus-visible,
    .deck-toggle:focus-visible,
    .row-action:focus-visible,
    .row-more:focus-visible,
    .icon-link:focus-visible {
      outline: 2px solid rgba(49, 87, 200, 0.28);
      outline-offset: 2px;
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

    .workflow-section {
      margin-top: 24px;
      display: grid;
      gap: 16px;
    }

    .flow-steps {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      align-items: start;
      gap: 0;
      padding: 0 8px;
    }

    .flow-step {
      position: relative;
      display: grid;
      justify-items: center;
      gap: 8px;
      color: var(--ink-4);
      font-size: 13px;
      font-weight: 650;
      text-align: center;
    }

    .flow-step:not(:last-child)::after {
      content: "";
      position: absolute;
      left: calc(50% + 24px);
      right: calc(-50% + 24px);
      top: 17px;
      border-top: 1.5px dashed #d7dde8;
      z-index: 0;
    }

    .flow-step.done:not(:last-child)::after {
      border-top-style: solid;
      border-color: rgba(23, 150, 106, 0.78);
    }

    .flow-dot {
      width: 34px;
      height: 34px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: #edf1f7;
      color: var(--ink-3);
      font-weight: 760;
      line-height: 1;
      font-variant-numeric: tabular-nums;
      position: relative;
      z-index: 1;
      box-shadow: 0 0 0 6px var(--canvas);
    }

    .flow-step.done {
      color: var(--ready);
    }

    .flow-step.done .flow-dot {
      background: var(--ready);
      color: #fff;
      box-shadow: 0 0 0 5px var(--ready-soft);
    }

    .flow-step.active {
      color: var(--accent);
      font-weight: 760;
    }

    .flow-step.active .flow-dot {
      background: linear-gradient(135deg, #2448b8, #5175dc, #3157c8);
      background-size: 180% 180%;
      color: #fff;
      box-shadow: 0 0 0 6px rgba(49, 87, 200, 0.1);
      animation: activeNodeGradient 2.4s ease infinite;
    }

    .flow-step.active .flow-dot::before {
      content: "";
      position: absolute;
      inset: -8px;
      border-radius: 999px;
      background: conic-gradient(from 0deg, rgba(49, 87, 200, 0), rgba(49, 87, 200, 0.5), rgba(49, 87, 200, 0));
      animation: spin 1.8s linear infinite;
      z-index: -1;
      -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 2px), #000 calc(100% - 1px));
      mask: radial-gradient(farthest-side, transparent calc(100% - 2px), #000 calc(100% - 1px));
    }

    .flow-stars::before,
    .flow-stars::after {
      content: "";
      position: absolute;
      border-radius: 999px;
      background: #72adff;
      box-shadow: 22px 8px 0 -1px #a9c4ff;
    }

    .flow-stars::before {
      width: 4px;
      height: 4px;
      top: -8px;
      left: -14px;
    }

    .flow-stars::after {
      width: 3px;
      height: 3px;
      right: -14px;
      bottom: 3px;
    }

    .flow-step.failed {
      color: var(--warn);
    }

    .flow-step.failed .flow-dot {
      background: var(--warn);
      color: #fff;
    }

    @keyframes activeNodeGradient {
      0%, 100% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .task-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      padding: 16px;
      box-shadow: var(--shadow-soft);
      display: grid;
      gap: 8px;
    }

    .task-card.is-generating {
      position: relative;
      border-color: #e6eaf0;
    }

    .task-card.is-generating::after {
      content: "";
      position: absolute;
      inset: -1px;
      border: 1px solid rgba(49, 87, 200, 0.18);
      border-radius: inherit;
      pointer-events: none;
      opacity: 0.15;
      animation: cardBreath 2.8s ease-in-out infinite;
    }

    .task-head {
      display: grid;
      grid-template-columns: 30px minmax(0, 1fr) auto;
      align-items: center;
      gap: 12px;
    }

    .task-icon {
      width: 30px;
      height: 30px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: var(--accent);
      color: #fff;
    }

    .task-icon.is-running {
      background: var(--accent);
      box-shadow: 0 0 0 5px rgba(49, 87, 200, 0.1);
    }

    .task-title-wrap {
      min-width: 0;
      display: grid;
      gap: 3px;
    }

    .task-title {
      margin: 0;
      color: var(--ink);
      font-size: 18px;
      line-height: 1.25;
      font-weight: 760;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .task-meta,
    .task-actions {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--ink-4);
      font-size: 13px;
      flex-wrap: wrap;
    }

    .task-actions {
      justify-content: flex-end;
    }

    .task-summary {
      margin: 4px 0 0;
      color: var(--ink-2);
      font-weight: 680;
    }

    .task-sub,
    .task-result-meta {
      margin: 0;
      color: var(--ink-3);
      font-size: 13px;
    }

    .task-log {
      margin-top: 2px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f8fafd;
      padding: 9px 11px;
      display: grid;
      gap: 5px;
    }

    .log-line {
      color: var(--ink-3);
      font-size: 13px;
      display: grid;
      grid-template-columns: 16px minmax(0, 1fr);
      gap: 8px;
      align-items: center;
    }

    .log-line.is-active {
      position: relative;
      overflow: hidden;
      border-radius: 8px;
      background: rgba(49, 87, 200, 0.035);
      margin: 0 -5px;
      padding: 5px;
    }

    .log-line.is-active::after {
      content: "";
      position: absolute;
      top: 0;
      left: -40%;
      width: 40%;
      height: 100%;
      background: linear-gradient(
        90deg,
        transparent,
        rgba(49, 87, 200, 0.08),
        transparent
      );
      animation: shimmer 2.4s ease-in-out infinite;
    }

    .log-line::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--accent);
    }

    .task-details {
      color: var(--ink-3);
      font-size: 13px;
    }

    .task-details summary {
      cursor: pointer;
      color: var(--ink-3);
      font-weight: 650;
    }

    .task-details pre {
      margin: 8px 0 0;
      max-height: 160px;
      overflow: auto;
      white-space: pre-wrap;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
      padding: 10px;
      font: 12px/1.55 var(--mono);
    }

    .deck-section {
      margin-top: 22px;
      display: grid;
      gap: 0;
      position: relative;
      isolation: isolate;
    }

    .deck-section::before,
    .deck-section::after {
      content: "";
      position: absolute;
      left: 18px;
      right: 18px;
      height: 24px;
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      background: #fbfcfd;
      z-index: -1;
      pointer-events: none;
    }

    .deck-section::before {
      top: 10px;
      transform: translateY(14px) scale(0.985);
      opacity: 0.72;
    }

    .deck-section::after {
      top: 24px;
      transform: translateY(14px) scale(0.955);
      opacity: 0.48;
    }

    .deck-section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      min-height: 44px;
      padding: 0 13px;
      border: 1px solid var(--line);
      border-bottom: 0;
      border-radius: 8px 8px 0 0;
      background: var(--surface);
      color: var(--ink-3);
      font-size: 13px;
      font-weight: 560;
    }

    .deck-section-title {
      min-width: 0;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      color: var(--ink-2);
      font-weight: 650;
    }

    .deck-section-count {
      color: var(--ink-4);
      font-size: 12px;
      white-space: nowrap;
    }

    .deck-section-actions {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      flex: 0 0 auto;
    }

    .deck-toggle {
      width: 28px;
      height: 28px;
      border: 0;
      border-radius: 7px;
      background: transparent;
      color: var(--ink-4);
      display: grid;
      place-items: center;
      cursor: pointer;
      transition: transform 0.16s ease, color 0.16s ease, background 0.16s ease;
    }

    .deck-toggle:hover {
      background: var(--line-soft);
      color: var(--ink);
    }

    .deck-shelf {
      min-height: 74px;
      border: 1px solid var(--line);
      border-radius: 0 0 8px 8px;
      background: var(--surface);
      padding: 10px;
      box-shadow: 0 10px 26px -24px rgba(15, 18, 28, 0.3);
      overflow: hidden;
      position: relative;
    }

    .deck-section.is-collapsed .deck-shelf {
      max-height: 96px;
      cursor: pointer;
    }

    .deck-section.is-collapsed .deck-shelf::after {
      content: "";
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      height: 28px;
      background: linear-gradient(to bottom, rgba(255, 255, 255, 0), var(--surface));
      pointer-events: none;
    }

    .deck-section.is-expanded .deck-shelf {
      max-height: min(45vh, 420px);
      overflow-y: auto;
    }

    .deck-peek {
      min-width: 0;
      min-height: 54px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 12px;
      padding: 8px 9px;
      border-radius: 7px;
      background: #fbfcfd;
      color: var(--ink-3);
    }

    .deck-peek-main {
      min-width: 0;
      display: grid;
      gap: 4px;
    }

    .deck-peek-title {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: var(--ink);
      font-size: 14px;
      font-weight: 680;
    }

    .deck-peek-meta {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      color: var(--ink-4);
      font-size: 12px;
    }

    .deck-peek.empty {
      grid-template-columns: 1fr;
      justify-items: center;
      color: var(--ink-4);
      background: transparent;
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

    .pill.running::before {
      content: "";
      width: 6px;
      height: 6px;
      border-radius: 999px;
      background: var(--accent);
      display: inline-block;
      flex: 0 0 auto;
      margin-right: 6px;
      animation: statusPulse 1.6s ease-in-out infinite;
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

    .deck-section {
      margin-top: 18px;
    }

    .deck-section::before,
    .deck-section::after {
      display: none;
    }

    .deck-section-head {
      min-height: 46px;
      padding: 0 16px;
      border-bottom: 1px solid var(--line-soft);
    }

    .deck-toggle {
      width: auto;
      height: 28px;
      padding: 0 4px;
      color: var(--accent);
      font-size: 13px;
      font-weight: 650;
    }

    .deck-toggle:hover {
      background: transparent;
      color: var(--accent-2);
    }

    .deck-shelf,
    .deck-section.is-expanded .deck-shelf,
    .deck-section.is-collapsed .deck-shelf {
      min-height: 0;
      max-height: none;
      overflow: visible;
      padding: 0;
      border-radius: 0 0 8px 8px;
      box-shadow: 0 16px 34px -30px rgba(15, 18, 28, 0.28);
      cursor: default;
    }

    .deck-section.is-collapsed .deck-shelf::after {
      display: none;
    }

    .deck-empty {
      min-height: 72px;
      display: grid;
      place-items: center;
      color: var(--ink-4);
      font-size: 14px;
    }

    .deck-list {
      gap: 0;
    }

    .deck-row {
      border: 0;
      border-radius: 0;
      box-shadow: none;
      padding: 12px 14px;
      grid-template-columns: 144px minmax(0, 1fr) auto;
      align-items: center;
      gap: 14px;
      border-bottom: 1px solid var(--line-soft);
    }

    .deck-row:last-child {
      border-bottom: 0;
    }

    .deck-row:hover {
      background: #fbfcff;
    }

    .deck-row:hover .deck-cover {
      border-color: var(--accent-line);
    }

    .deck-cover {
      width: 144px;
      aspect-ratio: 16 / 9;
      border-radius: 8px;
      overflow: hidden;
      background: #eaf1ff;
      border: 1px solid var(--line-soft);
      display: grid;
      place-items: center;
      color: #fff;
      font-size: 12px;
      font-weight: 720;
    }

    .deck-cover img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .deck-cover-fallback {
      background:
        linear-gradient(135deg, #eef4ff, #f8faff),
        radial-gradient(circle at 76% 12%, rgba(49, 87, 200, 0.11), transparent 34%);
      padding: 10px;
      align-items: end;
      justify-items: start;
      color: var(--ink-2);
    }

    .deck-cover-fallback span {
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .deck-main {
      display: grid;
      grid-template-columns: 1fr;
      align-items: center;
      gap: 5px;
    }

    .deck-title {
      font-size: 16px;
      font-weight: 740;
    }

    .deck-actions {
      min-width: 0;
      display: inline-flex;
      align-items: center;
      justify-content: flex-end;
      gap: 9px;
    }

    .row-action.primary {
      background: var(--accent);
      color: #fff;
    }

    .row-action.primary:hover {
      background: var(--accent-2);
    }

    .row-action.is-disabled {
      color: var(--ink-4);
      cursor: not-allowed;
      opacity: 0.72;
    }

    .row-more {
      width: 28px;
      height: 32px;
      border: 0;
      border-radius: 8px;
      background: transparent;
      color: var(--ink-4);
      display: grid;
      place-items: center;
      cursor: pointer;
      font-size: 20px;
      line-height: 1;
    }

    .row-more:hover {
      background: var(--line-soft);
      color: var(--ink);
    }

    .mini-progress {
      width: 120px;
      height: 4px;
      border-radius: 999px;
      overflow: visible;
      background: #dfe5ef;
    }

    .mini-progress span {
      display: block;
      height: 100%;
      border-radius: inherit;
      background: var(--accent);
      position: relative;
    }

    .mini-progress span::after {
      content: "";
      position: absolute;
      right: -4px;
      top: 50%;
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--accent);
      box-shadow: 0 0 10px rgba(49, 87, 200, 0.35);
      transform: translateY(-50%) scale(0.85);
      animation: progressDotBreath 1.8s ease-in-out infinite;
    }

    .mini-percent {
      color: var(--ink-3);
      font-size: 13px;
    }

    @keyframes cardBreath {
      0%, 100% {
        opacity: 0.15;
        box-shadow: 0 0 0 rgba(49, 87, 200, 0);
      }
      50% {
        opacity: 0.72;
        box-shadow: 0 0 22px rgba(49, 87, 200, 0.1);
      }
    }

    @keyframes statusPulse {
      0%, 100% {
        opacity: 0.35;
        transform: scale(0.9);
      }
      50% {
        opacity: 1;
        transform: scale(1.15);
      }
    }

    @keyframes shimmer {
      0% {
        left: -40%;
      }
      60%, 100% {
        left: 120%;
      }
    }

    @keyframes progressDotBreath {
      0%, 100% {
        opacity: 0.45;
        transform: translateY(-50%) scale(0.85);
      }
      50% {
        opacity: 1;
        transform: translateY(-50%) scale(1.15);
      }
    }

    @media (prefers-reduced-motion: reduce) {
      .task-card.is-generating::after,
      .pill.running::before,
      .log-line.is-active::after,
      .mini-progress span::after,
      .flow-step.active .flow-dot,
      .flow-step.active .flow-dot::before {
        animation: none;
      }
    }

    @media (max-width: 900px) {
      .app-shell {
        grid-template-columns: 230px minmax(0, 1fr);
      }

      .agent-steps {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .flow-steps {
        grid-template-columns: repeat(5, minmax(72px, 1fr));
        overflow-x: auto;
        padding-bottom: 8px;
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

      .hero {
        min-height: 0;
        padding: 38px 14px 26px;
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

      .prompt-card textarea {
        min-height: 108px;
      }

      .prompt-footer {
        grid-template-columns: 1fr;
      }

      .prompt-control,
      .primary-action {
        width: 100%;
        justify-content: center;
      }

      .primary-action {
        justify-self: stretch;
      }

      .task-head {
        grid-template-columns: 30px minmax(0, 1fr);
      }

      .task-actions,
      .task-head > .row-action {
        grid-column: 1 / -1;
        justify-content: flex-start;
      }

      .deck-main {
        grid-template-columns: 1fr;
      }

      .deck-row {
        grid-template-columns: 96px minmax(0, 1fr);
      }

      .deck-actions {
        grid-column: 1 / -1;
        justify-content: flex-start;
      }
    }

    @media (max-width: 460px) {
      .scope-title {
        font-size: 32px;
      }

      .scope-tabs {
        max-width: 100%;
      }

      .scope-tab {
        padding: 0 10px;
      }

      .deck-row {
        grid-template-columns: 1fr;
      }

      .deck-cover {
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
    let deckSlideCounts = new Map();
    let busy = false;
    let searchQuery = "";
    let noticeText = "";
    let decksExpanded = false;

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
        redirectToLogin();
      }
    }

    function redirectToLogin() {
      const next = encodeURIComponent(rootPath + "/");
      window.location.replace(`${api}/auth/jaccount/login?next=${next}`);
    }

    async function loadDecks() {
      decks = await request("/decks");
      filesByDeck = new Map();
      jobsByDeck = new Map();
      jobLogs = new Map();
      deckSlideCounts = new Map();
      await Promise.all(decks.map(async (deck) => {
        let files = [];
        try {
          files = await request(`/files/decks/${deck.id}`);
          filesByDeck.set(deck.id, files);
        } catch (_) {
          filesByDeck.set(deck.id, []);
        }
        deckSlideCounts.set(deck.id, await loadDeckSlideCount(deck, files));
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
                <span class="brand-mark" aria-hidden="true"><i></i></span>
                <strong>AIPPT</strong>
              </a>
            </div>
            <nav class="side-nav" aria-label="主导航">
              <button type="button" class="side-row is-active" data-jump="compose">
                ${icon("spark")}<span>生成</span><em>首页</em>
              </button>
              <button type="button" class="side-row" data-jump="deck-list">
                ${icon("deck")}<span>我的 PPT</span><em class="side-badge" id="side-total-count">${decks.length}</em>
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
                  <textarea id="outline" name="outline" required placeholder="告诉我主题、页数、使用场景，或直接粘贴 Markdown 大纲...">${escapeHtml(draftOutline)}</textarea>
                  <div class="prompt-insights" id="prompt-insights">${renderInsightChips(draftOutline)}</div>
                  <div class="prompt-divider"></div>
                  <div class="prompt-footer">
                    <button class="prompt-control" type="button" title="模板">
                      ${icon("folder")}<span>模板</span><strong>SJTU 模板</strong>
                    </button>
                    <button class="prompt-control" type="button" title="风格">
                      ${icon("spark")}<span>风格</span><strong id="style-control-label">${escapeHtml(inferStyleLabel(draftOutline))}</strong>
                    </button>
                    <button id="submit" class="primary-action" type="submit" ${busy ? "disabled aria-busy=\\"true\\"" : "aria-busy=\\"false\\""}>
                      ${icon(busy ? "spark" : "arrowUp")}${busy ? "生成中" : "生成 PPT"}
                    </button>
                  </div>
                </form>

                <div class="suggestions" aria-label="示例需求">
                  <button class="suggestion suggestion-fill" type="button" data-title="机器学习科普" data-outline="请制作 5-6 页 PPT，关于机器学习的科普。">${icon("quote")}机器学习科普</button>
                  <button class="suggestion suggestion-fill" type="button" data-title="线性代数课程导入" data-outline="请制作 6 页 PPT，面向本科生介绍线性代数的学习价值，包含一个直观例子和课堂讨论。">${icon("list")}课程章节讲解</button>
                  <button class="suggestion suggestion-fill" type="button" data-title="项目阶段汇报" data-outline="请制作 7 页 PPT，用于项目阶段汇报，包含目标、已完成工作、关键数据、风险、下一步计划。">${icon("deck")}项目汇报</button>
                </div>
              </div>

              ${renderCurrentWorkflow()}

              <section class="deck-section ${decksExpanded ? "is-expanded" : "is-collapsed"}" id="deck-list" aria-labelledby="deck-list-title">
                <div class="deck-section-head">
                  <span class="deck-section-title" id="deck-list-title">${icon("deck")}最近 · 我的 PPT</span>
                  <span class="deck-section-actions">
                    <span class="deck-section-count" id="deck-section-count">${deckCountLabel()}</span>
                    ${filteredDecks().length > 3 ? `<button class="deck-toggle" id="toggle-decks" type="button" aria-expanded="${decksExpanded}" title="${decksExpanded ? "收起" : "查看全部"}">${decksExpanded ? "收起" : "查看全部"}</button>` : ""}
                  </span>
                </div>
                <div class="deck-shelf" id="deck-list-body">${renderDeckShelf()}</div>
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
      document.getElementById("outline").addEventListener("input", (event) => {
        draftOutline = event.target.value;
        draftTitle = deriveTitle(draftOutline);
        autosizeOutline();
        updatePromptInsights();
      });
      document.getElementById("outline").addEventListener("keydown", (event) => {
        if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
          event.preventDefault();
          if (!busy) document.getElementById("deck-form").requestSubmit();
        }
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
        decksExpanded = true;
        updateDeckViews();
        document.getElementById("deck-list").scrollIntoView({ behavior: "smooth", block: "start" });
      });
      document.getElementById("toggle-decks")?.addEventListener("click", () => {
        decksExpanded = !decksExpanded;
        updateDeckViews();
      });
      document.querySelector("[data-task-detail]")?.addEventListener("click", (event) => {
        const detail = document.getElementById("task-detail-panel");
        if (!detail) return;
        const isHidden = detail.hasAttribute("hidden");
        detail.toggleAttribute("hidden", !isHidden);
        event.currentTarget.textContent = isHidden ? "收起详情" : "查看详情";
      });
      document.querySelectorAll(".suggestion-fill").forEach((button) => {
        button.addEventListener("click", () => {
          draftTitle = button.dataset.title || draftTitle;
          draftOutline = button.dataset.outline || draftOutline;
          document.getElementById("outline").value = draftOutline;
          autosizeOutline();
          updatePromptInsights();
          document.getElementById("outline").focus();
        });
      });
    }

    function autosizeOutline() {
      const textarea = document.getElementById("outline");
      if (!textarea) return;
      textarea.style.height = "auto";
      const nextHeight = Math.min(Math.max(textarea.scrollHeight, 70), 180);
      textarea.style.height = `${nextHeight}px`;
    }

    function updatePromptInsights() {
      const insights = document.getElementById("prompt-insights");
      const style = document.getElementById("style-control-label");
      if (insights) insights.innerHTML = renderInsightChips(draftOutline);
      if (style) style.textContent = inferStyleLabel(draftOutline);
    }

    function updateDeckViews() {
      const list = document.getElementById("deck-list-body");
      const side = document.getElementById("side-recents");
      const section = document.getElementById("deck-list");
      const toggle = document.getElementById("toggle-decks");
      const count = document.getElementById("deck-section-count");
      const tabCount = document.getElementById("tab-deck-count");
      const totalCount = document.getElementById("side-total-count");
      if (list) list.innerHTML = renderDeckShelf();
      if (section) {
        section.classList.toggle("is-expanded", decksExpanded);
        section.classList.toggle("is-collapsed", !decksExpanded);
      }
      if (toggle) {
        toggle.setAttribute("aria-expanded", String(decksExpanded));
        toggle.textContent = decksExpanded ? "收起" : "查看全部";
        toggle.setAttribute("title", decksExpanded ? "收起" : "查看全部");
      }
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
      return visible.map((deck) => {
        const updated = formatSidebarTime(deck.updated_at || deck.created_at);
        return `
          <button class="side-deck" type="button" data-jump="deck-list" title="${escapeHtml(deck.title)}">
            ${icon("file")}<span>${escapeHtml(deck.title)}</span><em>${escapeHtml(updated)}</em>
          </button>
        `;
      }).join("");
    }

    function renderDeckShelf() {
      const visible = filteredDecks();
      if (visible.length === 0) {
        return `<div class="deck-empty">${searchQuery.trim() ? "没有匹配的 PPT" : "暂无 PPT"}</div>`;
      }
      const shown = decksExpanded ? visible : visible.slice(0, 3);
      return `<div class="deck-list">${shown.map(renderDeck).join("")}</div>`;
    }

    function renderDeck(deck) {
      const files = filesByDeck.get(deck.id) || [];
      const pptx = files.find((file) => file.kind === "pptx");
      const preview = files.find((file) => file.kind === "preview");
      const previewImage = files.find((file) => file.kind === "preview" && String(file.content_type || "").startsWith("image/"));
      const jobs = jobsByDeck.get(deck.id) || [];
      const state = workflowState(deck, jobs, files);
      const updated = formatDeckTime(deck.updated_at || deck.created_at);
      const progress = state.isRunning ? `
        <div class="mini-progress" aria-label="生成进度 ${state.percent}%">
          <span style="width: ${state.percent}%"></span>
        </div>
        <strong class="mini-percent">${state.percent}%</strong>
      ` : "";
      return `
        <article class="deck-row">
          ${renderDeckCover(deck, previewImage)}
          <div class="deck-main">
            <h2 class="deck-title">${escapeHtml(deck.title)}</h2>
            <div class="deck-meta">
              <span class="pill ${statusClass(deck.status)}">${statusLabel(deck.status)}</span>
              <span>${escapeHtml(deckPageLabel(deck))}</span>
              <span>SJTU 模板</span>
              <span>${escapeHtml(updated)}</span>
            </div>
          </div>
          <div class="deck-actions">
            ${state.isRunning ? progress : renderPreviewAction(preview)}
            ${pptx ? `<a class="row-action primary" href="${api}/files/${pptx.id}/download">${icon("download")}下载 PPTX</a>` : ""}
            <button class="row-more" type="button" aria-label="更多操作">⋮</button>
          </div>
        </article>
      `;
    }

    function renderCurrentWorkflow() {
      const deck = decks[0];
      if (!deck || deck.status === "draft") return "";
      const jobs = jobsByDeck.get(deck.id) || [];
      const files = filesByDeck.get(deck.id) || [];
      const state = workflowState(deck, jobs, files);
      return `
        <section class="workflow-section" aria-label="当前生成进度">
          ${renderFlowSteps(state)}
          ${renderTaskCard(deck, state, files)}
        </section>
      `;
    }

    function renderFlowSteps(state) {
      return `
        <div class="flow-steps">
          ${state.steps.map((label, index) => {
            let cls = "future";
            if (index < state.completeCount) cls = "done";
            if (index === state.activeIndex && !state.isDone) cls = state.isFailed ? "failed" : "active";
            if (state.isDone) cls = "done";
            return `
              <div class="flow-step ${cls}">
                <span class="flow-dot">
                  ${cls === "done" ? "✓" : index + 1}
                  ${cls === "active" ? "<span class=\\"flow-stars\\"></span>" : ""}
                </span>
                <span class="flow-label">${index + 1} ${escapeHtml(label)}</span>
              </div>
            `;
          }).join("")}
        </div>
      `;
    }

    function renderTaskCard(deck, state, files) {
      const pptx = files.find((file) => file.kind === "pptx");
      const preview = files.find((file) => file.kind === "preview");
      const time = formatTime(deck.updated_at || deck.created_at);
      const meta = `${deckPageLabel(deck)} · SJTU 模板 · ${inferStyleLabel(deck.outline_md)}`;
      const logLines = taskLogLines(state);
      if (state.isDone) {
        return `
          <article class="task-card is-result">
            <div class="task-head">
              <span class="task-icon">${icon("file")}</span>
              <div class="task-title-wrap">
                <h2 class="task-title">${escapeHtml(deck.title)}</h2>
                <div class="task-meta"><span class="pill ready">已完成</span><span>${escapeHtml(time)}</span></div>
              </div>
              <div class="task-actions">
                ${renderPreviewAction(preview)}
                ${pptx ? `<a class="row-action primary" href="${api}/files/${pptx.id}/download">${icon("download")}下载 PPTX</a>` : ""}
              </div>
            </div>
            <p class="task-result-meta">${escapeHtml(meta)}</p>
          </article>
        `;
      }
      const runningClass = state.isRunning && !state.isFailed ? " is-generating" : "";
      const activeLogIndex = runningClass ? logLines.length - 1 : -1;
      return `
        <article class="task-card${runningClass}">
          <div class="task-head">
            <span class="task-icon is-running">${icon("file")}</span>
            <div class="task-title-wrap">
              <h2 class="task-title">${escapeHtml(deck.title)}</h2>
              <div class="task-meta"><span class="pill ${statusClass(deck.status)}">${statusLabel(deck.status)}</span><span>${escapeHtml(time)}</span></div>
            </div>
            <button class="row-action" type="button" data-task-detail>查看详情</button>
          </div>
          <div class="task-summary">正在生成第 ${state.activeIndex + 1} 步：${escapeHtml(state.activeLabel)}</div>
          <div class="task-sub">已完成 ${state.completeCount}/5 步，预计剩余约 ${state.remainingMinutes} 分钟</div>
          <div class="task-log">
            ${logLines.map((line, index) => `<div class="log-line${index === activeLogIndex ? " is-active" : ""}">${escapeHtml(line)}</div>`).join("")}
          </div>
          <div class="task-details" id="task-detail-panel" hidden>
            <pre>${escapeHtml(state.fullLog || deck.outline_md || "暂无更多细节")}</pre>
          </div>
        </article>
      `;
    }

    function workflowState(deck, jobs, files = []) {
      const steps = ["理解需求", "规划大纲", "生成内容", "渲染 PPTX", "完成下载"];
      const plan = jobs.find((job) => job.type === "plan_outline");
      const build = jobs.find((job) => job.type === "build_pptx");
      const pptx = files.find((file) => file.kind === "pptx");
      const failedJob = jobs.find((job) => job.status === "failed");
      const fullLog = formatAgentLog(jobs.map((job) => jobLogs.get(job.id) || "").join("\\n"));
      const hasRenderSignal = /渲染|pptx|deck ir|soffice|已生成/i.test(fullLog);
      const isDone = Boolean(pptx || deck.status === "ready" || build?.status === "succeeded");
      const isFailed = Boolean(failedJob || deck.status === "failed");
      let activeIndex = 0;
      if (plan) activeIndex = 1;
      if (plan?.status === "succeeded") activeIndex = 2;
      if (build && ["queued", "running"].includes(build.status)) {
        activeIndex = hasRenderSignal ? 3 : 2;
      }
      if (isDone) activeIndex = 4;
      if (isFailed && build) activeIndex = Math.max(activeIndex, 3);
      const completeCount = isDone ? 5 : Math.max(0, activeIndex);
      const percent = isDone ? 100 : Math.max(8, Math.min(92, completeCount * 20));
      return {
        steps,
        activeIndex,
        activeLabel: steps[activeIndex] || steps[0],
        completeCount,
        percent,
        fullLog,
        isDone,
        isFailed,
        isRunning: deck.status === "generating" || jobs.some((job) => ["queued", "running"].includes(job.status)),
        remainingMinutes: Math.max(1, Math.ceil((5 - completeCount) / 2))
      };
    }

    function taskLogLines(state) {
      const lines = agentLogLines(state.fullLog).slice(-3);
      if (lines.length) return lines;
      const fallback = [];
      if (state.completeCount >= 1) fallback.push("已完成需求理解");
      if (state.completeCount >= 2) fallback.push("已生成 PPT 大纲");
      if (!state.isDone) fallback.push(`正在处理：${state.activeLabel}`);
      return fallback.length ? fallback.slice(-3) : ["正在准备生成任务"];
    }

    function agentLogLines(logText) {
      return String(logText || "")
        .split("\\n")
        .map((line) => line.trim())
        .filter(Boolean);
    }

    function renderDeckCover(deck, preview) {
      if (preview) {
        return `
          <div class="deck-cover">
            <img src="${api}/files/${preview.id}/download" alt="${escapeHtml(deck.title)} 预览">
          </div>
        `;
      }
      return `
        <div class="deck-cover deck-cover-fallback">
          <span>${escapeHtml(deck.title)}</span>
        </div>
      `;
    }

    function renderPreviewAction(preview) {
      if (preview) {
        return `<a class="row-action preview" href="${api}/files/${preview.id}/download" target="_blank" rel="noopener">${icon("search")}预览</a>`;
      }
      return `<button class="row-action preview is-disabled" type="button" aria-disabled="true">${icon("search")}预览</button>`;
    }

    async function loadDeckSlideCount(deck, files) {
      const deckIr = files.find((file) => file.kind === "deck_ir");
      if (deckIr) {
        try {
          const response = await fetch(`${api}/files/${deckIr.id}/download`, {
            credentials: "same-origin"
          });
          if (response.ok) {
            const payload = await response.json();
            if (Array.isArray(payload.slides) && payload.slides.length > 0) {
              return payload.slides.length;
            }
          }
        } catch (_) {}
      }
      return inferredSlideCount(deck.outline_md);
    }

    function deckPageLabel(deck) {
      const count = deckSlideCounts.get(deck.id);
      if (Number.isFinite(count) && count > 0) return `${count} 页`;
      return inferPageLabel(deck.outline_md);
    }

    function renderInsightChips(outline) {
      return promptInsights(outline).map((item) => `
        <span class="insight-chip">${icon(item.icon)}${escapeHtml(item.label)}</span>
      `).join("");
    }

    function promptInsights(outline) {
      const title = deriveTitle(outline);
      const style = inferStyleLabel(outline);
      return [
        { icon: "file", label: inferPageLabel(outline) },
        { icon: "deck", label: title === "未命名 PPT" ? "主题待定" : title },
        { icon: "spark", label: style },
        { icon: "folder", label: "SJTU 模板" }
      ];
    }

    function inferPageLabel(outline) {
      const count = inferredSlideCount(outline);
      if (Number.isFinite(count) && count > 0) return `${count} 页`;
      return "5-6 页";
    }

    function inferredSlideCount(outline) {
      const text = String(outline || "");
      const requested = requestedPageCount(text);
      if (requested) return requested;

      const pageHeadings = text.match(/^#{1,3}\\s*第\\s*\\d+\\s*页/gmu) || [];
      if (pageHeadings.length > 1) {
        const hasThanks = /^#{1,3}\\s*第\\s*\\d+\\s*页\\s*[·:：\\-—]\\s*(谢谢|致谢|结束)/gmu.test(text);
        return pageHeadings.length + (hasThanks ? 0 : 1);
      }
      return null;
    }

    function requestedPageCount(text) {
      const normalized = String(text || "").replace(/^#{1,3}\\s*第\\s*\\d+\\s*页.*$/gmu, "");
      const range = normalized.match(/(?:制作|生成|做|写|一份|共|总共|约|大约|控制在|需要)?\\s*(\\d{1,2})\\s*[-~到至—]\\s*(\\d{1,2})\\s*页\\s*(?:PPT|ppt|幻灯片)?/u);
      if (range) return Number(range[2]);
      const single = normalized.match(/(?:制作|生成|做|写|一份|共|总共|约|大约|控制在|需要)?\\s*(\\d{1,2})\\s*页\\s*(?:PPT|ppt|幻灯片)?/u);
      if (single) return Number(single[1]);
      return null;
    }

    function inferStyleLabel(outline) {
      const text = String(outline || "");
      if (/汇报|商务|项目|阶段/u.test(text)) return "简洁专业";
      if (/课程|讲解|教学|本科生/u.test(text)) return "课程讲解";
      if (/科普|介绍|入门/u.test(text)) return "科普";
      return "简洁专业";
    }

    function formatDeckTime(value) {
      const date = parseApiTime(value);
      const today = new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }).format(new Date());
      const current = new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }).format(date);
      const time = formatTime(value);
      return current === today ? `今天 ${time}` : `${current} ${time}`;
    }

    function formatSidebarTime(value) {
      const date = parseApiTime(value);
      const today = new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }).format(new Date());
      const current = new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }).format(date);
      if (current === today) return formatTime(value);
      return new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        month: "2-digit",
        day: "2-digit"
      }).format(date).split("/").join("-");
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
        ready: "已完成",
        failed: "失败"
      }[status] || status;
    }

    function deriveTitle(outline) {
      const text = String(outline || "").trim();
      const heading = text.match(/^#{1,3}\\s+(.+)$/m);
      let raw = (heading ? heading[1] : text)
        .replace(/^请(帮我|帮忙)?(制作|生成|做|写)?/u, "")
        .replace(/PPTX?/giu, "PPT")
        .split(/[。！？!?\\n]/)[0]
        .replace(/^(一份)?\\s*\\d+\\s*[-~到至]?\\s*\\d*\\s*页\\s*PPT[，,、\\s]*/u, "")
        .replace(/^(一份)?\\s*PPT[，,、\\s]*/u, "")
        .replace(/[，,；;：:]+$/u, "")
        .trim();
      const about = raw.match(/关于(.+?)(?:的(?:科普|介绍|讲解|汇报)|[，,。]|$)/u);
      const usage = raw.match(/用于(.+?)(?:[，,。]|$)/u);
      if (about) raw = about[1].trim();
      else if (usage) raw = usage[1].trim();
      if (!raw) return "未命名 PPT";
      return raw.length > 24 ? `${raw.slice(0, 24)}...` : raw;
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
        const outline = document.getElementById("outline").value;
        if (!outline.trim()) throw new Error("请先写下需求或大纲");
        const title = deriveTitle(outline);
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
      if (!submit) return;
      submit.disabled = value;
      submit.setAttribute("aria-busy", String(value));
      submit.innerHTML = `${icon(value ? "spark" : "arrowUp")}${value ? "生成中" : "生成 PPT"}`;
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
