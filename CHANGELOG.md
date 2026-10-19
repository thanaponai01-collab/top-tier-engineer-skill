# Changelog

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
