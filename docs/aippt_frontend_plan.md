# AIPPT Frontend Plan

This plan adapts the maintainability rules from
`/Users/k/ai/course/aistudy/docs/UI_DEVELOPMENT_GUIDELINES.md` for the AIPPT
product.

## One-Line Principle

Find the owner before editing. Shared UI belongs in shared components and design
tokens; page-specific layout belongs to that page.

## Product Shape

AIPPT is a logged-in workbench, not a marketing site. The first screen after
login should help a user continue or create PPT work quickly:

- Production login uses SJTU jAccount.
- Deck list scoped to the current user.
- Recent job status and generated artifacts.
- Clear entry point for a new PPT request.
- No public filesystem paths or unauthenticated artifact links.

## Route Map

```text
/login               account entry
/decks               private deck list
/decks/{deck_id}     outline editor, job panel, artifact panel
/decks/{deck_id}/jobs/{job_id}
                     focused job progress and logs
/settings            account and model/runtime preferences
```

`/login` should point users to `/api/auth/jaccount/login`; local development may
offer a small fake-login switch that calls `?dev_login=...`, but production UI
must not expose fake login.

## Owner Map

When a frontend app is added, start with this ownership structure:

```text
apps/web/
  src/api/                 typed API client and auth/session calls
  src/app/                 routing and top-level shell
  src/components/
    app-shell/             sidebar, top bar, account menu
    buttons/               icon buttons, primary/secondary actions
    dialogs/               modal and confirmation surfaces
    forms/                 text fields, inline errors, field groups
    job-status/            job timeline, log preview, progress states
    deck-editor/           Markdown editor and preview split
    artifacts/             PPTX download, preview placeholders
  src/pages/
    login/
    decks/
    deck-workspace/
    job-detail/
    settings/
  src/styles/
    tokens.css             product colors, spacing, typography tokens
    base.css               reset and primitives
    app-shell.css          global shell layout only
```

Rules:

- Tokens only change in `src/styles/tokens.css`.
- Shared components never define page layout.
- Page styles stay under their page owner.
- A component moves to `components/` only after the same pattern appears in
  multiple pages.
- Do not add broad selectors like `.page *`, `.app .btn`, or layout-level
  `!important`.
- Do not use native `alert()`, `confirm()`, or `prompt()` for product flows.
  Use inline errors, toast feedback, or app-owned modal dialogs.
- Do not add runtime CDN dependencies; vendor static assets when needed.

## Core Screens

### Deck List

Purpose: scan and resume private work.

Expected controls:

- Search/filter input.
- Create deck button.
- Deck rows with title, status, updated time, and latest artifact state.
- Empty state with one direct create action.

### Deck Workspace

Purpose: edit outline and trigger generation.

Expected regions:

- Markdown outline editor.
- Preview/read-only outline pane.
- Generation controls.
- Job status panel.
- Artifact panel for authenticated downloads.

The Markdown editor should be the primary authoring path at first. Avoid a
Word/Notion-style editor until the PPT generation contract is stable.

### Job Detail

Purpose: inspect one run.

Expected regions:

- Status timeline.
- Sanitized log preview.
- Links back to deck and artifact panel.
- Failure message with next action.

## API Contract Expectations

The frontend should treat ids as product handles and never rely on filesystem
paths.

Needed API surfaces:

- Current user session.
- Deck CRUD scoped to the logged-in user.
- Job creation and job list scoped to a deck.
- Job detail by id, still scoped to the logged-in user.
- Authenticated artifact download endpoints.

## Verification Checklist

For any UI change:

```bash
git diff --check
```

For layout or shared CSS changes, check:

- Desktop workbench width.
- 390px mobile.
- Long Chinese title and long English word wrapping.
- Empty, queued, running, succeeded, and failed states.
- User A cannot see User B decks, jobs, or artifacts.
