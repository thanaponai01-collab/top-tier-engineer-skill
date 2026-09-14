# CLAUDE.md — working on the suite itself

This repo is the `top-tier-engineer` plugin: twenty skill contracts, five isolated gate agents,
four tools, and the law they all answer to. A session here is editing **rules that govern other
repos**, not application code. That changes what "done" means.

## Read first, once per session

- **`PROTOCOL.md`** — the law. §0 who is answering, §1 evidence tags, §2 the Laws, §3 what gets
  written to disk, §4 the registry, §5 verdict lines, §6 fresh eyes, §7 delivering a fix, §8 the
  ratchet, §9 how a report reads. If a skill and `PROTOCOL.md` disagree, `PROTOCOL.md` wins — and
  that disagreement is itself a defect to fix, not a preference to live with.
- **`skills/meta-skills/SKILL.md`** — always-on judgment. Discipline 5 governs every edit made here.

Everything else is loaded on demand. Do not read all twenty skills to answer a question about one.

## The route

Route substantial requests through `top-tier-engineer:boss` before acting — it is this suite's own
router, and this repo is not exempt from it. (Renamed from `chief-engineer` in 2.15.0; the old name
survives only in `runs/` and `CHANGELOG.md`, which are history.)

## Before any commit: five gates, all green

```
python tools/test_tools.py
python tools/structure-report.py --baseline .structure-baseline.json --require-debt-ledger .
bash tools/check-references.sh
bash tools/check-verdict-nouns.sh
# version: plugin.json must equal CHANGELOG.md's newest heading
```

These are the same five `.github/workflows/gates.yml` runs. Report their actual output, not that
you ran them — a gate whose result is described rather than pasted is **(trace-only)** (§1).

## Rules specific to this repo

- **History is never rewritten.** `runs/` holds transcripts of what actually ran and `CHANGELOG.md`
  describes superseded behavior. Both name things that no longer exist, on purpose (Law 2). Renames
  and deletions move forward only; `check-references.sh` excludes both by design.
- **A decision needs two options and a reversibility class**, appended to `DECISION_LEDGER.md`,
  never edited once written. Superseding adds an entry; it does not delete one.
- **Every skill that ends a run declares one verdict noun** in the fixed shape
  `**Verdict noun:** \`NOUN\`` and states which of §5's four states it may emit.
  `meta-skills` ends no run and declares none.
- **A tool path inside `skills/` or `agents/` is written `<root>/tools/…`.** A skill executes in the
  *subject's* working directory, so a bare `tools/x.py` names the subject's file (§1, D020).
  `check-references.sh` fails the build for it.
- **The suite's own register is not the model for a report.** These files are rules, read many
  times, and they use nearly every construction §9 bans. A report is read once, by someone with no
  time. Do not sand one into the other.
- **The session that proposes a skill edit cannot approve it** (Discipline 5). Pass a level-2 edit
  to a fresh context with only the target file and `PROTOCOL.md`; where that is unavailable, mark
  the changelog entry `(same-context review)`.
- **Version lives in `plugin.json`.** `marketplace.json` must not re-add a `version` key (D010).

## Where things are

| Path | What it holds |
|---|---|
| `skills/<name>/SKILL.md` | one contract each; `<root>` is two directories up |
| `agents/` | §6 isolation wrappers — the skill owns the method, the agent owns only the isolation |
| `tools/` | stdlib-only Python + bash gates; `tools/tests/` is one module per tool |
| `PROTOCOL.md` `DECISION_LEDGER.md` `DEBT_LEDGER.md` | the law, the decisions, the accepted debt |
| `CHANGELOG.md` `runs/` | history — append, never rewrite |

## Governing a project with this suite

Claude Code auto-reads a project's `CLAUDE.md`; it does not auto-read this suite. To govern another
repo, paste this into that repo's `CLAUDE.md`:

```
This project is governed by the top-tier-engineer suite.
Route every substantial engineering request through the boss skill
(top-tier-engineer:boss) before acting.
Default to writing nothing to disk: the report is the deliverable (PROTOCOL §3).
Where this project does keep notes at the repo root, read them before writing anything.
If DEBT_LEDGER.md exists, check it before taking the "smallest diff" — a diff that
lands in a file listed there is a withdrawal, not a free move (§8).
```
