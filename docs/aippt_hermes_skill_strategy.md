# AIPPT Hermes Skill Strategy

This note turns the Hermes/MiMo experiments into an operational plan for AIPPT.
The goal is to let Hermes preserve experience and guard execution without
letting it bypass the API, builder, or QA boundaries.

## What Hermes Should Own

Hermes is strongest as a learning planner/reviewer:

- Remember user and lab presentation preferences.
- Convert rough intent into an outline or constrained Deck IR.
- Review whether each slide has a claim and proof.
- Repair Deck IR after validator failures.
- Produce page-local improvement suggestions after preview QA.
- Write reusable lessons into skills and scoped memory.

Hermes should not own:

- jAccount login or authorization.
- Database reads outside the active job.
- Raw file downloads.
- Production secrets.
- Unbounded Python script generation.
- Final acceptance of PPTX artifacts.

## Proposed Production Loop

```text
User input / outline
  |
  v
API creates deck + job workspace
  |
  v
Deterministic builder creates deck.json and deck.pptx
  |
  v
QA creates qa.json + preview images
  |
  v
Hermes reads workspace skill + memory + qa.json
  |
  v
Hermes writes review.md or deck.repaired.json
  |
  v
Worker accepts repair only after validation/build/QA pass
```

Start with Hermes as a shadow reviewer. Move it earlier into planning only after
we can measure that it improves accepted output.

## Skill Package

The project-owned skill lives at:

```text
docs/hermes_skills/aippt-sjtu-ppt/
  SKILL.md
  references/
    builder_contract.md
    memory_policy.md
    quality_gates.md
```

It is intentionally job-workspace oriented. Hermes should load it when a task is
about:

- AIPPT job workspaces.
- SJTU Wine Red + Gold PPT generation.
- Markdown outline to Deck IR conversion.
- PPTX QA and repair.
- User/lab preference memory for presentations.

Install it on a Hermes host with:

```bash
ops/install_hermes_aippt_skill.sh
```

On the `aippt` server, install as root so the system Hermes profile sees it:

```bash
ssh aippt 'bash /srv/aippt/ops/install_hermes_aippt_skill.sh'
```

## Memory Model

Use three scopes:

```text
template memory  global SJTU/AIPPT visual rules
group memory     course/lab shared preferences
user memory      private habits and feedback
```

Suggested preference schema:

```yaml
audience: 研究生 / 青年教师 / 管理者 / 课程学生
tone: 学术克制 / 教学讲解 / 项目汇报 / 路演
density: sparse / normal / dense
language: zh-CN / en-US / bilingual
preferred_components:
  - timeline
  - process_cards
  - fact_cards
avoid:
  - 纯 bullet 堆叠
  - 过多营销话术
  - 字号过小
last_feedback:
  - 2026-05-24: 喜欢显式页模式，继续优化细节
```

Do not store full private PPT content as durable memory unless the user
explicitly asks for that behavior. Store derived preferences and reusable style
signals instead.

## Hermes Entry Points

### 1. Outline Planner

Input:

- User brief.
- User/group/template memory.
- Optional uploaded text.

Output:

- Editable Markdown using explicit pages when the user asks for a fixed page
  count or provides page headings.

Guard:

- Do not include private memory in visible output unless it is a style
  preference.
- Keep speaker notes clearly marked so the parser can drop them.

### 2. Deck IR Reviewer

Input:

- `ir/deck.json`
- Validator output.
- Builder contract reference.

Output:

- `ir/deck.repaired.json` or `logs/hermes_repair.md`.

Guard:

- Use only whitelisted layouts.
- Do not increase page count without explaining why.
- Preserve user-authored explicit page titles.

### 3. Visual QA Reviewer

Input:

- `qa.json`
- Rendered preview PNG/PDF when available.
- Current PPTX style rules.

Output:

- `logs/hermes_review.md`
- Optional suggested outline/IR edits.

Guard:

- Prefer concrete repairs: reduce bullet length, choose process layout, split a
  dense page, add a claim line.
- Do not ask the worker to use unapproved assets or network search.

### 4. Preference Curator

Input:

- User explicit feedback.
- Accepted deck metadata.
- QA deltas before/after repair.

Output:

- Small memory updates, not full transcripts.

Guard:

- Store "what the user likes" rather than the user's confidential content.
- Keep group memory separate from user memory.

## Provider Policy

The Xiaomi MiMo token-plan key used in the research probe is currently treated
as a development/interactive agent key. Do not wire that specific key directly
into automated production backend jobs unless the license permits it.

Production provider integration should be abstracted:

```text
AIPPT_PLANNER_PROVIDER=deterministic|hermes
AIPPT_HERMES_PROVIDER=...
AIPPT_HERMES_MODEL=...
AIPPT_HERMES_ENABLED=false
```

Every model run should record:

- Provider and model.
- Prompt/version id.
- Workspace id.
- Input/output file paths.
- Whether the result was accepted after validation.

## Hard Gates Before Blocking Production Jobs

Hermes can block or repair production jobs only after:

- Per-user memory isolation exists.
- The skill is installed and versioned.
- Toolsets are restricted for worker runs.
- Generated script paths are sandboxed or disabled.
- Builder validation is mandatory after Hermes output.
- PPTX open/render QA is mandatory.
- Failure fallback returns the deterministic deck instead of no deck.

## Recommended Next Implementation

1. Install `aippt-sjtu-ppt` on the server Hermes profile. Done.
2. Add a manually triggered `hermes_review` job type. Done as a
   non-destructive deterministic preflight.
3. Materialize `qa/qa.json` and `logs/hermes_review.md` in review workspaces.
   Done for text/IR/artifact QA.
4. Add rendered preview PNG/PDF inputs to the review workspace.
5. Replace or augment deterministic preflight with a Hermes call that preloads
   `--skills aippt-sjtu-ppt`.
6. Add UI feedback buttons and store derived preference events.
7. Promote Hermes to `ir_repair` only after review quality is consistent.

## Current `hermes_review` Job

The first implementation is deliberately conservative:

- It is manually triggered from the workbench.
- It does not call a production model yet.
- It reads the current outline and latest Deck IR/PPTX file assets.
- It writes `qa/qa.json` and `logs/hermes_review.md`.
- It records the review report as a downloadable `review` file asset.
- It does not change a deck from `ready` to `generating`, and review failure
  does not mark an already generated deck as failed.

This gives us the stable artifact and UI path that Hermes can later occupy.
When model review is enabled, the worker should keep the same output contract:

```text
input/outline.md
ir/deck.json
qa/qa.json
logs/hermes_review.md
```

The model step should be an internal implementation detail behind that contract.
