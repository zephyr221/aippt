# AIPPT Implementation Plan

## Goal

Build a multi-user AI PPT generation service where each user can only see and
operate on their own decks, jobs, files, and logs.

## Phase 1: Product Backbone

- API service with users, sessions, deck sessions, jobs, and file assets.
- Strict owner-based authorization on every query.
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
- QA for page count, readable PPTX, and basic text overflow risks.

## Phase 3: Planner And Worker

- Planner creates Markdown outline and Deck IR.
- Worker creates isolated job workspaces.
- Worker run-once loop claims one queued job, writes Deck IR, builds PPTX, and
  records internal artifacts.
- Hermes operates only inside the current job workspace.
- Worker can repair IR and rerun builder on validation/build failures.

## Phase 4: Web UI

- Login/register.
- Deck list scoped to the current user.
- Markdown outline editor.
- Generate PPTX button and job progress view.
- Download through authenticated API only.
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
