# Component Catalog

Use this reference when planning Markdown or repairing Deck IR. Hermes chooses
the page rhythm; the deterministic builder renders only the safe component
signals below.

## Markdown Design Signals

For each content page, optionally add these plain-text lines immediately after
the page heading:

```text
版式：three_column
组件：rich_cards
支撑：用于展开本页的数据、案例、步骤、定义、行动项、流程、公式或来源
洞察：底部一句总结
```

Allowed layouts:

```text
one_column
two_column
three_column
horizontal
comparison
table
summary
```

Allowed components:

```text
card_grid
rich_cards
fact_grid
timeline
process
stat_callout
quote_block
two_column
three_column
horizontal
table
summary
```

The builder ignores unknown signals. Do not ask it to create free-form
coordinates, generated scripts, SVG logos, or arbitrary new components.

## When To Use Each Component

- `rich_cards`: default for teaching/report pages with one takeaway plus 2-4
  titled support cards.
- `fact_grid`: key-value details such as `指标：含义 / 数值 / 风险`.
- `timeline`: two or more dated events.
- `process`: workflow, agent loop, model training, validation pipeline, or any
  `A -> B -> C` sequence.
- `stat_callout`: 2-4 key metrics or counts that should be read first.
- `quote_block`: one strong conclusion, cited example, warning, or principle.
- `two_column`: input/output, before/after, problem/solution, theory/practice.
- `three_column`: three capabilities, stages, risks, audiences, or methods.
- `horizontal`: 3-5 ordered stages when sequence matters but arrows are not
  essential.
- `table`: compact matrix with at most 5 rows x 4 columns.
- `summary`: final synthesis before the generated thanks page.

## Deck Type Patterns

For brief prompts, choose the deck spine before choosing components:

- Teaching/training decks: motivation, core concepts, smallest worked example,
  categories/process, common mistakes, summary/practice.
- Project reports: conclusion, progress, blockers, risks, decisions, owners.
- Research reports: question, gap, method, experiment, results, limits, next
  validation.
- Product introductions: user scenario, pain, capability workflow, value,
  boundary, pilot plan.

For "机器学习导论", do not jump straight to a list of algorithms. A stronger
teaching flow is: why rules are insufficient, data/model/loss vocabulary,
house-price prediction walkthrough, supervised/unsupervised/reinforcement
tasks, training-validation loop, common mistakes and next practice.

## Content Grammar

Use `标签：要点一；要点二；要点三` for structured cards. Examples:

```text
## 第 3 页 · 它如何工作
版式：horizontal
组件：process
典型流程是数据准备、模型训练、效果评估和迭代改进。
- 数据准备：收集样本；清洗异常值；整理输入特征 x
- 模型训练：用 ŷ=fθ(x) 产生预测；根据误差调整参数 θ
- 效果评估：保留测试集；比较指标；回到数据继续迭代
- 公式：J(θ)=1/m ∑ᵢ L(yᵢ, fθ(xᵢ))
```

For metric slides, make the first segment a large number:

```text
## 第 2 页 · 质量提升先看三项指标
版式：one_column
组件：stat_callout
支撑：QA 报告、预览渲染与用户反馈会进入同一轮改写。
用指标约束生成质量，比只调 prompt 更可靠。
- 设计覆盖：100% / 内容页都要求组件信号
- 展开对象：每页 1 个 / 定义、步骤、案例、数据或公式
- 节奏重复：≤2 页 / 连续同版式会被 QA 提醒
```

For quote slides, put the conclusion after a short label:

```text
## 第 5 页 · 设计原则
版式：one_column
组件：quote_block
支撑：来自当前 AIPPT 生成链路的稳定性约束。
模型做设计决策，builder 做稳定渲染。
- 原则：Hermes 负责版式和展开对象，Python 只执行白名单组件
- 落地：任何 repair 都必须先 validation，再 build，再 QA
```

```text
## 第 4 页 · 方法对比
版式：comparison
组件：two_column
左栏强调规则方法可控但维护成本高，右栏强调模型方法适合复杂模式但需要验证。
- 规则方法：逻辑透明；调试直接；覆盖新场景需要手写规则
- 模型方法：能从样本学习；适合非线性模式；上线后必须持续监控
洞察：选择方法时先看数据闭环，而不是先看模型名。
```

For tables, make the first row the header:

```text
版式：table
组件：table
- 阶段：输入 / 输出 / 验证信号
- 数据准备：样本与标签 / 特征表 / 缺失率与偏差检查
- 模型训练：训练集 / 参数 θ / 损失下降曲线
```

## Full SJTU Skill Source

The legacy full component notes live in:

```text
docs/SJTU PPT 模板/SKILL_SJTU.md
docs/SJTU PPT 模板/generate_claudecode_ppt.py
```

Those files contain richer component ideas such as `icon_label_row` and
`chevron_flow`. Treat them as a design backlog. Production Hermes should only
emit the safe signals listed above until the deterministic builder and QA tests
support more components.
