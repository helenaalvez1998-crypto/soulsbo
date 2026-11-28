#!/bin/sh
set -eu
cd /app
python scripts/runtime_preflight.py --project-root /app
exec "$@"
