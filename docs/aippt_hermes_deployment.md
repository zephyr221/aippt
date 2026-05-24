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
AIPPT_JACCOUNT_REDIRECT_URI=https://your-domain.example/api/auth/jaccount/callback
```
