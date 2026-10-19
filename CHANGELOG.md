# Changelog

## 1.5.0 - 2026-10-19 - A frozen check cannot be quietly re-frozen

- `verify.py baseline` refuses (exit 1, `BASELINE REFUSED`) when a frozen test or oracle file
  changed, a check command was removed or edited, or a feature's `fail-signal:` changed, unless
  `--reviewed-by <name>` and `--reason <why>` are given. Added checks, test files, oracles and
  features, and `## Run` repairs, still freeze without review.
- Each reviewed re-baseline is recorded in `.verify-state.json` (`rebaselines`: who, why, what,
  HEAD). `status` prints `RE-BASELINED` lines and `report` lists `gaps.rebaselined` until the change
  is committed.
- SKILL.md, triage, answer and VERIFY_FORMAT document the rule and its limit: local state is
  editable, so CI and review rules stay the independent guard.

## 1.4.1 - 2026-10-19 - Docs match what ships

- New `references/helpers.md` documents `loop`, `watch`, `triage`, `contract`, the scaffolds and
  `--stress`/`--quarantine`, including when an agent may quarantine a check.
- `loop` is described as rerun-and-triage (it makes no edits); `watch` is shown with `--max-runs`
  so an agent's shell does not block.
- `ci.md` drops its table of skills that no longer ship and says the CI example lives in the
  source repo, not the installed skill. `VERIFY_FORMAT.md` no longer names the missing
  `features.py`. README drops its `correctness-gate`/`wire-check` note.

## 1.4.0 - 2026-10-19 - One answer reference

- `references/handoff.md` is now `references/answer.md`: one contract for every caller, what they
  pass and what comes back. The table of caller skills that no longer ship is gone, and SKILL.md
  drops its separate handoff row.

## 1.3.0 - 2026-10-19 - Sharper SKILL.md

- Rewrote `SKILL.md` around check quality: what a good check is, the loop, and what to look for
  before saying done. Helper commands are listed in one line instead of explained; detail stays in
  `references/`. Dropped pointers to skills that are no longer shipped.

## 1.2.0 - 2026-10-19 - Maintain mode

- Maintain mode (`references/maintain.md`) is a periodic pass over a project verify skill. It
  has three outcomes: clean, changed or blocked. Its edit scope keeps frozen checks behind a
  person's review. The pass reads every feature from source, runs a live pass over every
  feature, triages drift into map drift, harness gaps and product gaps, and ends on
  `run --strict` + `report`.
- The new `verify.py maintain` is a read-only audit. Per feature it reports `map`, `re-prove`,
  `fix`, `re-drive` or `drive`. It also reports skill-check shape problems, checks changed since
  the baseline, and changed files that no feature claims. Churn counts from a committed
  `last-maintained: <sha>` line in `features/README.md` (or `--since REF`). A check input that
  matches the baseline does not count as churn.
- Create mode now records `last-maintained:`, and generated skills point to maintain mode.

## 1.1.0 - 2026-10-19 - One way in, one answer, create mode

- verify-loop is no longer manual-only. The new description lets users, skills and agents call it
  to verify a change, prove a task is done, or create a project verify skill. SKILL.md gains a
  "How to call me" section.
- One answer for every caller, documented in `references/handoff.md`: the verdict
  (green/red/partial/stale/unverified), the `VERIFY:` line, the observed rejections, what passed
  and the gaps. The new `verify.py report` prints it. `status --json` and `report --json` now
  return `verdict`, `verify_line`, `rejections`, `passed` and `gaps`, and keep the earlier fields.
  `run --json` carries `verify_line`, and the last whole run's line is kept in state.
- Create mode (`references/create.md`) generates a project `.claude/skills/verify/` skill named
  `verify` (Launch, Doctor, Drive, Evidence, Cleanup, Helpers, Verdict) plus a feature map. Each
  feature is tied to a VERIFY.md section with a `fail-signal:` and a `fail-proof:`. The new
  `verify.py scaffold-skill` drafts it from the detected stack, and `verify.py skill-check` lints
  it. `examples/verify-create/` is a proven run. Ideas come from pstack's
  `create-verification-skill` (MIT, see `NOTICE`).

## 1.0.0 - 2026-10-19 - Verify Loop on its own

- Cut from top-tier-engineer 4.66.0, keeping only the `verify-loop` skill, its scripts, its unit
  tests and the `examples/verify-ci` workflow. Other skills, agents, hooks, the eval harness and
  the project docs are removed. The plugin is renamed `verify-loop`.
