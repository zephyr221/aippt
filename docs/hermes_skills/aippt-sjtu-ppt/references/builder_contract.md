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
  "proof": "source, data point, workflow, formula, or case",
  "support": "definition, example, steps, case, action, data, or source",
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

- One lead line: a claim, teaching goal, or action takeaway.
- Three to four supporting points.
- One support object or structured layout. For teaching/training decks this can
  be definitions, examples, steps, exercises, or action items; for analytical
  decks it can be data, evidence, source, or method.
- Projection-readable density: 2-3 cards or process steps are usually better
  than five small boxes; keep each card to 2-3 short points when possible.

For short teaching prompts, especially "导论" or "入门", expand the deck as a
micro-lesson rather than a topic list: motivation, core vocabulary, smallest
worked example, categories or process, common mistakes, and summary/practice.

## Markdown Design Signals

Hermes may choose safe page design signals in Markdown. Put them directly under
the page heading:

```text
版式：two_column
组件：rich_cards
支撑：本页使用的定义、例子、步骤、案例、行动项、数据、流程、公式或来源
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
concept_diagram
example_walkthrough
stat_callout
quote_block
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

Use `stat_callout` for 2-4 key metrics:

```text
- 设计覆盖：100% / 内容页都要求组件信号
- 展开对象：每页 1 个 / 定义、步骤、案例、数据或公式
```

Use `concept_diagram` for core vocabulary or system relationships:

```text
版式：horizontal
组件：concept_diagram
- 输入 x：样本、特征和可观察信号
- 模型 fθ：把输入映射成预测
- 预测 ŷ：输出类别、数值或排序
- 损失 J：衡量预测与目标的差距，并反馈到训练
```

Use `example_walkthrough` for one worked teaching example:

```text
版式：horizontal
组件：example_walkthrough
- 准备数据：输入、标签、异常检查
- 建立模型：预测关系与参数含义
- 公式：J(θ)=1/m ∑ᵢ L(yᵢ, fθ(xᵢ))
- 验证泛化：留出新样本测试
```

Use `quote_block` for one strong sourced conclusion:

```text
组件：quote_block
支撑：来自 QA 报告和用户反馈。
- 原则：模型做设计决策，builder 做稳定渲染
```

## Renderer Rhythms

The current builder chooses visual rhythm from content cues:

```text
timeline      multiple date anchors
process       arrows, loops, "how it works"
concept map   3-4 related concepts, vocabulary, input/model/output/loss
walkthrough   one concrete teaching example
fact cards    several key-value rows
card grid     mixed takeaways and supporting points
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
