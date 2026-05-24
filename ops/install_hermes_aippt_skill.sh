#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${AIPPT_REPO_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
SKILL_NAME="aippt-sjtu-ppt"
SKILL_SRC="$REPO_ROOT/docs/hermes_skills/$SKILL_NAME"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SKILLS_DIR="$HERMES_HOME/skills"
SKILL_DST="$SKILLS_DIR/$SKILL_NAME"

if [ ! -f "$SKILL_SRC/SKILL.md" ]; then
  echo "missing skill source: $SKILL_SRC/SKILL.md" >&2
  exit 1
fi

mkdir -p "$SKILLS_DIR"
rm -rf "$SKILL_DST"
cp -R "$SKILL_SRC" "$SKILL_DST"
find "$SKILL_DST" -name ".DS_Store" -delete

echo "installed Hermes skill: $SKILL_DST"
echo "try: hermes -z '/skills' --toolsets skills"
