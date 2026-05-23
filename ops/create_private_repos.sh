#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="${REPO_NAME:-aippt}"
REPO_DESCRIPTION="${REPO_DESCRIPTION:-Multi-user AI PPT generation platform}"
GITLAB_BASE_URL="${GITLAB_BASE_URL:-https://git.dev.sjtu.edu.cn}"
GITHUB_REMOTE="${GITHUB_REMOTE:-github-private}"
GITLAB_REMOTE="${GITLAB_REMOTE:-origin}"

if [ ! -d .git ]; then
  git init -b main
fi

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "GITHUB_TOKEN is required to create the GitHub private repo." >&2
else
  echo "Creating GitHub private repo: $REPO_NAME"
  if [ -n "${GITHUB_OWNER:-}" ]; then
    github_url="https://api.github.com/orgs/${GITHUB_OWNER}/repos"
  else
    github_url="https://api.github.com/user/repos"
  fi
  github_response="$(curl -fsS -X POST "$github_url" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -d "{\"name\":\"${REPO_NAME}\",\"description\":\"${REPO_DESCRIPTION}\",\"private\":true}")"
  github_url="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["clone_url"])' <<<"$github_response")"
  git remote remove "$GITHUB_REMOTE" 2>/dev/null || true
  git remote add "$GITHUB_REMOTE" "$github_url"
  echo "Added remote $GITHUB_REMOTE: $github_url"
fi

if [ -z "${GITLAB_TOKEN:-}" ]; then
  echo "GITLAB_TOKEN is required to create the SJTU GitLab private repo." >&2
else
  echo "Creating SJTU GitLab private repo: $REPO_NAME"
  payload="name=${REPO_NAME}&path=${REPO_NAME}&visibility=private&description=${REPO_DESCRIPTION}"
  if [ -n "${GITLAB_NAMESPACE_ID:-}" ]; then
    payload="${payload}&namespace_id=${GITLAB_NAMESPACE_ID}"
  fi
  gitlab_response="$(curl -fsS -X POST "${GITLAB_BASE_URL}/api/v4/projects" \
    -H "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
    --data "$payload")"
  gitlab_url="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["http_url_to_repo"])' <<<"$gitlab_response")"
  git remote remove "$GITLAB_REMOTE" 2>/dev/null || true
  git remote add "$GITLAB_REMOTE" "$gitlab_url"
  echo "Added remote $GITLAB_REMOTE: $gitlab_url"
fi

git remote -v
