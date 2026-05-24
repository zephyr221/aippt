# AIPPT Visual QA Strategy

This note clarifies how AIPPT should review visual quality without assuming that
the planning model has vision capability.

## Core Principle

Do not tie visual QA to MiMo.

MiMo/Hermes should be used for:

- Story planning.
- Markdown/Deck IR repair.
- Academic wording and density review.
- User/lab preference memory.
- Reasoning about QA reports.

Visual QA should be a separate layer:

```text
PPTX -> rendered PDF/PNG previews -> deterministic checks -> optional vision model
```

If no vision-capable model is available, the pipeline should still produce a
useful deterministic QA report.

## Capability Split

```text
MiMo / Hermes text planner
  - reads outline.md, deck.json, qa.json
  - writes review.md or repaired deck.json proposal

Deterministic visual QA
  - renders PPTX to PDF/PNG when tools are available
  - checks page count, blank pages, approximate text density, repeated layouts
  - records findings in qa/qa.json

Optional vision reviewer
  - reads preview PNG contact sheet
  - comments on overlap, hierarchy, readability, and visual rhythm
  - writes logs/vision_review.md
```

The optional vision reviewer can be OpenAI, Gemini, Claude, Qwen-VL, or another
approved visual model. It should be selected through provider configuration, not
hard-coded into the Hermes/MiMo planner.

## Deterministic Checks First

The first implementation should not need a multimodal model. It can check:

- PPTX opens with `python-pptx`.
- Page count matches Deck IR.
- PDF conversion succeeds when LibreOffice is available.
- PNG pages are non-empty when Poppler or another renderer is available.
- Very high text count on a slide.
- Repeated content layout across too many adjacent pages.
- Missing title/claim fields in Deck IR.
- Oversized title or bullet strings before rendering.

These checks are not "taste", but they catch many failures cheaply and
reproducibly.

## Contact Sheet

When PNG rendering is available, create:

```text
preview/deck.pdf
preview/pages/slide-01.png
preview/pages/slide-02.png
preview/contact-sheet.png
```

The contact sheet is useful for:

- Human debugging.
- Optional vision model review.
- Regression artifacts when builder styles change.

## Provider Abstraction

Recommended settings:

```text
AIPPT_PREVIEW_RENDER_ENABLED=true
AIPPT_PREVIEW_SOFFICE_COMMAND=soffice
AIPPT_PREVIEW_PDFTOPPM_COMMAND=pdftoppm
AIPPT_PREVIEW_RENDER_DPI=144
AIPPT_VISUAL_QA_ENABLED=false
AIPPT_VISUAL_QA_PROVIDER=none
AIPPT_VISUAL_QA_MODEL=
```

Allowed provider values:

```text
none
deterministic
openai
gemini
claude
qwen_vl
```

`none` and `deterministic` should never call a model. Production should default
to deterministic QA until a visual provider is explicitly configured.

## Review Contract

Regardless of provider, the worker should write:

```text
qa/qa.json
logs/hermes_review.md
```

Optional visual review writes:

```text
logs/vision_review.md
preview/contact-sheet.png
```

Hermes can then read `qa/qa.json` and `logs/vision_review.md` as text. This
allows a text-only model such as MiMo to still reason over visual QA findings
without seeing images directly.

## Why This Matters

This split keeps AIPPT robust:

- MiMo can remain the reasoning/planning model even if it has no image input.
- Visual review can improve independently.
- The default production path remains deterministic and testable.
- Users still get a useful review report when no multimodal model is configured.
