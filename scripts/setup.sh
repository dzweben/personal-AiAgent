#!/usr/bin/env bash
# one shot setup for a fresh clone. creates a venv, installs the project, and copies the
# env template so you just have to drop your keys in.
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"

echo "==> creating virtual environment in ./venv"
"$PYTHON" -m venv venv

echo "==> activating and upgrading pip"
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip >/dev/null

echo "==> installing the project (core deps)"
pip install -e .

if [ ! -f .env ]; then
  echo "==> creating .env from the template (remember to add your keys)"
  cp .env.example .env
else
  echo "==> .env already exists, leaving it alone"
fi

echo
echo "all set. next steps:"
echo "  source venv/bin/activate"
echo "  edit .env and add your OPENAI_API_KEY / ANTHROPIC_API_KEY"
echo "  python main.py        # classic flow"
echo "  aiagent research \"...\"  # nicer cli (after: pip install -e .)"
