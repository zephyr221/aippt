# Git Remote Setup

Created on 2026-05-23:

- GitHub private repo: `https://github.com/zephyr221/aippt.git`
- SJTU GitLab private repo: `https://git.dev.sjtu.edu.cn/moran/aippt.git`

Local remotes follow the existing `course/aistudy` convention:

```bash
git remote -v
# github-private  https://github.com/zephyr221/aippt.git
# origin          https://git.dev.sjtu.edu.cn/moran/aippt.git
```

`main` currently tracks `github-private/main`. Push to both remotes with:

```bash
git push github-private main
git push origin main
```

When off campus, `origin` needs either the campus VPN or a tunnel through
`aippt`/`pj2-ext`; otherwise `git.dev.sjtu.edu.cn` may return the SJTU network
"forbidden" page. The first SJTU push was completed through a local HTTPS
forward to the campus network.
