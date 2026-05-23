# Git Remote Setup

This workspace is ready to push to two private remotes:

- GitHub private repository
- SJTU GitLab project on `git.dev.sjtu.edu.cn`

Automated creation requires tokens:

```bash
export GITHUB_TOKEN=...
export GITLAB_TOKEN=...
export REPO_NAME=aippt

# Optional:
export GITHUB_OWNER=...
export GITLAB_NAMESPACE_ID=...

bash ops/create_private_repos.sh
git push -u github main
git push -u sjtu main
```

Current blocker:

- GitHub has no authenticated CLI or SSH identity in this environment.
- `git.dev.sjtu.edu.cn` is reachable through `aippt`, but the local SJTU GitLab
  SSH keys are not accepted by that server yet.

Manual fallback:

1. Create a private GitHub repo named `aippt`.
2. Create a private SJTU GitLab repo named `aippt`.
3. Add remotes:

```bash
git remote add github git@github.com:<owner>/aippt.git
git remote add sjtu git@git.dev.sjtu.edu.cn:<namespace>/aippt.git
git push -u github main
git push -u sjtu main
```

