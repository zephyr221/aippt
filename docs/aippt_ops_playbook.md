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

The deterministic `run-once` loop now covers this path for `build_pptx` jobs.
The next backend step is authenticated artifact download endpoints.
