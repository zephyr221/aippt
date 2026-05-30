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
two_column
three_column
horizontal
table
summary
```

The builder ignores unknown signals. Do not ask it to create free-form
coordinates, generated scripts, SVG logos, or arbitrary new components.

## When To Use Each Component

- `rich_cards`: default for teaching/report pages with one claim plus 2-4
  titled support cards.
- `fact_grid`: key-value evidence such as `指标：含义 / 数值 / 风险`.
- `timeline`: two or more dated events.
- `process`: workflow, agent loop, model training, validation pipeline, or any
  `A -> B -> C` sequence.
- `two_column`: input/output, before/after, problem/solution, theory/practice.
- `three_column`: three capabilities, stages, risks, audiences, or methods.
- `horizontal`: 3-5 ordered stages when sequence matters but arrows are not
  essential.
- `table`: compact matrix with at most 5 rows x 4 columns.
- `summary`: final synthesis before the generated thanks page.

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

Those files contain richer component ideas such as `stat_callout`,
`quote_block`, `icon_label_row`, and `chevron_flow`. Treat them as a design
backlog. Production Hermes should only emit the safe signals listed above until
the deterministic builder and QA tests support more components.
