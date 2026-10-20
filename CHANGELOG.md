# Changelog

## 1.9.0 - 2026-10-20 - Faster, more honest mutation surveys

- `challenge --auto` copies the tree once per lane instead of twice per mutant. Each lane runs the
  unmutated checks once, then writes every mutant in place, judges it against the selected feature's
  checks only, and reverts it. A lane whose checks leave other files changed is recopied first. On a
  60 MB repo with one check, 6 mutants went from 203 s to 18.6 s.
- `challenge --auto --jobs N` judges mutants in N parallel lanes. With a 1 s check, 6 mutants went
  from 13.1 s (1.8.0) to 8.7 s with one lane and 3.4 s with `--jobs 6`. A `## Run` recipe forces one
  lane. Where copying the tree dominates, more lanes do not help.
- Duplicate mutants are dropped: two operators that produce the same line (`zero-to-one` and
  `int-off-by-one` on `0`) count once, and so does a Python mutant whose syntax tree is unchanged.
- A survivor on a line no check executes is now `UNCOVERED`, found by a probe that aborts before
  that line and still passes. It counts against the score like a survivor, but it names a missing
  check rather than a weak one. JSON adds `uncovered`, `jobs` and `copies`.
- `run` without a `## Run` recipe hashes the checks twice (before and after) instead of three times.
- `challenge.py` exposes `prepare`, `mutable_target`, `judge` and `copy_repo`, so `--mutation` and
  `--auto` judge mutants by the same rules.

## 1.8.0 - 2026-10-20 - Many agents, one checkout

- State writes are atomic: each save goes to a temp file and replaces `.verify-state.json` whole.
  Before, a reader racing six writers saw a half-written file 38 times in 6 seconds.
- Each save takes a short lock (`.verify-state.lock`), re-reads the file and merges. A key the
  saving process did not change keeps what is on disk, receipts are merged per check and
  re-baselines are appended, so a stale save no longer reverts another agent's baseline or drops
  its receipts. Six processes saving 25 receipts each now keep all 150.
- `VERIFY_AGENT=<name>` gives an agent its own loop memory in `.verify-state.<name>.json`: last
  run, NEWLY RED/SAME FAILURE, rounds, scope, doctor and `status`/`report`. The baseline,
  re-baselines and rejection receipts stay in `.verify-state.json` for every agent, so a new name
  cannot escape a freeze and one agent's proof that a check fails counts for all. A bad name exits 2.
- Every `.verify-state*` file is left out of the tree signature, scope, challenge copies and CI
  inputs, so one agent's save does not make another's green stale. Gitignore `.verify-state*`.
- `challenge` no longer calls itself inconclusive because another agent added a receipt meanwhile.

## 1.7.0 - 2026-10-20 - Parallel checks

- `verify.py run --jobs N` runs up to N checks at once and reports them in recipe order, so
  output, loop memory and verdict match a serial run. On a 20-check repo, `--jobs 8` cut a run
  from 7.6s to 1.6s; check execution was 93% of run time. Default stays 1: checks that share an
  app, port or files can collide. Documented in SKILL.md and `references/helpers.md`.

## 1.6.0 - 2026-10-19 - Built for stronger agents

- `require: challenge` (a top-level VERIFY.md line, written by `init`, frozen by `baseline`) keeps
  `run --strict` red with `UNCHALLENGED` until a `challenge` mutation is caught for the current
  checks. `report` lists it under the new `unchallenged` gap.
- `.verify-state.json` is sealed with a content hash. A hand-edited file reads as `STATE FORGED`
  on run and `tampered` on status until it is deleted. Existing unsealed state files read as
  tampered once: delete them and verify again.
- SKILL.md: done includes a caught challenge, the check-strength ladder has no top rung, and a new
  section treats the checker as foolable (separate judge from worker, freeze before building,
  prefer third-party evidence). The build-identity steps are summarized in the project recipe.

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
