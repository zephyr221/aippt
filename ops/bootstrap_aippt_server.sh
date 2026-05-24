#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/srv/aippt}"
HERMES_DIR="$APP_ROOT/vendor/hermes-agent"
API_VENV="$APP_ROOT/venvs/api"
BUILDER_VENV="$APP_ROOT/venvs/ppt-builder"
HERMES_REPO="${HERMES_REPO:-https://github.com/nousresearch/hermes-agent.git}"
HERMES_TARBALL="${HERMES_TARBALL:-https://github.com/nousresearch/hermes-agent/archive/refs/heads/main.tar.gz}"

export DEBIAN_FRONTEND=noninteractive

echo "[1/7] Installing system packages"
apt-get update
apt-get install -y \
  ca-certificates \
  curl \
  fontconfig \
  fonts-noto-cjk \
  git \
  libreoffice \
  pkg-config \
  python3 \
  python3-pip \
  python3-venv \
  ripgrep \
  unzip \
  build-essential

echo "[2/7] Installing uv if needed"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

echo "[3/7] Preparing directories under $APP_ROOT"
mkdir -p \
  "$APP_ROOT/app" \
  "$APP_ROOT/builder" \
  "$APP_ROOT/env" \
  "$APP_ROOT/jobs" \
  "$APP_ROOT/logs" \
  "$APP_ROOT/shared" \
  "$APP_ROOT/vendor" \
  "$APP_ROOT/venvs"

echo "[4/7] Fetching Hermes Agent source"
rm -rf "$HERMES_DIR"
mkdir -p "$HERMES_DIR"
curl -L --fail --retry 5 --retry-delay 3 "$HERMES_TARBALL" \
  | tar -xz --strip-components=1 -C "$HERMES_DIR"

echo "[5/7] Creating Hermes development environment"
cd "$HERMES_DIR"
uv python install 3.11
uv venv venv --python 3.11
uv pip install -p venv/bin/python -e ".[all,dev]"
ln -sf "$HERMES_DIR/venv/bin/hermes" /usr/local/bin/hermes

echo "[6/7] Creating PPT builder environment"
uv venv "$BUILDER_VENV" --python 3.11
uv pip install -p "$BUILDER_VENV/bin/python" \
  "python-pptx>=1.0.0" \
  "lxml>=5.0.0" \
  "Pillow>=10.0.0" \
  "pydantic>=2.0.0" \
  "jsonschema>=4.0.0" \
  "PyYAML>=6.0.0" \
  "markdown-it-py>=3.0.0" \
  "regex>=2024.0.0" \
  "rich>=13.0.0" \
  "matplotlib>=3.8.0" \
  "numpy>=1.26.0"

cat > "$APP_ROOT/env/aippt.env.example" <<'EOF'
# Copy to /srv/aippt/env/aippt.env and fill locally.
# Do not commit real secrets.
NOUS_API_KEY=
OPENAI_API_KEY=
AIPPT_ROOT=/srv/aippt
AIPPT_APP_ENV=production
AIPPT_DATABASE_URL=sqlite:////srv/aippt/app/api/aippt.db
AIPPT_SESSION_SECRET=replace-with-a-long-random-secret
AIPPT_SECURE_COOKIES=true
AIPPT_JOBS_ROOT=/srv/aippt/jobs
AIPPT_BUILDER_COMMAND=/srv/aippt/venvs/ppt-builder/bin/aippt-build
AIPPT_JACCOUNT_CLIENT_ID=
AIPPT_JACCOUNT_CLIENT_SECRET=
AIPPT_JACCOUNT_REDIRECT_URI=https://ai4edu.sjtu.edu.cn/ppt/api/auth/jaccount/callback
AIPPT_JACCOUNT_SCOPE=basic
HERMES_AGENT_DIR=/srv/aippt/vendor/hermes-agent
EOF

cat > "$APP_ROOT/README.md" <<'EOF'
# AIPPT Server Layout

- `/srv/aippt/vendor/hermes-agent`: Hermes Agent source and editable venv.
- `/srv/aippt/app`: AI PPT application code.
- `/srv/aippt/builder`: deterministic SJTU PPTX builder code.
- `/srv/aippt/jobs`: isolated per-job workspaces.
- `/srv/aippt/shared`: templates, schemas, and reusable assets.
- `/srv/aippt/logs`: service and worker logs.
- `/srv/aippt/env`: local environment files. Keep secrets out of git.

Useful checks:

```bash
hermes --help
/srv/aippt/venvs/ppt-builder/bin/python -c "import pptx; print('python-pptx ok')"
```
EOF

echo "[7/8] Creating API environment if app/api exists"
if [ -f "$APP_ROOT/app/api/pyproject.toml" ]; then
  uv venv "$API_VENV" --python 3.11
  uv pip install -p "$API_VENV/bin/python" -e "$APP_ROOT/app/api[dev]"
else
  echo "Skipping API environment; $APP_ROOT/app/api/pyproject.toml not found yet."
fi

echo "[8/8] Verifying"
hermes --help >/tmp/aippt-hermes-help.txt || true
"$BUILDER_VENV/bin/python" -c "import pptx, pydantic, jsonschema, markdown_it; print('ppt builder deps ok')"
if [ -x "$API_VENV/bin/python" ]; then
  "$API_VENV/bin/python" -c "from aippt_api.main import create_app; print(create_app().title)"
fi

echo
echo "AIPPT bootstrap complete."
echo "Root: $APP_ROOT"
echo "Hermes: $HERMES_DIR"
echo "API Python: $API_VENV/bin/python"
echo "Builder Python: $BUILDER_VENV/bin/python"
