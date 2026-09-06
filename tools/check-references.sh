#!/usr/bin/env bash
# Every file the live surface names must exist. This is the defect class 2.0.0 shipped:
# the docs kept citing tools that had been deleted, and nothing noticed.
#
# Two things are deliberately not failures:
#   - CHANGELOG.md, DECISION_LEDGER.md and runs/ are excluded entirely. They are
#     history, and naming a file that was deleted is exactly their job.
#   - An ALL_CAPS .md name that does not exist here is an artifact the suite tells a
#     SUBJECT project to write (NOTES.md, THREAT_MODEL.md, CLAUDE.md), not a broken link.
set -euo pipefail
cd "$(dirname "$0")/.."

surface=(PROTOCOL.md README.md MAP.md DEBT_LEDGER.md)
while IFS= read -r f; do surface+=("$f"); done \
  < <(find skills agents tools -type f \( -name '*.md' -o -name '*.py' -o -name '*.sh' \))

missing=0
for f in "${surface[@]}"; do
  # Backtick-quoted paths only: prose names plenty of things that are not files.
  while IFS= read -r ref; do
    [ -e "$ref" ] && continue                                    # named in full
    [ -n "$(find . -name "$(basename "$ref")" -not -path './.git/*' -print -quit)" ] \
      && continue                                                # named by basename
    [[ "$ref" =~ ^[A-Z_]+\.md$ ]] && continue                    # a subject's artifact
    echo "$f: names '$ref', which does not exist"
    missing=1
  done < <(grep -oE '`[A-Za-z0-9_./-]+\.(py|md|json|sh|yml)`' "$f" | tr -d '`' | sort -u)
done

[ "$missing" -eq 0 ] && echo "references: every named file exists"
exit "$missing"
