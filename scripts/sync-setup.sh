#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/pip install -e ".[sync]"
echo ""
echo "Done. Copy .env.example to .env, then: npm run sync:web"
