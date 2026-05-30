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
concept_diagram
example_walkthrough
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

The builder ignores unknown signals. Do not ask it to create free-form
coordinates, generated scripts, SVG logos, or arbitrary new components.

## When To Use Each Component

- `rich_cards`: default for teaching/report pages with one takeaway plus 2-4
  titled support cards.
- `fact_grid`: key-value details such as `指标：含义 / 数值 / 风险`.
- `timeline`: two or more dated events.
- `process`: workflow, agent loop, model training, validation pipeline, or any
  `A -> B -> C` sequence.
- `concept_diagram`: core vocabulary where 3-4 concepts relate to each other,
  such as input, model, output, loss, feedback, or boundary.
- `example_walkthrough`: one worked teaching example with input, model/action,
  formula or result, and validation.
- `metric_strip`: report overview with 3-4 large KPI/result numbers plus
  optional workstream detail.
- `milestone_timeline`: dated stages, project roadmap, or multi-phase progress
  with optional screenshot placeholders.
- `project_showcase`: 3-4 representative projects, products, cases, or modules
  that each need a title, short points, and a visual placeholder.
- `media_explain`: left screenshot/image placeholder plus right-side
  positioning, layered structure, and supporting points.
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
  categories/process, common mistakes, summary/next steps.
- Project reports: conclusion/KPIs, progress timeline, representative projects,
  blockers, risks, decisions, owners.
- Research reports: question, gap, method, experiment, results, limits, next
  validation.
- Product introductions: user scenario, pain, screenshot/story, capability
  workflow, value, boundary, pilot plan.

For "机器学习导论", do not jump straight to a list of algorithms. A stronger
teaching flow is: why rules are insufficient, data/model/loss vocabulary,
house-price prediction walkthrough, supervised/unsupervised/reinforcement
tasks, training-validation loop, common mistakes and next steps. Use house-price
prediction as the main throughline across the concept, example, task, and
validation slides; use another example such as spam classification only as a
supporting contrast.

For intro courses with limited time, do not force a practice or understanding
check page unless the user explicitly asks. The harder job is to make the
throughline and transitions clear.

For classroom projection, prefer fewer stronger objects over many tiny boxes:
2-3 cards or steps per content slide are usually more readable than five, and
each card should carry 2-3 short points rather than a paragraph.

## Content Grammar

Use `标签：要点一；要点二；要点三` for structured cards. Examples:

Use `洞察：...` as a transition, not only a summary. A strong transition tells
why the next slide follows, such as "四个词讲清楚后，房价预测就从例子变成了一条
可复用主线。"

For report overview pages, use `metric_strip`:

```text
## 第 2 页 · 三年工作总览
版式：one_column
组件：metric_strip
支撑：用关键数字和两条主线建立汇报全局。
两条主线推进：AI 教学与应用 + AI 教务信息化。
- 系统数量：30+ / 独立开发系统与应用
- 课程支持：240+ / AI 课程深度支持
- 持续开发：16 / 个月持续 AI 开发
- 平台职责：平台 / AI 应用平台负责人
- 主线一：AI 教学与应用开发；课程支持；平台建设；知识库沉淀
- 主线二：AI 教务信息化；评教系统；教学运行监控；修业导师
```

For dated roadmaps, use `milestone_timeline`:

```text
## 第 3 页 · AI 应用开发全景
版式：horizontal
组件：milestone_timeline
16 个月独立开发 30+ 系统，并全部稳定运行。
- 2024 秋：AI 翻译；AI 转录；本地 A100 部署
- 2024.11：AI 应用平台上线；招生 AI 审核；AI 组卷助手
- 2025.5：AI 修业导师；评教系统；研小知智能体
- 2025-2026：教学运行监控；查重系统；AI 知识库 / AIPPT
```

For representative projects, use `project_showcase`:

```text
## 第 4 页 · 代表性项目
版式：horizontal
组件：project_showcase
国家级、省部级平台输出，并沉淀为自研产品。
- AI 组卷助手：上线国家智慧教育平台；中小学大规模使用
- 研小知智能体：为教育部学位中心建设；获得官方感谢信
- 研招自命题查重：保密环境独立开发；600+ 套试卷解析
- AI 知识库平台：高质量 RAG 引擎；教学与学科大模型底座
```

For platform/product explanation, use `media_explain`:

```text
## 第 5 页 · AI 知识库平台
版式：horizontal
组件：media_explain
支撑：AI 知识库首页 / 笔记 / 检索界面截图。
对标腾讯 ima，沉淀教学与学科大模型的基础底座。
- 定位：自研高质量知识库平台，把文档做 RAG 处理，沉淀为可复用知识资产
- 学科大模型建设：向上支撑学科模型
- AI 教学材料与课程：服务教师制作和学生学习
- AI 知识库底座：提供 RAG 引擎和检索能力
```

For concept maps, use `concept_diagram` and order the bullets as the diagram
should read:

```text
## 第 3 页 · 核心思想：从数据中学习规律
版式：horizontal
组件：concept_diagram
支撑：输入、模型、预测和损失四个概念构成学习闭环。
机器学习的核心不是记忆答案，而是学习能迁移到新样本的映射关系。
- 输入 x：图片、文字、表格或传感器记录；需要转成特征；质量决定学习上限
- 模型 fθ：把输入映射成预测；参数 θ 会在训练中更新；复杂度要匹配任务难度
- 预测 ŷ：模型给出对新样本的估计；可以是类别、数值或排序；需要和真实标签比较
- 损失 J：衡量预测与目标的差距；训练让损失变小；验证检查是否只是在背题
```

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

For worked examples, use `example_walkthrough`:

```text
## 第 4 页 · 最小例子：房价预测
版式：horizontal
组件：example_walkthrough
支撑：用房屋面积预测价格，把抽象术语落到一个可算例子。
用房价预测可以串起输入、标签、模型、损失和泛化这五个关键词。
- 准备数据：输入是面积、位置和房龄；标签是成交价；先检查缺失值
- 建立模型：从线性关系开始；预测值写作 ŷ=fθ(x)；参数代表特征影响
- 公式：J(θ)=1/m ∑ᵢ L(yᵢ, fθ(xᵢ))，损失越小代表整体预测越接近标签
- 验证泛化：留出新房源测试；看误差是否稳定；失败样例提示数据问题
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
