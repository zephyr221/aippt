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
worked example, categories or process, common mistakes, and summary/next steps.
For intro courses, prefer one throughline example over many scattered examples,
and do not force exercises unless requested.

## Markdown Design Signals

Hermes may choose safe page design signals in Markdown. Put them directly under
the page heading:

```text
版式：two_column
组件：rich_cards
支撑：本页使用的定义、例子、步骤、案例、行动项、数据、流程、公式或来源
洞察：本页一句底部总结
```

`洞察` may also be a transition sentence that explains why the next slide
follows. This is especially useful for intro courses.

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
loop_flow
concept_diagram
example_walkthrough
learning_modes
numbered_cards
compare_matrix
metric_strip
milestone_timeline
project_showcase
media_explain
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

Use `metric_strip` for report overview numbers:

```text
组件：metric_strip
- 系统数量：30+ / 独立开发系统与应用
- 课程支持：240+ / AI 课程深度支持
- 持续开发：16 / 个月持续 AI 开发
- 平台职责：平台 / AI 应用平台负责人
```

Do not feed `metric_strip` long indicator-name lists without values. If the page
has no real numbers, use `fact_grid` or `compare_matrix`.

Use `milestone_timeline` for dated stage cards:

```text
组件：milestone_timeline
- 2024 秋：AI 翻译；AI 转录；本地 A100 部署
- 2024.11：AI 应用平台上线；招生 AI 审核；AI 组卷助手
```

Each milestone should stay compact: one short date/title and at most two short
points.

Use `project_showcase` for representative projects:

```text
组件：project_showcase
- AI 组卷助手：上线平台；大规模使用
- AI 知识库平台：RAG 引擎；课程知识沉淀
```

Use three or four project items and keep each body to one or two concise
outcomes.

Use `media_explain` when a platform/product page needs a screenshot placeholder:

```text
组件：media_explain
支撑：系统首页 / 检索界面截图
- 定位：说明产品解决什么问题
- 底座：说明基础能力
- 应用：说明上层使用场景
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

Use `learning_modes` for four learning paradigms or modes:

```text
组件：learning_modes
- 监督学习：有标签样本；分类或回归；房价预测、垃圾邮件识别
- 无监督学习：没有标准答案；聚类或降维；客户分群、异常发现
- 半监督/自监督学习：少量标签或自造监督信号；表征预训练
- 强化学习：通过奖励学习策略；机器人控制、推荐策略
```

Use `loop_flow` for feedback loops:

```text
组件：loop_flow
- 数据准备：收集样本；清洗异常；划分训练/验证/测试集
- 模型训练：设定目标；更新参数 θ；观察损失
- 效果验证：用新样本比较误差；复盘失败案例
- 迭代上线：补充数据；监控漂移；保留人工复核
```

Use `numbered_cards` for four algorithm, scenario, or recommendation cards:

```text
组件：numbered_cards
- KNN：用相似样本投票；直观易懂；适合小样本
- 决策树：按规则层层划分；解释性强；需要剪枝
- SVM：寻找最大间隔边界；高维小样本表现稳
- 朴素贝叶斯：基于概率假设快速分类；文本分类常见
```

Use `compare_matrix` for 2x2 evaluation or trade-off pages:

```text
组件：compare_matrix
- 分类指标：准确率看总体正确；精确率看误报成本；召回率看漏报风险
- 回归指标：MAE 直观；MSE 放大大误差；R² 解释整体拟合程度
- 泛化检查：训练集和测试集差距；交叉验证；失败样例复盘
- 业务指标：误差是否可接受；是否节省人工；上线后是否持续监控
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
loop flow     feedback cycles and four-step validation loops
concept map   3-4 related concepts, vocabulary, input/model/output/loss
learning map  four paradigms or modes with feedback signals
number cards  numbered algorithm/scenario/recommendation cards
matrix        evaluation metrics, trade-offs, and selection criteria
metrics       report overview with 3-4 large KPI/result numbers
milestones    dated roadmap or stage progress
showcase      representative projects/cases with screenshot placeholders
media explain platform/product screenshot plus explanation
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
