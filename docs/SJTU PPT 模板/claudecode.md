

# Claude Code 源码核心机制深度解析

以下是按照 PPT 页面结构编排的 Markdown 文稿，每个 `---` 代表一页幻灯片。

---

```markdown
---
# 幻灯片 1：封面
---

# Claude Code 源码核心机制深度解析

> 从 System Prompt 到 MCP 协议，拆解 AI 编程 Agent 的工程细节

**对比框架：** Claude Code / Codex / OpenCode / Gemini-CLI

---
# 幻灯片 2：目录
---

# 目录

1. System Prompt — 动态组装机制
2. 工具系统 — 并发调度 / 延迟加载 / 结果控制
3. 仓库目录树感知
4. Plan 模式
5. Context 压缩管理（五层机制）
6. Sub-Agent 系统
7. 失败处理机制
8. Hooks 系统
9. CLAUDE.md 记忆系统
10. 权限与治理系统
11. 状态持久化与会话恢复
12. MCP 协议集成
13. 预算管理
14. 总结与对比

---
# 幻灯片 3
---

# 1. System Prompt：动态组装，而非静态模板

### 核心差异

- 大多数框架：**写死的静态文本**，启动时原样注入
- Claude Code：**运行时动态组装**，由 `buildEffectiveSystemPrompt` 现场构建

### 默认 Prompt 的"行为契约"

| 规则 | 说明 |
|------|------|
| 工具优先 | 优先用 Read/Grep/Glob，而非 bash 等效命令 |
| 输出风格 | 简洁直接，禁用 emoji、填充词、不必要确认 |
| Memory 机制 | CLAUDE.md 自动发现路径说明 |
| Git 安全 | force push / reset --hard 需显式授权 |
| Skill 调用 | slash command 使用方式说明 |

---
# 幻灯片 4
---

# System Prompt：运行时动态注入的 6 类内容

1. **工具描述** — 遍历所有启用工具的 `prompt()` 方法，禁用则自动消失
2. **MCP 服务器指令** — 连接的 MCP 服务器使用说明
3. **Skill 索引** — 已安装 skill 的 name / description / whenToUse
4. **环境信息** — 平台、日期、工作目录
5. **ToolSearch 提示** — 延迟加载工具的发现方式说明
6. **用户配置覆盖** — 6 层优先级配置合并

### 横向对比

| 特性 | Claude Code | Codex | OpenCode | Gemini-CLI |
|------|-------------|-------|----------|------------|
| Prompt 类型 | 动态组装（6层优先级） | 静态模板 | 按模型选择静态文件 | 静态模板 |
| 工具描述注入 | 每个工具自带 `prompt()` | 静态描述 | 静态描述 | 静态描述 |

---
# 幻灯片 5
---

# 2. 工具系统概览

### 规模

- **约 45 个工具**，分布在 `src/tools/` 下 40+ 个子目录
- 每个工具是独立模块，统一接口声明：
  - ✅ 并发安全性（`isConcurrencySafe`）
  - 📏 最大结果大小（`maxResultSizeChars`）
  - 🔒 权限检查（`checkPermissions`）
  - ⏳ 是否延迟加载（`shouldDefer`）

### 设计目标

> 调度层在 **不了解工具内部实现** 的情况下，统一管理并发、权限和 token 预算

---
# 幻灯片 6
---

# 工具并发调度：isConcurrencySafe

### 规则

- ✅ **只读操作**（Glob / Grep / Read / WebSearch）→ `true`，可并发
- ❌ **写操作**（Edit / Write / Bash）→ `false`，必须串行

### 分批执行示例

模型一次输出：`[Glob, Grep, Read, FileEdit, Glob, Read]`

```
批次 1: [Glob, Grep, Read]  → Promise.all 并发执行
批次 2: [FileEdit]          → 串行执行
批次 3: [Glob, Read]        → Promise.all 并发执行
```

- 最大并发数默认 **10**（可通过环境变量覆盖）
- **隐式影响**：模型需在单次回复中发出多个只读调用，才能利用并发

---
# 幻灯片 7
---

# 工具延迟加载：shouldDefer + ToolSearch

### 问题

工具越多 → Schema 越占 context → Token 浪费严重（尤其 MCP 工具）

### 解法

- `shouldDefer: true` 的工具 → 初始请求中 **只发空壳**（无参数描述）
- 模型调用 **ToolSearch** 搜索关键词 → 框架注入完整 Schema

### ToolSearch 搜索评分

| 匹配来源 | 权重 |
|---------|------|
| `searchHint`（3~10 词能力描述） | 4 分 |
| 工具名 | 2 分 |
| 完整 prompt 描述 | 1 分 |

### 避免破坏 Prefix Cache

- ~~早期方案~~：动态插入已发现工具列表 → cache 每次失效 ❌
- **当前方案**：工具发现信息通过独立 **attachment** 发送，消息序列 prefix 不变 ✅

---
# 幻灯片 8
---

# 工具结果大小控制 & 权限检查

### 结果大小控制

- 每个工具声明 `maxResultSizeChars`
- 超出 → 自动**持久化到磁盘**，模型收到路径引用
- **例外**：Read 工具设为 `Infinity`（否则"读文件→路径→再读"死循环）

### 权限检查

每个工具独立的 `checkPermissions()` → 三种结果：

```
✅ 自动放行 → alwaysAllow 规则匹配
❓ 询问用户 → 无规则匹配
🚫 直接拦截 → alwaysDeny 规则匹配 / Hooks 拦截
```

---
# 幻灯片 9
---

# 工具分类总览

| 类别 | 工具 | 说明 |
|------|------|------|
| **文件操作** | Read / Edit / Write / Glob / Grep / NotebookEdit | 常用 shell 命令抽象为独立工具 |
| **Shell** | Bash | 持久化 shell 会话，跨调用保留环境 |
| **Multi-Agent** | Agent / SendMessage / TeamCreate | 子 Agent 统一入口 + Swarms 协作 |
| **规划** | EnterPlanMode / ExitPlanMode | 权限层面只读约束 |
| **任务追踪** | TaskCreate / TaskUpdate / TaskList / TodoWrite | 任务与进度管理 |
| **搜索 & 网络** | WebSearch / WebFetch / ToolSearch | 网络搜索 + 延迟工具发现 |
| **MCP** | MCPTool / ListMcpResources / ReadMcpResource | 外部工具/资源接入 |
| **高级** | LSP / Worktree / Cron / REPL | 代码导航 / 沙箱 / 定时任务 |

---
# 幻灯片 10
---

# 工具系统横向对比

| 特性 | Claude Code | Codex | OpenCode | Gemini-CLI |
|------|-------------|-------|----------|------------|
| 工具并发 | 自动分批（`isConcurrencySafe`） | 不支持 | batch 工具（手动） | 自动 |
| 延迟加载 | ✅ shouldDefer + ToolSearch | ❌ | ❌ | ❌ |
| 结果大小限制 | 超限存磁盘 | 截断（首尾保留） | 无 | 截断 |
| LSP 工具 | ✅ | ❌ | ✅ | ❌ |
| 语义代码搜索 | ❌ | ❌ | ✅（Exa Code） | ❌ |

---
# 幻灯片 11
---

# 3. 仓库目录树感知

### 各框架策略对比

| 框架 | 方式 | 说明 |
|------|------|------|
| **Claude Code** | 不注入目录树，**注入 git 状态** | 每轮更新，按需探索 |
| Codex | 自动生成 2 层目录树 | 注入 user prompt |
| OpenCode | 硬编码禁用 | `&& false` 强制跳过 |
| Gemini-CLI | 不注入目录树 | 注入 git 工作流指引 |

### Claude Code 的 git 上下文（每轮注入）

- 📌 当前分支名
- 📋 最近几条 commit 记录
- 📝 git status 工作区变更（最多 2000 字符）

### 设计判断

> "当前改了哪些文件" 比 "目录里有哪些文件" **更有决策价值**
>
> 目录结构由模型通过 Glob/Grep/Read **主动探索**，不占固定 token 预算

---
# 幻灯片 12
---

# 4. Plan 模式

### 核心区别

- 大多数框架：Prompt 层面约束 → **靠模型自觉**
- Claude Code：**权限系统层面约束** → `mode = 'plan'`，写操作在权限检查阶段直接拦截

### 三个触发入口

1. 🤖 模型主动调用 `EnterPlanMode`（需先通过 ToolSearch 发现）
2. ⌨️ 启动参数 `--mode plan`
3. 🖱️ 用户 UI 手动切换

### 退出与审批

- 模型调用 `ExitPlanMode` → 规划写入 `.claude/plans/` 下 Markdown
- **UI 弹出审批对话框** → 用户必须手动批准
- 这是整个流程中 **唯一强制用户介入** 的环节

### 限制

- ❌ 禁止在子 Agent 中使用（无法弹出 UI 审批，会永远无法退出）

---
# 幻灯片 13
---

# 5. Context 压缩管理 — 五层递进机制

### 动态触发阈值

- 阈值与当前模型 **context window 动态绑定**
- 公式：`context_window - 输出保留(20K) - buffer(13K)`
- 示例（200K window）：~167K 自动压缩，160K 警告，177K 硬性拦截

### 五层压缩架构

```
第1层: 工具结果预算    → 超限存磁盘（每轮执行）
第2层: 历史片段截断    → 规则打分，删低分消息（不调 LLM）
第3层: 微压缩         → 利用 cache_edits 服务端清理（保 cache）
第4层: 上下文折叠     → 旧内容→摘要，近期保留原始粒度
第5层: 完整摘要压缩   → fork 子 Agent 调 LLM 生成摘要
```

> 从轻量到昂贵，逐层兜底

---
# 幻灯片 14
---

# Context 压缩：第 3 层 — 微压缩（microCompact）

### 核心思路

不修改本地消息 → 利用 API `cache_edits` **服务端**清理旧工具结果

### 两种触发模式

| 模式 | 条件 | 操作 |
|------|------|------|
| 时间触发 | 距上次消息 > 60 分钟（cache 已过期） | 直接修改本地消息，替换为 `[cleared]` |
| 热缓存模式 | cache 仍有效 | 通过 `cache_edits` 服务端注意力屏蔽 |

### 反直觉的关键

> `cache_edits` **不是删除 token**，而是将 attention mask 置 0
>
> 序列位置编码不变 → KV 缓存全部有效 → Cache 持续命中 ✅

### 可清理的工具

Read / Bash / Grep / Glob / WebSearch / WebFetch / FileEdit / FileWrite

---
# 幻灯片 15
---

# Context 压缩：第 4 & 5 层

### 第 4 层：上下文折叠（contextCollapse）

- 将历史分组 → **旧分组归档为摘要**，**近期保留原始粒度**
- 触发：context 用量 ~90% 准备，95% 阻塞触发
- 与 autoCompact **互斥**（避免竞争覆盖）

### 第 5 层：完整摘要压缩（autoCompact）

- Fork 子 Agent 调 LLM 生成完整对话摘要
- 压缩后结构：`[compact_boundary] + [摘要] + [尾部消息] + [重注入 attachments]`
- 重新注入：CLAUDE.md / MCP 指令 / Skill 列表 / Hook 结果

### 横向对比

| 框架 | 触发方式 | 是否调 LLM | 特点 |
|------|---------|-----------|------|
| Claude Code | 响应式，每轮检查 | ✅ fork 子 Agent | 五层递进，attachments 自动恢复 |
| Codex | 预防性 + 响应式 | ✅ | 保留最近用户消息 |
| Gemini-CLI | 主动式 | ✅ | 保留最新 30% 历史 |
| OpenCode | 响应式 | ✅ | 全量替换 |

---
# 幻灯片 16
---

# 6. Sub-Agent 系统

### 统一入口：AgentTool

一个入口 → 通过参数组合路由到 **7 种执行模式**

| 模式 | 触发条件 | 特点 |
|------|---------|------|
| 同步前台 | 默认 | 阻塞等待结果 |
| 异步后台 | `run_in_background: true` | 立即返回 ID，轮询结果 |
| 自动转后台 | 运行 > 120 秒 | 自动切换，避免阻塞 |
| Worktree 隔离 | `isolation: 'worktree'` | 独立 git 副本，主工作区不受影响 |
| 远端执行 | `isolation: 'remote'` | 云端运行（内部功能） |
| Fork 模式 | 实验性 | 继承父 Agent 完整历史 + system prompt |
| Teammate | Swarms 模式 | 独立 tmux session，双向通信 |

---
# 幻灯片 17
---

# Sub-Agent：内置类型 & Context 共享

### 4 种内置 Agent 类型

| 类型 | 工具集 | 适用场景 |
|------|--------|---------|
| general-purpose | 所有工具（除 AgentTool） | 通用复杂任务 |
| Explore | 只读工具 | 代码库探索 |
| Plan | 只读 + ExitPlanMode | 规划阶段 |
| claude-code-guide | Read / Grep / WebSearch | Claude Code 使用答疑 |

- 支持 **用户自定义 Agent**（YAML 定义文件，自动发现注册）

### 父子 Context 共享

- **普通模式**：克隆文件缓存 / 工具结果预算 / 权限上下文 / MCP 连接
- **Fork 模式**：额外继承完整对话历史 + **字节级相同的 system prompt**（保证 cache 命中）

---
# 幻灯片 18
---

# 7. 失败处理机制

### 工具执行错误

- 错误以 `is_error: true` 的 tool_result 返回给模型
- 批次内单个失败 **不中断** 其他工具执行
- **无** 失败计数预算，不会主动终止

### API 错误恢复

| 错误类型 | 处理方式 |
|---------|---------|
| 输出 token 超限 | 自动重试 ≤ 3 次 |
| 请求过长 | 先 autoCompact → 再从头部逐条删消息 |
| 网络失败 | 指数退避重试 |

### 权限拒绝的渐进式升级（Claude Code 特有）

```
连续拒绝 ≥ 3 次 或 累计拒绝 ≥ 20 次
    → 从"自动拒绝" 切换到 "询问用户"
    → 安全阀，避免死循环
```

### ⚠️ 无内置死循环检测

- OpenCode：相同工具+参数连续 3 次 → 询问用户
- Gemini-CLI：注入恢复 prompt → 60 秒强制终止
- Claude Code：仅靠 autoCompact + 用户 ESC 兜底

---
# 幻灯片 19
---

# 8. Hooks 系统（Claude Code 独有）

### 定位

> 将工具调用流程从"黑盒"变为 **可扩展平台**

### 核心能力

| 能力 | Hook 返回字段 |
|------|-------------|
| 🚫 拦截工具调用 | `decision: 'block'` |
| ✏️ 修改工具输入 | `updatedInput` |
| 📎 注入上下文 | `additionalContext` |
| 📝 修改工具输出 | `updatedMCPToolOutput` |
| 💬 替换初始消息 | `initialUserMessage` |
| ⏹️ 终止会话 | `continue: false` |
| 🔑 自动化权限 | `allow / deny` |

### 24 种 Hook 事件覆盖 6 大类别

生命周期 / 工具 / 权限 / Sub-Agent / 用户交互 / 压缩 / 任务 / 系统 / MCP

### 三层配置优先级

**企业管理策略** > **用户级** > **项目级**　|　`--no-hooks` 一键禁用

---
# 幻灯片 20
---

# 9. CLAUDE.md 记忆系统

### 多层目录递归发现

```
~/.claude/CLAUDE.md          ← 全局用户级（最低优先级）
<project_root>/CLAUDE.md     ← 项目级
<current_dir>/CLAUDE.md      ← 目录级
<parent_dirs>/CLAUDE.md      ← 递归向上查找（最高优先级）
```

- 所有文件 **合并注入**，深层目录可覆盖上层规则
- autoCompact 后作为 **attachment 重新注入**，记忆不因压缩丢失

### 典型用途

- 📏 项目约束：代码风格、禁止修改的目录、命名规则
- 🔧 常用命令：build / test / lint
- 🏗️ 架构说明：模块职责、依赖关系
- 📝 **跨会话记忆**：模型可**主动写入**，实现跨会话学习

### 对比

| 框架 | 记忆机制 | 作用范围 |
|------|---------|---------|
| Claude Code | CLAUDE.md（多层递归） | 全局 / 项目 / 目录 |
| Codex | AGENTS.md | 项目级 |
| Gemini-CLI | GEMINI.md | 项目级 |
| OpenCode | 无 | — |

---
# 幻灯片 21
---

# 10. 权限与治理系统

### 四种权限模式

| 模式 | 行为 | 场景 |
|------|------|------|
| `default` | 每次弹确认框 | 交互式 IDE |
| `auto` | AI 分类器自动判断 | CI / 自动化 |
| `plan` | 只读放行，写操作拦截 | 规划阶段 |
| `bypassPermissions` | 跳过所有检查 | 完全自动化 |

### 静态规则：Allow / Deny / Ask

```
alwaysAllow: ["Bash(git *)"]       → git 操作直接放行
alwaysDeny:  ["Bash(rm -rf *)"]    → 始终拒绝
alwaysAsk:   ["Bash(deploy *)"]    → 即使 auto 模式也询问
```

三层优先级：**企业管理策略** > **用户级** > **项目级**

---
# 幻灯片 22
---

# AI 安全分类器（Auto Mode）

### 关键设计

- 不是规则匹配 → 是一次真正的 **AI 模型调用（Claude Opus）**
- 输入：工具调用描述 + 对话历史紧凑编码

### 两阶段分类

| 阶段 | max_tokens | 行为 |
|------|-----------|------|
| Stage 1（快速） | 64 | 输出 yes/no → "不阻止"立即返回 |
| Stage 2（思考） | 4096 | `<thinking>` 链式推理 → 降低误报率 |

### 优化措施

- **35+ 只读工具** 走白名单，直接放行，不调分类器
- 两阶段都利用 **prompt cache** 复用前缀
- 分类器不可用时默认 **Fail-closed**（阻止，而非降级放行）

### Worktree 沙箱隔离

- `isolation: 'worktree'` → 临时 git worktree 副本
- 子 Agent 所有文件操作在隔离副本 → **主工作区不受影响**

---
# 幻灯片 23
---

# 11. 状态持久化与会话恢复

### Session 存储

- 完整 transcript → **JSONL 格式** → `~/.claude/projects/<project_hash>/`
- 记录类型：对话消息 / compact_boundary / 摘要 / 文件替换 / worktree 状态 ...
- System prompt **不存储**（每次恢复时动态重新组装）

### Compact 后的存储结构

```
[旧历史消息...] [compact_boundary] [摘要] [新消息...]
                      ↑
              logicalParentUuid → 指向压缩前最后一条消息
```

- 文件 > 50MB → 跳过 boundary 之前内容，只读后半部分

### 子 Agent Sidechain

```
<sessionId>.jsonl                    ← 主线程
<sessionId>/subagents/
  ├── agent-<id>.jsonl               ← 子 Agent
  └── agent-<id>.meta.json           ← 元数据
```

---
# 幻灯片 24
---

# 跨会话恢复流程（/resume）

### 四步重建

```
Step 1: 确定读取范围
        → 找最后一个 compact_boundary → 只加载其后的消息

Step 2: 重建对话链
        → 按 parentUuid 构建 DAG → 过滤孤立分支 → 输出线性序列

Step 3: 恢复应用状态
        → content-replacement → 文件历史 → TodoWrite → worktree

Step 4: 重新注入动态内容
        → System prompt 重新组装
        → CLAUDE.md / MCP 指令 / Skill 列表重新注入
```

> 恢复后的会话对模型来说与 **未中断的会话基本一致**

---
# 幻灯片 25
---

# 12. MCP 协议集成

### Claude Code 是四个框架中 **唯一完整原生支持 MCP** 的

### 三大能力

| 能力 | 说明 |
|------|------|
| **动态工具扩展** | 第三方服务器注册新工具 `mcp__<server>__<tool>`，与内置工具共享全部调度机制 |
| **资源访问** | 文件 / 数据库 / API 响应等结构化数据的读取 |
| **认证 & 交互** | OAuth 认证流程 + Elicitation 协议（服务器请求用户输入） |

### 配置示例

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "..." }
    }
  }
}
```

> 扩展边界由 **MCP 生态** 而非 Claude Code 本身决定

---
# 幻灯片 26
---

# 13. 预算管理 — 四维度独立控制

| 维度 | 机制 | 说明 |
|------|------|------|
| **Token 预算** | `output_config.task_budget` | 整个 agentic turn 的 token 总量上限，跨 Compact 持续追踪 |
| **成本预算** | `maxBudgetUsd` | 单次会话最大美元成本，CostTracker 实时计算 |
| **工具结果预算** | `maxResultSizeChars` | 单次工具结果字符上限，超限存磁盘 |
| **轮次预算** | `maxTurns` | Agent 最大迭代次数，防失控循环 |

### 横向对比

| 框架 | Token | 成本 | 工具结果 | 轮次 |
|------|-------|------|---------|------|
| Claude Code | ✅ | ✅ | ✅ 存磁盘 | ✅ |
| Codex | ❌ | ❌ | 截断 | ✅ |
| OpenCode | ❌ | ❌ | ❌ | ❌ |
| Gemini-CLI | ❌ | ❌ | 截断 | ✅ |

---
# 幻灯片 27
---

# 总结：Claude Code 的核心设计哲学

### 🧩 动态而非静态

- System Prompt 运行时组装
- 工具 Schema 延迟加载
- 压缩阈值与模型 context window 动态绑定

### 🔒 约束落在系统层，不靠模型自觉

- Plan 模式 → 权限系统层面拦截写操作
- AI 分类器 → 两阶段分类 + 渐进升级
- Worktree → 文件系统级隔离沙箱

### 🔌 平台化而非工具化

- Hooks 系统 → 24 种事件，全生命周期可扩展
- MCP 协议 → 动态接入任意第三方能力
- 自定义 Agent → YAML 定义即注册

### 📊 精细化资源管理

- 五层 Context 压缩递进机制
- 四维度预算独立控制
- 完整的状态持久化与无损会话恢复

---
# 幻灯片 28
---

# 横向对比总览

| 能力维度 | Claude Code | Codex | OpenCode | Gemini-CLI |
|---------|-------------|-------|----------|------------|
| System Prompt | 动态组装 | 静态 | 按模型选择 | 静态 |
| 工具数量 | ~45 | ~5 | ~10 | ~10 |
| 工具并发 | 自动分批 | ❌ | 手动 batch | 自动 |
| 延迟加载 | ✅ | ❌ | ❌ | ❌ |
| Context 压缩 | 五层递进 | 单层 | 单层 | 单层 |
| Sub-Agent | 7 种模式 | 3 角色 | 2 层 | 1 层 |
| Hooks 系统 | 24 种事件 | ❌ | ❌ | ❌ |
| MCP 支持 | ✅ 完整 | ❌ | ❌ | ❌ |
| 预算维度 | 4 维 | 1 维 | 0 维 | 1 维 |
| 权限系统 | AI 分类器 | 静态规则 | 静态规则 | 策略引擎 |

---
# 幻灯片 29
---

# Thank You

### 参考资料

- Claude Code 源码：`src/tools/` / `src/constants/prompts.ts` / `src/query.ts`
- MCP 协议：[modelcontextprotocol.io](https://modelcontextprotocol.io)
- 对比框架：Codex / OpenCode / Gemini-CLI

> Claude Code 各种机制处理的细致程度，比其他开源框架强不少。
> 但这也意味着更高的工程复杂度和理解门槛。

---
```

---

## 使用说明

- 共 **29 页**，每个 `---` 分隔符代表一页幻灯片
- 结构：封面 → 目录 → 13 个主题模块 → 总结对比 → 结束页
- 每页控制在 **可视范围内**，重点用表格和代码块呈现
- 你可以在后续框架中直接用这份 Markdown 生成 `.pptx`，只需告诉我用哪个框架（如 Marp / Slidev / python-pptx 等），我来适配格式