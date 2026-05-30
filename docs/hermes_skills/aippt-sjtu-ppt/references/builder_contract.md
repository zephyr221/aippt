# Builder Contract

Use this reference when planning Markdown, repairing Deck IR, or interpreting
builder failures in an AIPPT job workspace.

## Production Boundary

The deterministic builder is the only production component that writes final
PPTX geometry. Hermes may propose Markdown or Deck IR repairs, but the worker
must validate and rebuild before accepting output.

## Markdown Rules

### Standard Markdown

When the outline is ordinary section Markdown:

- `#` is the deck title.
- `##` sections become content slides.
- A TOC may be inserted when there are enough sections.
- Long sections may be chunked.

### Explicit Page Markdown

When two or more headings look like this:

```text
## 第 2 页 · 开场：一个事实
## 幻灯片 3：方法路线
```

Treat the document as explicit page mode:

- One authored page maps to one slide.
- Do not auto-insert a TOC.
- Do not create continuation slides.
- Ignore planning notes before the first page.
- Ignore speaker notes such as `讲者备注`.
- Skip fenced code unless a future diagram layout explicitly handles it.
- Preserve the user's page titles after stripping `第 N 页`.

## Deck IR Shape

Top level:

```json
{
  "title": "deck title",
  "author": "",
  "slides": []
}
```

Slide layouts:

```text
cover
section
toc
one_column
two_column
three_column
horizontal
comparison
table
summary
thanks
```

Common slide fields:

```json
{
  "layout": "one_column",
  "title": "slide title",
  "subtitle": "",
  "visual": "rich_cards",
  "bullets": [],
  "columns": [],
  "items": [],
  "table": null,
  "insight": null
}
```

## Text Limits

Current conservative limits:

```text
non-cover title <= 36 characters
bullets per slide <= 5
bullet length <= 90 characters
table <= 5 rows x 4 columns
```

Prefer shorter text than the hard limits. A good academic slide normally has:

- One claim line.
- Three to four supporting points.
- One proof object or structured layout.

## Markdown Design Signals

Hermes may choose safe page design signals in Markdown. Put them directly under
the page heading:

```text
版式：two_column
组件：rich_cards
洞察：本页一句底部总结
```

Allowed `版式` values:

```text
one_column
two_column
three_column
horizontal
comparison
table
summary
```

Allowed `组件` values:

```text
card_grid
rich_cards
fact_grid
timeline
process
two_column
three_column
horizontal
table
summary
```

For structured cards, write bullets as:

```text
- 标签：要点一；要点二；要点三
```

The builder turns these into `columns`, `items`, or `table` fields when the
layout requests it. Unknown signals are ignored; do not emit arbitrary PPTX
coordinates or generated scripts.

## Renderer Rhythms

The current builder chooses visual rhythm from content cues:

```text
timeline      multiple date anchors
process       arrows, loops, "how it works"
fact cards    several key-value rows
card grid     mixed claims and supporting points
```

When repairing Markdown or IR, make cues easy for the builder to detect. For
example, use `2026.03.23 - event` for timeline anchors and `A -> B -> C` for
process flows.

## Commands

When the workspace has `aippt-build` available:

```bash
aippt-build outline input/outline.md ir/deck.json --title "Deck Title"
aippt-build build ir/deck.json out/deck.pptx
```

Only run commands if the job instructions allow it. Do not install missing
dependencies inside the job workspace.
