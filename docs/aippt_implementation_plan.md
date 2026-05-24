# AIPPT Implementation Plan

## Goal

Build a multi-user AI PPT generation service where each user can only see and
operate on their own decks, jobs, files, and logs.

## Phase 1: Product Backbone

- API service with jAccount users, sessions, deck sessions, jobs, and file assets.
- Strict owner-based authorization on every query.
- Production auth uses SJTU jAccount OAuth2; password auth is only temporary
  local scaffolding.
- SQLite for local development, Postgres-ready schema decisions.
- Job workspace manifest convention:

```text
/srv/aippt/jobs/{owner_user_id}/{job_id}/
  AGENTS.md
  manifest.json
  input/
  ir/
  skill/
  assets/
  scripts/
  out/
  logs/
```

The API materializes this workspace when a job is created. The database stores
the raw `workspace_path` for workers, but user-facing API responses do not
expose that path.

## Phase 2: Deterministic Builder

- Deck IR schema and validation.
- Layout whitelist: cover, toc, one_column, two_column, three_column,
  horizontal, comparison, table, summary, thanks.
- Hard text limits before PPTX generation.
- Minimal python-pptx renderer using SJTU colors and predictable spacing.
- Markdown parser promotes cover metadata into the cover slide, normalizes
  `第 N 页 · ...` headings, skips legacy cover placeholder pages, and inserts a
  TOC when there are at least three sections.
- Short one-line requests can be expanded into a simple 5-6 page starter deck
  before the deterministic builder runs.
- QA for page count, readable PPTX, and basic text overflow risks.

## Phase 3: Planner And Worker

- Planner creates Markdown outline and Deck IR.
- Hermes memory stores user and lab preferences for audience, tone, density,
  template choice, and preferred slide components.
- Worker creates isolated job workspaces.
- Worker loop claims queued jobs, writes Deck IR, builds PPTX, and records
  internal artifacts. `run-once` remains available for debugging.
- `hermes_review` jobs create non-destructive QA/review artifacts
  (`qa/qa.json`, `logs/hermes_review.md`) without changing ready deck status.
- Review jobs render deterministic preview artifacts when tools are available:
  `preview/deck.pdf`, `preview/pages/slide-*.png`, and
  `preview/contact-sheet.png`.
- Hermes operates only inside the current job workspace.
- Worker can repair IR and rerun builder on validation/build failures.
- Experimental path: Hermes/MiMo can generate a constrained SJTU-template
  deck spec in a job workspace; deterministic runtime scripts split it into
  per-slide modules and assemble the PPTX after guards and validation.

## Phase 4: Web UI

- jAccount login.
- Deck list scoped to the current user.
- Markdown outline editor.
- Generate PPTX button and job progress view.
- Download through authenticated API only.
- The first thin workbench is live at `/ppt/`; future work should split it into
  structured frontend modules once interaction complexity grows.
- Follow the owner map in `docs/aippt_frontend_plan.md` before adding shared
  components or page CSS.

## Phase 5: Deployment

- Run API and worker as separate services.
- Store secrets in `/srv/aippt/env/aippt.env`.
- Use object storage or protected local file serving for PPTX artifacts.
- Add audit logs for job starts, downloads, and failures.

## Non-Negotiable Security Rules

- Every persisted user-facing object has an `owner_user_id`.
- Every API read/write filters by the authenticated user.
- Raw file paths are never exposed as public download links.
- Hermes receives only the files for the active job.
- Runtime job workspaces cannot install dependencies or access secrets.
