#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
git pull --ff-only
python migrate.py up
systemctl restart shop-web
systemctl restart shop-worker   # waits for the current batch
