# AIPPT Operations Playbook

This note records the practical setup details discovered during the first
server and repository bootstrap on 2026-05-23.

## Current Infrastructure

- Development server SSH alias: `aippt`
- Server name: `aippt2026`
- Campus-facing IP given by jCloud: `10.119.5.70`
- Server LAN address from `pj2-ext`: `192.168.1.17`
- Jump path from off campus: local machine -> `pj2-ext` -> `aippt`
- App root on the server: `/srv/aippt`
- Public path: `https://ai4edu.sjtu.edu.cn/ppt/`

Local SSH config uses `HostName 192.168.1.17`, `ProxyJump pj2-ext`, and
`HostKeyAlias 10.119.5.70`. The alias keeps host-key continuity with the IP
first used during manual login.

## Server Bootstrap Lessons

GitHub `git clone` can hang on the server network. The bootstrap script
therefore downloads Hermes Agent from the GitHub tarball endpoint and installs
it editable from `/srv/aippt/vendor/hermes-agent`.

The verified server layout is:

```text
/srv/aippt/
  app/api/
  builder/
  env/
  jobs/
  logs/
  shared/docs/
  vendor/hermes-agent/
  venvs/api/
  venvs/ppt-builder/
```

Verified commands:

```bash
ssh aippt 'hermes --help | head'
ssh aippt '/srv/aippt/venvs/ppt-builder/bin/aippt-build --help'
ssh aippt 'soffice --headless --version'
```

Worker command shape:

```bash
AIPPT_BUILDER_COMMAND=/srv/aippt/venvs/ppt-builder/bin/aippt-build \
  /srv/aippt/venvs/api/bin/aippt-worker run-once
```

The worker reads a queued job from the API database, runs the deterministic
builder inside that job workspace, and records internal file assets for Deck IR,
PPTX, and logs.

## Public Route

The public route is hosted by Nginx on `pj2-ext`:

```text
https://ai4edu.sjtu.edu.cn/ppt/ -> pj2-ext:127.0.0.1:18080 -> aippt:127.0.0.1:18080
```

The direct `pj2-ext -> aippt:192.168.1.17:18080` path timed out, so the stable
setup uses a systemd-managed SSH tunnel instead of opening another cloud
security-group port.

Runtime units:

```bash
ssh aippt 'systemctl status aippt-api'
ssh aippt 'systemctl status aippt-worker'
ssh pj2-ext 'systemctl status aippt-pj2-tunnel'
ssh pj2-ext 'nginx -t'
```

Config files:

```text
aippt:/etc/systemd/system/aippt-api.service
aippt:/etc/systemd/system/aippt-worker.service
pj2-ext:/etc/systemd/system/aippt-pj2-tunnel.service
pj2-ext:/etc/nginx/snippets/aippt-ppt-location.conf
pj2-ext:/etc/nginx/sites-enabled/ai4edu
```

Health checks:

```bash
curl -sS https://ai4edu.sjtu.edu.cn/ppt/health
curl -I https://ai4edu.sjtu.edu.cn/ppt/docs
```

The public root `/ppt/` serves the first thin workbench UI. It uses the same
cookie-authenticated API surface as the docs: jAccount login, deck creation, job
submission, status polling, and authenticated PPTX downloads. The worker unit
runs `aippt-worker loop --sleep-seconds 3`, so queued web jobs are picked up
without a manual `run-once`.

## Git Remotes

The project has two private remotes:

```text
github-private  https://github.com/zephyr221/aippt.git
origin          https://git.dev.sjtu.edu.cn/moran/aippt.git
```

The local `main` branch tracks `github-private/main`, matching the convention
already used by `/Users/k/ai/course/aistudy`.

Routine push:

```bash
git push github-private main
git push origin main
```

## SJTU Git From Off Campus

`git.dev.sjtu.edu.cn` blocks direct off-campus browser and Git access. The
symptom is a "forbidden" page showing the external IP, or Git HTTP errors that
look like authentication failures.

Preferred solutions:

1. Use the campus VPN, then push normally to `origin`.
2. Use an SSH tunnel through `aippt`/`pj2-ext` for one-off operations.

For the initial project creation, a local HTTPS forward worked reliably:

```bash
ssh -N -L 127.0.0.1:18443:git.dev.sjtu.edu.cn:443 aippt
```

GitLab on `git.dev.sjtu.edu.cn` supports creating a private project by pushing
to a new path. The first push to `moran/aippt.git` created the private project.
Do not put SJTU or GitHub tokens on the server; keep credentials local and use a
tunnel when needed.

## Product Security Notes

The API owns identity and authorization. Hermes and the PPTX builder are worker
components and must not decide user access.

Operational rules:

- Every user-facing row has `owner_user_id`.
- Every resource query filters by both id and `owner_user_id`.
- Production authentication uses SJTU jAccount; keep
  `AIPPT_DEV_ALLOW_FAKE_LOGIN=false` and `AIPPT_APP_ENV=production` on servers.
- Password register/login routes are disabled when `AIPPT_APP_ENV=production`;
  keep them as local scaffolding only.
- The current campus setup reuses the jAccount OAuth client from
  `/opt/aistudy/.env` on `pj2-ext`. Map its client id/secret/redirect URI/scope
  into `/srv/aippt/env/aippt.env` as `AIPPT_JACCOUNT_*`; never commit the copied
  client secret. Since the shared redirect URI is
  `https://ai4edu.sjtu.edu.cn/aistudy/auth/callback`, Nginx must keep an exact
  `/aistudy/auth/callback` proxy to AIPPT before the old `/aistudy/ -> /notes/`
  rewrite.
- Job workspaces live under `/srv/aippt/jobs` and are addressed through the API,
  not by exposing raw paths to the browser.
- Hermes receives only the active job workspace.
- Secrets belong in `/srv/aippt/env/aippt.env`, never in Git.

## Next Engineering Direction

The next stable milestone is an end-to-end local job loop:

1. Create a deck under the logged-in user.
2. Create a job for that deck.
3. Materialize an isolated job workspace with `manifest.json`, input snapshot,
   logs, and worker instructions.
4. Let the worker build or repair Deck IR and write authenticated artifacts.

The deterministic worker loop and authenticated artifact download endpoints now
cover this path for `build_pptx` jobs.
