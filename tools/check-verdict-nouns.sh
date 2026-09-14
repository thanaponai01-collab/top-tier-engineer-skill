#!/usr/bin/env bash
# PROTOCOL §5 makes the verdict noun the skill's own to declare (D015). Nothing held
# that: the four skills that named none were found by a human reading nineteen files,
# and the phrasing varies enough that no grep could tell a declaration from a quoted
# example. So each skill states it once in a fixed shape, and this checks three things:
#
#   1. every skill that ends a run declares exactly one noun;
#   2. the noun matches §5's own recovery grep — ALL-CAPS, no hyphens;
#   3. the declared noun also appears in the skill's §5 sentence, so the machine-readable
#      line and the prose around it cannot drift apart.
#
# meta-skills is always-on and ends no run of its own (§4), so it declares none.
set -euo pipefail
cd "$(dirname "$0")/.."

shape='^\*\*Verdict noun:\*\* `[A-Z]+( <[a-zA-Z]+>)?`$'
bad=0
for f in skills/*/SKILL.md; do
  name=$(basename "$(dirname "$f")")
  n=$(grep -cE "$shape" "$f" || true)

  if [ "$name" = "meta-skills" ]; then
    [ "$n" -eq 0 ] || { echo "$f: meta-skills ends no run (§4) and must declare no noun"; bad=1; }
    continue
  fi

  if [ "$n" -ne 1 ]; then
    echo "$f: declares $n verdict nouns, want exactly 1 — a line reading: **Verdict noun:** \`NOUN\`"
    bad=1; continue
  fi

  noun=$(grep -hE "$shape" "$f" | grep -oE '\b[A-Z]+\b' | head -1)
  if ! grep -qE "§5" "$f" || ! grep -E "§5" "$f" | grep -q "$noun"; then
    echo "$f: declares $noun, but no line citing §5 uses it — declaration and prose have drifted"
    bad=1
  fi
done

[ "$bad" -eq 0 ] && echo "verdict nouns: 19 skills declare one, meta-skills exempt"
exit "$bad"
