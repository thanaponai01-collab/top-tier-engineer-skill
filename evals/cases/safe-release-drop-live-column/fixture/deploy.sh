#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
git pull --ff-only
python migrate.py up
systemctl restart crm-web           # serves the web app and the /v1 API
systemctl restart crm-export-cron
