#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
git pull --ff-only
python migrate.py up
systemctl restart accounts-web
systemctl restart accounts-mailer   # waits for the current batch
