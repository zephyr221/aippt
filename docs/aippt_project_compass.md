# AIPPT Project Compass

This document is the high-level map for AIPPT after the first working public
slice at `https://ai4edu.sjtu.edu.cn/ppt/`.

## Product Thesis

AIPPT should be a logged-in academic PPT workbench, not a one-shot slide toy.
The user should be able to:

1. Log in with SJTU jAccount.
2. Keep private deck sessions under their account.
3. Edit an understandable Markdown outline.
4. Generate an editable SJTU-style PPTX.
5. Give feedback so the next deck better matches their habits.

The long-term differentiator is not just "AI writes PPT". It is "the system
learns how this user and this lab prefer PPTs to be structured".

## Current Stable Baseline

Implemented and verified:

- Public route: `/ppt/`.
- jAccount login using the same OAuth client family as `aistudy`.
- Multi-user ownership checks in the API and tests.
- Deck/session/job/file entities with `owner_user_id`.
- Worker loop for queued `build_pptx` jobs.
- Isolated job workspace layout under `/srv/aippt/jobs/{owner}/{job}`.
- Deterministic Markdown -> Deck IR -> PPTX builder.
- Short prompt expansion for simple requests such as "做 5-6 页机器学习科普 PPT".
- Editable text-formula rendering for simple math expressions such as
  `J(theta)=1/m sum_i L(y_i, f_theta(x_i))`; these are PPT text boxes, not
  raster images.
- Non-destructive `hermes_review` job path that writes `qa/qa.json` and a
  downloadable `logs/hermes_review.md` report.
- Deterministic preview rendering for review jobs: PDF, page PNGs, and contact
  sheet when LibreOffice/Poppler/Pillow are available.
- Explicit `第 N 页` Markdown mode: one authored page maps to one slide.
- SJTU Wine Red + Gold renderer with timeline, fact-card, card-grid, process,
  cover, thanks, and TOC rhythms.
- Server API and worker managed by systemd.
- GitHub private and SJTU GitLab private remotes.
- Hermes/MiMo research probes for outline planning and modular SJTU-template
  PPT generation.

## Architecture Principle

Keep four responsibilities separate:

```text
API          owns identity, authorization, persistence, artifacts.
Hermes       owns memory, planning, review, and repair.
Builder      owns deterministic geometry, style, validation, PPTX output.
QA           owns preview/render checks and feedback signals.
```

Hermes should not become the authority for user access or raw artifact serving.
The builder should not learn user preferences by itself. The API should not
embed model-specific prompt logic directly into routes.

Visual review is also its own layer. MiMo may be text-only, so AIPPT should not
assume the Hermes planning model can inspect images. The safe contract is:
render PPTX previews, run deterministic checks, optionally ask a separate
vision-capable provider, then feed the text findings back to Hermes.

## Important Lessons So Far

### Markdown Needs Two Modes

Normal Markdown should be interpreted as sections and may get a TOC or chunking.
Explicit page Markdown should be treated as the user's authored page contract:

```text
## 第 2 页 · 开场：一个事实
```

In explicit page mode:

- Do not insert a TOC automatically.
- Do not split one page into continuation slides.
- Ignore planning notes before the first page heading.
- Ignore speaker notes such as `讲者备注`.
- Skip fenced code blocks unless a future layout explicitly supports diagrams.

### PPT Quality Needs Contact-Sheet Thinking

The first version was structurally correct but visually flat because every
content page was the same large rounded box. The current renderer improves the
contact sheet by choosing layout rhythms from content cues:

- Timeline when multiple date anchors appear.
- Process cards when a page describes `→` loops or "how it works".
- Fact cards when several key-value rows exist.
- Card grid for mixed claims and supporting points.

The next style improvements should continue at the layout-system level, not by
manually polishing one generated deck.

### Models Should Plan, Code Should Place

MiMo/Hermes are useful for:

- Claim spine and story order.
- Audience/tone/density decisions.
- Reducing verbose bullet text.
- Choosing among allowed page types.
- Reviewing validation and QA failures.

They should not freely calculate all PPT coordinates or modify production
authorization/storage logic.

They also should not be treated as the visual QA engine unless the configured
provider explicitly supports image input. A text-only model can still improve
slides by reading `qa/qa.json`, `logs/hermes_review.md`, and any optional
`logs/vision_review.md`.

### Formula Support Is Text-Editable First

The current builder can display formula-like content as editable PPT text, using
a math-oriented font when expressions contain symbols such as `=`, `sum`, or
Greek letters. This is intentionally not image rendering. True Office Math
equation objects remain an experiment because `python-pptx` does not expose a
stable high-level equation API.

### Modular Slide Scripts Are Worth Keeping

The Hermes/MiMo SJTU-template probe showed that splitting generated PPT code into
one module per slide is better than one giant script:

- A failed slide can be regenerated alone.
- Review can be page-local.
- The assembler remains deterministic.
- Future workers can parallelize page generation.
- User preference feedback can attach to concrete page types.

## Near-Term Roadmap

### Milestone 1: Better Default PPTs

- Keep improving the deterministic renderer in `packages/builder`.
- Continue improving preview rendering and visual QA artifacts.
- Extend the lightweight visual QA report beyond page count, long text, likely
  overflow, repeated layout, and missing claims.
- Keep deterministic QA useful even without a multimodal model.
- Add a "regenerate with same outline" path in the UI.

### Milestone 2: Hermes As Shadow Reviewer

Run review after deterministic generation in a non-blocking or manually
triggered mode:

```text
outline.md -> deck.json -> deck.pptx -> qa.json
                              |
                              v
                      Hermes-ready review report
```

The current `hermes_review` job writes deterministic `qa/qa.json`,
`logs/hermes_review.md`, and optional preview artifacts without modifying the
deck. The next step is to let Hermes read only those workspace files and write
either an improved `logs/hermes_review.md` or a proposed
`ir/deck.repaired.json`. The worker should decide whether to accept any repair
after validation.

### Milestone 3: Preference Memory

Add explicit feedback controls:

```text
更学术一点
少字一点
多用流程图
保留当前风格
这页不好看
```

Store preferences as scoped data:

```text
user profile     private to one user
group profile    shared by a lab/course group
template profile global AIPPT style rules
```

Only summarized preferences should go into memory. Do not store full private PPT
content as long-term memory by default.

### Milestone 4: Hermes Planner Provider

Abstract planner backends:

```text
PlannerProvider
  deterministic_markdown
  hermes_outline
  hermes_deck_ir
  hermes_mimo_template_spec
```

The API creates the workspace and logs prompt/model versions. The planner writes
editable Markdown or constrained Deck IR, then the builder still validates and
renders.

### Milestone 5: Advanced Template Builder

Promote the current Hermes/MiMo probe only after hardening:

- Script sandbox or subprocess jail.
- AST guard for generated modules.
- No network and no secrets in job environment.
- Per-slide retries.
- Rendered PNG preview QA.
- A clear fallback to the deterministic builder.

## Where New Contributors Should Start

Read in this order:

1. `README.md`
2. `docs/aippt_architecture.md`
3. `docs/aippt_auth.md`
4. `docs/aippt_ops_playbook.md`
5. `docs/aippt_hermes_memory_and_sjtu_template.md`
6. `docs/aippt_hermes_skill_strategy.md`
7. `docs/aippt_visual_qa_strategy.md`
8. `docs/aippt_frontend_plan.md`

Then inspect:

```text
apps/api/aippt_api/services/job_runner.py
apps/api/aippt_api/services/workspaces.py
packages/builder/aippt_builder/outline.py
packages/builder/aippt_builder/render.py
packages/builder/tests/test_outline.py
```

## Engineering Bias

Prefer boring, testable production paths and experimental side channels:

- Put new visual grammar in the builder with tests and preview checks.
- Put long-term taste and habits in Hermes memory.
- Put job-local execution rules in the AIPPT Hermes skill.
- Keep secrets and identity out of model prompts.
