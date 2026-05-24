# AIPPT Hermes 部署草案

## 当前服务器

- SSH 别名：`aippt`
- IP：`10.119.5.70`
- 跳板内网地址：`192.168.1.17`
- 用户：`root`
- 连接方式：校外经 `pj2-ext` 跳板到 `192.168.1.17`
- 本机 SSH 配置：`/Users/k/.ssh/config`

当前 SSH 配置要点：

```sshconfig
Host aippt 10.119.5.70
    HostName 192.168.1.17
    User root
    IdentityFile ~/.ssh/id_ed25519_servers
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
    HostKeyAlias 10.119.5.70
    ProxyJump pj2-ext
```

## 一键初始化

在服务器上执行：

```bash
bash /path/to/bootstrap_aippt_server.sh
```

如果从本机推送脚本：

```bash
scp /Users/k/ai/aiagent/ops/bootstrap_aippt_server.sh aippt:/root/
ssh aippt 'bash /root/bootstrap_aippt_server.sh'
```

脚本会创建：

```text
/srv/aippt/
  app/
  builder/
  env/
  jobs/
  logs/
  shared/
  vendor/hermes-agent/
  venvs/ppt-builder/
```

说明：服务器上 `git clone` GitHub 会卡住，所以脚本当前使用 GitHub tarball 拉取 Hermes `main` 分支源码，再用 editable install 安装。

## Hermes 定位

Hermes 不只是被当成一个命令行工具安装。我们的用法更接近：

1. 保留 Hermes Agent 源码和 editable Python 环境，方便阅读、调试、定制 worker。
2. App Backend 负责用户、会话、Job 状态、文件存储和权限。
3. Planner 负责生成 Markdown 提纲和 Deck IR。
4. Hermes Worker 只在单个 Job workspace 内修正 IR、调用白名单脚本。
5. SJTU PPTX Builder 用确定性 Python 代码生成 PPTX。

## 第一阶段工程边界

运行时 Job workspace 内禁止安装依赖、联网、读取敏感目录。依赖只在服务器初始化或镜像构建时安装。

推荐每个 Job 的目录：

```text
/srv/aippt/jobs/{owner_user_id}/{job_id}/
  AGENTS.md
  manifest.json
  input/
  ir/
  skill/
  assets/
  scripts/
  out/
  logs/
```

## 初始化后的检查

```bash
ssh aippt 'hermes --help | head'
ssh aippt '/srv/aippt/venvs/ppt-builder/bin/python -c "import pptx; print(\"python-pptx ok\")"'
ssh aippt 'soffice --headless --version'
```

## 已验证状态

2026-05-23 已完成：

- `hermes --help` 可用，服务器安装版本为 `hermes-agent==0.14.0`。
- `/srv/aippt/venvs/ppt-builder/bin/aippt-build --help` 可用。
- `/srv/aippt/venvs/api/bin/aippt-worker run-once` 可用。
- 示例 Deck IR 已在服务器上成功构建为 PPTX。
- API venv 已安装并通过双用户隔离冒烟测试。
- 本地代码已同步到 `/srv/aippt/app/api` 和 `/srv/aippt/builder`。

2026-05-24 已完成 Hermes + Xiaomi MiMo 研发验证：

- Hermes 内置 `xiaomi` provider 可用。
- 服务器 `/root/.hermes/.env` 已配置 `XIAOMI_API_KEY` 和
  `XIAOMI_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1`。
- `/root/.hermes/config.yaml` 默认模型设为 `provider: xiaomi`、
  `default: mimo-v2.5-pro`、`api_mode: chat_completions`。
- 使用 `/models` 验证 endpoint 返回 `mimo-v2.5-pro`、`mimo-v2.5`、
  `mimo-v2-pro`、`mimo-v2-omni` 等模型。
- `hermes --ignore-rules -z ... --provider xiaomi --model mimo-v2.5-pro`
  一次性调用验证成功。
- 研发探针路径：
  `/srv/aippt/hermes_probe/ppt_mimo_20260524124409/`。
- 探针流程：Hermes/MiMo 将原始需求整理为 Markdown 大纲，builder 生成
  Deck IR，再生成 PPTX。
- 探针产物：
  `out/hermes-mimo-aippt-probe.pptx`，Deck IR 与 PPTX 均为 10 页。
- LibreOffice 已能把探针 PPTX 转为 PDF：
  `preview/hermes-mimo-aippt-probe.pdf`。

本次验证暴露并修复了一个 builder 边界 bug：当 Hermes 生成 6 个以上章节时，
目录页会超过 validator 的 bullet 上限。`outline_to_deck` 现在使用统一的
`MAX_BULLETS` 限制目录项数量，并添加了覆盖测试。

## Hermes + MiMo 在 AIPPT 中的建议位置

短期内把 Hermes/MiMo 放在「Planner / Reviewer」层，而不是直接接管 PPTX
生成：

1. Planner：把用户的一段自然语言需求整理成可编辑 Markdown 大纲。
2. IR reviewer：在 Deck IR 校验失败时，读取错误信息并给出修正后的 IR 或
   Markdown。
3. Content reviewer：检查标题长度、bullet 密度、章节顺序和学术表达是否合适。
4. Research assistant：后续可在受控联网和引用记录下做资料搜集，但必须保留
   来源和人工确认。

PPTX 最终生成继续由 `packages/builder` 的确定性代码完成。这样可以保持：

- 用户身份、文件归属、下载权限仍由 AIPPT API 控制。
- 版式坐标、SJTU 视觉规范、文件写入路径可测试、可复现。
- Hermes 的输出可以被用户编辑，也可以被 validator 拦截。
- 多用户场景下每个 job 仍限制在自己的 workspace 内。

## Xiaomi MiMo Key 的合规边界

当前 MiMo key 的套餐说明写明：仅限在兼容的 AI 编程和智能体工具中交互式使用，
不可用于自动化脚本或应用后端。基于这个限制：

- 可以用于服务器上的人工研发、调试和一次性 agent 实验。
- 不应把该 key 写入仓库、浏览器代码、API 响应或前端环境变量。
- 不应直接把该 token-plan key 接入 `aippt-worker` 的生产自动任务。
- 如果要上线自动 PPT 生成，需要更换允许应用后端调用的生产模型服务 key，或
  获得明确授权。

因此，当前生产 worker 仍保持 deterministic builder 路径；Hermes/MiMo 作为
研发验证通道存在。未来接入生产时，应先抽象 `PlannerProvider`，并通过环境变量
显式启用，同时在 job 日志中记录 planner model、provider、prompt version 和
输入输出摘要。

## 需要手动填写的内容

复制 `/srv/aippt/env/aippt.env.example` 为 `/srv/aippt/env/aippt.env`，在服务器本地填写真实密钥：

```bash
cp /srv/aippt/env/aippt.env.example /srv/aippt/env/aippt.env
vi /srv/aippt/env/aippt.env
```

不要把真实密钥提交到仓库。

jAccount 生产配置至少包括：

```bash
AIPPT_APP_ENV=production
AIPPT_SESSION_SECRET=...
AIPPT_SECURE_COOKIES=true
AIPPT_JACCOUNT_CLIENT_ID=...
AIPPT_JACCOUNT_CLIENT_SECRET=...
AIPPT_JACCOUNT_REDIRECT_URI=https://ai4edu.sjtu.edu.cn/aistudy/auth/callback
```
