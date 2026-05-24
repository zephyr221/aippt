# AIPPT Hermes Memory 与 SJTU 模板实验

## 目标

AIPPT 不应只把 Hermes 当成一次性 LLM wrapper。Hermes 更适合承担长期
planner/reviewer 的角色：记住用户和课题组的 PPT 习惯，持续积累对内容密度、
视觉节奏、语气、模板偏好的判断，再把这些偏好注入每次 PPT 规划。

当前研发方向：

1. Hermes 负责记忆、规划、复盘和偏好积累。
2. MiMo 负责 agentic PPT planning，以及受约束的 python-pptx builder 实验。
3. SJTU 模板方法负责把视觉系统落到可编辑 PPTX。
4. AIPPT API 继续负责用户、权限、文件和任务状态。

## Hermes 记忆策略

Hermes 内置 memory 分为两类：

- `MEMORY.md`：项目环境、工具经验、模板规范、工程约定。
- `USER.md`：用户偏好、表达习惯、PPT 风格偏好。

在 AIPPT 中，应逐步把这些记忆拆成多用户命名空间。短期研发阶段可以先使用
服务器上的 Hermes built-in memory；生产阶段需要把记忆归属到 AIPPT 用户：

- 每个用户一份偏好 profile。
- 每个课题组或课程组一份共享模板 profile。
- 每次生成后记录用户显式反馈，例如“少一点营销”“bullet 更短”“多用表格”。
- planner prompt 只读取当前用户和当前课题组可见的偏好。

建议最小偏好结构：

```text
audience: 研究生 / 青年教师 / 管理者 / 招生宣传
tone: 学术克制 / 课程讲解 / 项目路演 / 管理汇报
density: sparse / normal / dense
template: SJTU Wine Red + Gold
preferred_components: 目录分组卡片, insight, step_flow, stat_callout
avoid: 中文斜体, 大面积深酒红, 纯 bullet 堆叠
```

## SJTU 模板方法

`docs/SJTU PPT 模板/` 提供了一个更高级的 PPT 制作方法：

- `SJTU 模板.pptx`：真实模板文件。
- `SKILL_SJTU.md`：模板布局、占位符、颜色、组件和避坑规则。
- `generate_claudecode_ppt.py`：完整 python-pptx 示例。
- `claudecode.md`：按页组织的内容样例。

核心原则：

1. 从模板加载 `Presentation(TEMPLATE_PATH)`，删除默认 slides，保留 layouts。
2. layout 0 做封面，layout 7 做内容页，layout 12 做封底。
3. 内容页只填充模板顶栏 placeholder，不叠加额外 header 装饰。
4. 页面正文由组件系统表达，而不是堆 bullet。
5. MiMo 先负责组件化 deck spec；runtime 再把 spec 拆成逐页模块并拼装。

## 实验命令

在服务器上运行：

```bash
/srv/aippt/ops/hermes_sjtu_mimo_probe.sh
```

也可以传入自定义 brief：

```bash
/srv/aippt/ops/hermes_sjtu_mimo_probe.sh /path/to/brief.md
```

如果脚本和 `docs/` 不在同一个父目录下，可以显式指定：

```bash
AIPPT_REPO_ROOT=/srv/aippt /srv/aippt/ops/hermes_sjtu_mimo_probe.sh
```

脚本会创建：

```text
/srv/aippt/hermes_probe/sjtu_mimo_{timestamp}/
  AGENTS.md
  input/
    brief.md
    mimo_plan.md
  ir/
    deck_spec.raw.json
    deck_spec.json
  skill/
    SKILL_SJTU.md
  assets/
    SJTU 模板.pptx
  scripts/
    sjtu_runtime.py
    write_slide_modules.py
    assemble_deck.py
    slides/
      slide_01.py
      slide_02.py
      ...
  out/
    mimo-sjtu-template.pptx
  preview/
    mimo-sjtu-template.pdf
  logs/
```

实验步骤：

1. Hermes/MiMo 一次性输出 `deck_spec.json`，其中包含故事脊柱、builder
   注意事项、每页 claim、组件语义和内容。
2. 本地解析器把 `deck_spec.json` 同步渲染成可读的 `input/mimo_plan.md`。
3. `write_slide_modules.py` 把 spec 拆成逐页 `slides/slide_XX.py`。
4. `assemble_deck.py` 通过 `sjtu_runtime.py` 逐页拼装并生成 PPTX。

这个结构刻意避免“一份超长脚本生成整套 PPT”。逐页模块的好处是：

- 单页失败可以只重试该页。
- Hermes 可以对某一页做局部审查和修复。
- 用户偏好可以映射到具体页型，例如“路线图页更稀疏”“痛点页多用 KPI”。
- 未来可以并行生成 slide modules，再统一 assemble。

脚本会做最小 guard：

- 禁止生成/拼装模块使用网络库、subprocess、`eval`、`exec`、`os.system`。
- 禁止读取 `/root`、`.env`、`authorized_keys`。
- 先 `py_compile`，再执行。
- 用 `python-pptx` 重新打开产物确认页数。
- 如果有 LibreOffice，会额外转 PDF 预览。

## 与当前 deterministic builder 的关系

短期保留两条路线：

- `aippt-build outline/build`：稳定、可测、适合线上默认生成。
- `hermes_sjtu_mimo_probe.sh`：研发实验，验证 MiMo 规划高级模板 spec，
  再由组件化 runtime 拼装 PPTX 的能力。

当实验稳定后，可以抽象为：

```text
PlannerProvider
  deterministic_markdown
  hermes_mimo_outline
  hermes_mimo_deck_ir

BuilderProvider
  deterministic_sjtu_basic
  hermes_mimo_python_pptx
```

上线前必须补齐：

- per-user memory namespace。
- 生成脚本沙箱。
- 代码审查/AST guard。
- PPTX 预览图和文字溢出 QA。
- 用户反馈回写 memory 的显式入口。

## 当前建议

下一阶段把 `/ppt/` 的体验拆成两步：

1. “生成/改写大纲”：Hermes/MiMo 根据用户偏好做 planning。
2. “生成高级模板 PPT”：默认仍用 deterministic builder，高级实验按钮走
   Hermes/MiMo SJTU template builder。

这样既能吃到 Hermes 记忆的长期收益，也能保留线上服务的稳定性。

## 已验证探针

2026-05-24 模块化探针已在 `aippt` 服务器跑通：

```text
/srv/aippt/hermes_probe/sjtu_mimo_20260524131533/
```

结果：

- MiMo 生成 `ir/deck_spec.json`，包含 9 页、故事脊柱和 builder notes。
- 脚本拆出 9 个逐页模块：`scripts/slides/slide_01.py` 到
  `slide_09.py`。
- `assemble_deck.py` 生成 `out/mimo-sjtu-template.pptx`。
- `python-pptx` 重新打开验证页数为 9。
- LibreOffice 生成 PDF 预览：`preview/mimo-sjtu-template.pdf`。
