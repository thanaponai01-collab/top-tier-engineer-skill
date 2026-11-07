# Dependency health: find what goes bad without anyone touching it

## Intent
<!-- purpose -->The user wants a codebase that stays maintained between changes, not only while
someone is editing it. Every other skill here starts from a change or a request about the code.
Dependencies go bad on their own: a package gets a known security hole, a runtime reaches end of
life, a pinned version falls behind with no record of why, a manifest and its lockfile drift
apart, a package is listed but never imported. Nobody notices until a deploy breaks or an audit
fails. evolve-maintain carries out an upgrade once asked; nothing finds which upgrades are owed.
A plain agent asked "are our dependencies healthy?" will run whatever audit tool it remembers,
read the output, and stop. The skill earns its place only if, on the same request, it finds more
of what is owed (holes in packages pulled in indirectly, end-of-life runtimes, manifest and
lockfile drift, unused packages), breaks less when it upgrades, and leaves a record so the next
run says what is new and what was accepted on purpose and is now due again.
<!-- end state -->The user types one word and gets a plain list of what is owed, worst first, each
with a decision: upgraded with the tests still passing, removed because nothing imports it, or
accepted on purpose with a reason and a date to look again. `python
plugin/skills/dependency-health/scripts/deps.py <repo>` lists findings in `.deps/findings.md`;
`--run CMD` records the tests before any change; `--done --run CMD` refuses done while a
high-severity finding has no decision, the tests got worse, or a manifest changed without its
lockfile, then saves the record the next run compares against and prints `DEPS: done`.
<!-- done when -->Every condition under Acceptance passes, the eval case shows the skill finding
what plain Opus misses on the same request (or the brief records that it ties and why it is kept
or dropped), the skill is registered like its siblings, and the full suite passes.

## Context
<!-- grounding -->
- The user does not read code. The answer must be plain words first, `package version -> version`
  and `file:line` second.
- The user cannot look after hooks, bots, linters or CI rules (no Dependabot, no Renovate config).
  Protection that needs upkeep turns into noise and bypasses. A record of each run replaces it.
- Past ports show plain Opus often ties. Gains came where a script caught what the agent skipped,
  so every rule here is a check the helper runs, not a step to follow. Build the eval case before
  the skill.
- The user wants to invoke it, not ask or type the request each time; it is fine that plain Opus
  already does the work when asked in full (the same reason cleanup exists). So a tie at close to
  plain cost is enough to keep it.
- Helpers are stdlib-only Python. Real audit tools (`pip-audit`, `npm audit`, `npm outdated`,
  `cargo audit`, `govulncheck`) may or may not be installed, and the network may be off. The
  helper uses what is there and says plainly what it could not check; it never reports "no holes"
  for an ecosystem it did not check.
- Evals must be repeatable offline, so the helper takes `--advisories FILE` (known holes and
  end-of-life dates in a fixed JSON shape) in place of a live lookup.
<!-- scope -->A new manual-only skill `plugin/skills/dependency-health/` (SKILL.md and
`scripts/deps.py`, stdlib only), with state in `.deps/`. Ecosystems: Python
(requirements*.txt, pyproject.toml, poetry.lock, uv.lock) and Node (package.json,
package-lock.json) first; others listed as "not checked". Also `tests/test_deps.py`, the eval case
with its plain baseline, and registration in CLAUDE.md, both plugin manifests and CHANGELOG.md.
<!-- non-goals -->
- Carrying out large or major-version upgrades across the code: evolve-maintain's job; the
  finding points there.
- Deploying the upgraded build: safe-release's job.
- Attack surface of the app's own code: threat-model's job.
- Licence compliance, SBOM generation and bots that open upgrade PRs.

## Guardrails
<!-- constraints -->
- One helper, `D`, lean on purpose.
  - `D <repo>` writes `.deps/findings.md`, one line per finding with kind and severity: known hole
    (direct or indirect, with the path that pulls it in), end-of-life runtime or package,
    manifest and lockfile out of step, declared but never imported (Python by AST, Node by
    `require`/`import` text), pinned with no reason recorded. It ends with a "not checked" list.
    With a record from an earlier run it also lists what is new and which accepted findings are
    past their look-again date.
  - `D --run CMD` records the manifests, lockfiles and test result before any change.
  - `D --accept ID --reason TEXT --until DATE` records an accepted finding; no reason or no date
    is refused.
  - `D --done --run CMD` refuses done when a high-severity finding has neither a fix nor an
    acceptance, the tests fail where they passed or ran fewer, or a manifest changed while its
    lockfile did not. Otherwise it saves `.deps/history.json` and prints `DEPS: done`.
- A major-version upgrade is named as a possible change in behavior and pointed at
  evolve-maintain unless the tests cover the code that uses the package.
- SKILL.md body is at most 3,000 characters.
<!-- invariants -->
- No test that passed before fails after, and the command never runs fewer tests.
- An ecosystem that was not checked is never reported as healthy.
- The record is written only by `--done` once it holds.
<!-- escalation -->Accepting a known high-severity hole instead of fixing it is the user's call: the
answer names it in plain words and the acceptance records who decided. The skill commits nothing.

## Freedom
<!-- latitude -->Which audit tools to call when present, how to resolve indirect paths, which
version to upgrade to, whether to fix or accept a low-severity finding, and the order of the work.

## Gates
<!-- precondition -->Stage 1, find: a repo with at least one manifest.
<!-- postcondition -->Findings and the "not checked" list are written, and the tests are recorded
before any change.
<!-- evidence -->`python -m unittest tests/test_deps.py`
<!-- precondition -->Stage 2, decide and fix: the findings and recorded tests exist.
<!-- postcondition -->Each high-severity finding is fixed or accepted with a reason and a date.
<!-- evidence -->`.deps/findings.md` and `python -m unittest tests/test_deps.py`
<!-- precondition -->Stage 3, done: every high-severity finding has a decision.
<!-- postcondition -->Nothing that passed fails, no fewer tests ran, manifests and lockfiles changed
together, and the record is saved; a later run shows what is new and what is due again.
<!-- evidence -->`python -m unittest tests/test_deps.py`

## Output
<!-- deliverable -->`plugin/skills/dependency-health/` with its helper, the eval case with plain
and skill reports, plus the release bookkeeping.
<!-- acceptance -->`tests/test_deps.py` holds every rule above. Each rule, broken in the helper,
turns at least one of its tests red. The eval case has an indirect hole, an end-of-life runtime,
a drifted lockfile, an unused package and a decoy that looks unused but is loaded by name; the
skill arm fixes or accepts the first four and keeps the decoy.
<!-- verification -->`python -m unittest discover tests`

## Eval evidence (2026-11-08, before any build)
Plain Opus, no skill, 3 tries per case. `dependency-health-owed-upgrades`: the finished repo
passed every outcome check 3/3 (indirect urllib3 hole, PyYAML, missing click pin, unused
simplejson, Jinja2 migrated, tzdata and gunicorn kept); the judge passed 1/3 only because two
reports did not say why gunicorn stays ($0.24 a try). `dependency-health-came-back`: after a
merge put the two holed pins back, a fresh agent asked only to add `rich` fixed both pins 3/3,
because recompiling against session 1's tightened requirements.in forced them; the phrase grader
passed 3/3, the judge 0/3 because the reports called it lock drift rather than holes coming back
($0.46 a try). Neither case shows a gap a skill would close. The skill was then built anyway
(1.45.0), lean like cleanup, because the user wants to invoke it rather than explain the request
each time; the cases moved back to `evals/cases/` to show it ties.
