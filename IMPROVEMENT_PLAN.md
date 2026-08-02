# IMPROVEMENT_PLAN.md — Design audit of the suite itself, with an executable prescription

```
PROTOCOL: 1.18.0
SUBJECT: top-tier-engineer @ 3651aee
ASKED: "design this plugin skill to be more well organized like real engineer …
        push the limit not just only add things but improve what we have,
        and find the doctrine that limit the plugin skill … spot all the flaws and gaps"
DID:   Audited the suite's wiring, tools, ledgers, and doctrine against its own rules;
       every finding below carries evidence and an executable fix.
SO:    A future session can execute this file top-to-bottom: each phase has concrete
       edits, commands, and an acceptance check that either passes or fails.
COST:  One new file (this one). Executing it touches ~8 files, adds 1 helper module,
       and opens 2 ledger entries. Nothing here is speculative work — every task
       traces to a proven or trace-only finding.
```

**How to execute this file:** work the phases in order. Each task states the files, the
edit, and a proof line. Run the full floor after every phase:

```bash
python tools/test_tools.py && python tools/structure-report.py --baseline .structure-baseline.json --require-debt-ledger . && python tools/registry-check.py
```

Per PROTOCOL §8/§9, the session that executes a phase spawns a fresh-eyes `scrutinize`
gate on its diff before committing (the `top-tier-engineer:scrutinize` agent exists for
exactly this). Suggested release: **1.19.0** for Phases 0–1, **1.20.0** for Phases 2–3.

---

## Part A — Flaws (defects in the current system; fix, don't debate)

### F1 — Nine of nineteen skills lose their trigger text in a live session  **(proven, this session)**

Observed in a live Claude Code session with the plugin installed at 1.18.0 (same commit
as HEAD): the harness skill listing showed **no description at all** for
`evolve-maintain`, `meta-skills`, `perf-optimize`, `problem-framing`, `ship-gate`,
`structure-gate`, `symptom-audit`, `threat-model`, `wire-check`. The other ten showed
full descriptions. All nineteen SKILL.md files *have* descriptions (measured 421–952
chars each, ~12.3 KB total), so the mechanism is **(suspected)** an aggregate
per-plugin character budget in the harness: the first ~10 descriptions fit, the rest
are listed name-only.

**Why this is the worst bug in the plugin:** proactive triggering — the entire routing
premise — depends on the model seeing the description. A session that never read
`chief-engineer` cannot auto-fire `threat-model` on "is this secure?" or `ship-gate` on
"deploy it" when those skills surface as bare names. Half the suite is soft-unwired.

**Fix (all 19 files, `skills/*/SKILL.md` frontmatter only):**
- Compress every `description:` to **≤ 250 characters** of pure trigger text: what it
  does in one clause + the trigger phrases. Delete boundary prose ("Boundaries: X →
  skill-y…") from frontmatter and move it into the skill body under a `## Boundaries`
  heading — the body is read after triggering; the frontmatter is *for* triggering.
- Keep `chief-engineer`'s description the longest (it is the catch-all), but still ≤ 400.

**Acceptance:** `python - <<'EOF'` measuring all description lengths reports max ≤ 400,
total ≤ 5,000 chars; then in a **fresh session** with the updated plugin installed,
confirm all 19 skills surface with descriptions. Record the observation in the
changelog entry as the proof.

### F2 — The Stop hook invokes `python`, the CI invokes `python3`  **(proven)**

`hooks/hooks.json:8` runs `python "${CLAUDE_PLUGIN_ROOT}/tools/stop-gate.py"`. On stock
Debian/Ubuntu/macOS there is no `python` binary — only `python3` — so for every
non-Windows installer the enforcement Stop hook **fails silently on every turn**. The
suite's own CI (`enforcement-floor.yml`) uses `python3` throughout: the two halves of
the enforcement floor disagree about the interpreter's name.

**Fix (`hooks/hooks.json`):** make the command interpreter-agnostic:

```json
"command": "python3 \"${CLAUDE_PLUGIN_ROOT}/tools/stop-gate.py\" 2>/dev/null || python \"${CLAUDE_PLUGIN_ROOT}/tools/stop-gate.py\""
```

(`python3` first: on Windows, `python3` is at worst the Store alias stub which exits
non-zero and falls through to `python`; on Linux/macOS it succeeds first try. Verify the
fallthrough on this Windows machine before committing — that check is the proof line.)

**Acceptance:** hook fires and exits correctly under both names; add a
`test_tools.py` test asserting `hooks/hooks.json` contains both interpreter forms.

### F3 — D-5's repayment trigger has already fired; four tools carry a documented latent crash  **(proven)**

`DEBT_LEDGER.md` D-5 defers extracting the encoding guard until "the fourth tool that
needs this guard." Grep shows **six** tools carry it today — `verdict-lint.py:300`,
`run-trace.py:412`, `stop-gate.py:197`, `structure-report.py:120`, `graph-audit.py:296`,
`registry-check.py:152` — in two drifted variants, which is exactly the rot the
duplication signal predicts. Worse: four of them (`verdict-lint`, `run-trace`,
`structure-report`, `graph-audit`) guard **stdout only**, and `stop-gate.py:192`'s own
comment documents that the stdout-only variant leaves stderr crashable
(`UnicodeEncodeError` on Windows cp1252 the moment an error message contains non-ASCII —
and the reports are full of `—`, `·`, `⚠️`).

**Fix (repay D-5, per its own pre-authorized repayment path):**
1. Create `tools/_encoding.py` (~10 lines): `def utf8_streams(): for stream in
   (sys.stdout, sys.stderr): reconfigure to utf-8 if supported`.
2. All six tools import and call it; delete the six inline copies. D-5's row already
   re-scopes the standalone-copy guarantee to "vendor two files, not one."
3. Move D-5 to the **Repaid** table with date and method; regenerate
   `.structure-baseline.json` — legitimate per §10 rule 3, this is repayment — which
   also removes the `duplication|tools/registry-check.py` entry.
4. Add a `test_tools.py` test: every tool in `tools/` that writes output imports
   `_encoding` (grep-based), and a functional test piping tool stderr through a
   cp1252-encoded stream without crash.

**Acceptance:** floor passes; `grep -rn "reconfigure" tools/*.py` matches only
`_encoding.py`; DEBT_LEDGER Repaid table gains the row.

### F4 — Repayment triggers are prose nobody watches  **(proven)**

`DEBT_LEDGER.md` declares "a deferral with no trigger is a wish" — but a trigger nothing
*checks* is the same wish one step removed, and F3 is the proof: D-5's trigger fired and
no tool, gate, or run noticed. `.structure-baseline.json` carries frozen values but zero
machine-readable triggers (the numeric ones — D-3: 700 SLoC, D-4: 800 SLoC — live only
in table prose).

**Fix (`tools/structure-report.py` + baseline schema, version 2):**
1. Baseline entries gain an optional `"repay_at": <number>` field, same unit as the
   frozen value. Encode D-3 (`file_lines|tools/structure-report.py|`: 700) and D-4
   (`file_lines|tools/test_tools.py|`: 800). Event-based triggers (D-1, D-2) stay prose.
2. `structure-report.py` ratchet mode: when current ≥ `repay_at`, emit a new verdict
   state `STRUCTURE: repayment-due(id-hint, signal, current/threshold)` and **exit
   non-zero** — distinct from `regressed`, because the debt did not grow past its
   freeze, it grew past its *expiry*. When under, print headroom
   (`626/700 — 74 SLoC headroom`) so drift is visible before it is due.
3. Register the new state: PROTOCOL §5 `STRUCTURE` row + `verdict-lint.py` enforcing
   copy + `registry-check.py` reconciliation (it will catch you if you miss one — that
   is what it is for).
4. Tests: repay_at crossed → exit 1 with `repayment-due`; under → exit 0 with headroom
   line; absent → behavior unchanged.

**Acceptance:** floor passes; deliberately setting `repay_at` below current in a temp
baseline fails the gate with the new state; `registry-check.py` still reports clean.

### F5 — Two director decisions have been open for a month with no forcing function  **(trace-only)**

`DECISION_LEDGER.md` D001 (observability mandate) and D002 (dependency intake) opened
2026-07-04, both gated on "a live run surfaces the finding" — but nothing schedules live
runs (see B2), so the evidence bar is an infinite deferral. Both records already
carry a recommended option marked two-way-reversible.

**Fix:** present both to the director with the §10/§11 precedent — *field reports
satisfy the evidence bar* (both of those PROTOCOL sections entered via use reports, not
runs) — and recommend closing each as its option 1 (fold into `ship-gate` /
`arch-design` checklist) now, promotable later if a run proves prose insufficient.
Additionally open **D005 — concurrency ownership**: `runs/patches/03_capacity_and_race.md`
is a real race-condition fix the suite shipped, and no skill's mandate names
concurrency/atomicity (correctness-gate proves against stated criteria; a race is
exactly the defect nobody states as a criterion). Options: a checklist item in
`correctness-gate` ("shared-resource check-and-claim enumerated as oracle rows") vs. a
new mandate. The patch is the run-earned evidence D001/D002 never got.

**Acceptance:** three ledger entries updated/added, each with decision or explicit
director deferral recorded; `DESIGN:` verdict line in the executing run's report.

---

## Part B — The doctrine that limits the plugin (the ceiling, named)

These are not defects; they are the suite's own laws operating as designed and capping
it. Each gets a resolution that keeps the law's intent.

### B1 — Law 6 absolutism: the suite may not own knowledge, so all learning compresses into ever-denser process prose

Law 6 ("constrain process, never intelligence") bans any load-bearing particular from a
skill. The intent is right — don't cap a stronger model — but the side effect is
structural: every lesson a run earns must be abstracted into process language before it
may enter the suite, which is why PROTOCOL.md reads like case law and grows denser per
release. Real top-tier organizations *codify knowledge* (failure-mode checklists,
error-prone catalogs, runbooks) and Law 6 as written has nowhere to put it — except
tools, where thresholds already live as a sanctioned exception nobody named.

**Resolution (keeps Law 6 intact for skills):** name the exception. A third artifact
tier — **knowledge, owned by tools and reference files** — is legal where skills are
not: machine-readable registries (`.structure-baseline.json` thresholds are already
this), worked-example fixtures, and per-domain checklists stored as *data a tool or
checklist-phase consumes*, explicitly labeled illustrative-and-overridable. Add one
paragraph to PROTOCOL §2 Law 6 defining the tier and its label; the substitution test
still applies to skill bodies unchanged.

### B2 — The evidence bar is reactive-only, and nothing generates evidence

"Justified only if a real run surfaces it" is a good bar against speculative mandates —
but the suite has run against an external subject four times ever (LIVE_RUN_001–004),
and releases 1.14→1.18 are **all introspection**. A learning system whose only teacher
is experience, run on a system that stopped having experiences, stops learning. The
skill-yield metric MAP.md promises ("computed from the gap between pre-run knowledge
and post-run findings") has never been computed.

**Resolution:** a run cadence obligation in PROTOCOL (one external-subject live run per
minor release that changes any skill body — a release that only touches tools/docs is
exempt), plus formally admitting **field reports** as evidence-bar-satisfying (already
the de-facto precedent for §10 and §11 — write it down). First concrete act:
LIVE_RUN_005 against a real external codebase, and compute skill-yield for it.

### B3 — Gate-heavy, improvement-light: the suite judges better than it repairs

Of nineteen mandates, roughly twelve are judgment/gates; only `build-discipline` and
`evolve-maintain` change code, and **nothing owns repayment as a proactive act**.
`structure-gate` detects, `DEBT_LEDGER.md` freezes, and then the ledger waits for a
human to notice a trigger fired — which F3 proves does not happen. This is the
director's exact complaint: the suite adds gates; it does not improve what it has.

**Resolution:** F4 gives repayment a mechanical trigger; close the loop by giving it an
owner: `evolve-maintain` gains intervention class **`Repay`** (routed automatically when
`STRUCTURE: repayment-due` appears), whose contract is the §10 rule 4 move —
extract/split first, re-lock the baseline at the improved number, move the row to
Repaid. One new class in an existing skill; no new mandate.

### B4 — Doctrine growth is unratcheted: the suite measures its subjects' god-files while becoming a god-doctrine

PROTOCOL.md is 472 lines / 37 KB and monotonic — every earned rule is permanent, each
release adds more, and §7 proportion + Discipline 7 subtraction apply to *subjects*,
never to the suite. Every session pays the full context tax (`chief-engineer` Phase 0
reads PROTOCOL entire; total skill surface ~2,500 lines + 37 KB protocol). The ratchet
rule's own logic applies: no single rule was wrong; only accumulation is visible, and
nothing watches it.

**Resolution:** ratchet the doctrine like the code. (1) Measure it: extend
`structure-report.py` (or a 30-line `doctrine-budget.py`) to report bytes-loaded-per-
session (PROTOCOL.md + all SKILL.md frontmatter + chief-engineer body) and freeze the
current number in the baseline with a `repay_at`. (2) A subtraction pass per release:
any PROTOCOL rule fully absorbed by a tool (e.g., §5's prose now that
`registry-check.py` reconciles; §9.4's marker rules now that `verdict-lint` enforces
them) compresses to *rule + pointer + provenance line*, cutting exposition. Target:
PROTOCOL under 30 KB without losing a single normative statement — deletion of
explanation, never of law.

### B5 — Self-referential closure: the suite's recent evidence is itself

Consequence of B2, worth naming separately because it is the failure mode of every
process-improvement system: 5 consecutive releases where the subject of the audit is
the auditor. Coherence keeps improving; external yield is unmeasured since
LIVE_RUN_004. The resolution is B2's cadence — this entry exists so the pattern is on
the ledger and a future audit checks whether it resumed.

---

## Part C — Gaps (missing mandates, held to the evidence bar)

| Gap | Evidence today | Disposition |
|---|---|---|
| Observability design | D001, no run finding | Close as fold into `ship-gate` (F5) |
| Dependency intake | D002, no run finding | Close as `arch-design` checklist (F5) |
| Concurrency / atomicity | **`runs/patches/03` — run-earned** | Open D005, decide (F5) |
| CI/CD pipeline ownership | Named "no owning skill" in chief-engineer routing | Leave explicit; a checklist row in `ship-gate` at most — do **not** add a mandate without a run finding |
| Secrets/config management | None | Watch; `threat-model` already triggers on "secrets" |
| Cost (cloud spend) budget | None | Watch; `perf-optimize`'s budget table can carry a cost dimension when a run demands it |

The discipline here is the suite's own: gaps without evidence get a watch entry, not a
skill. The table exists so the next audit doesn't re-derive it.

---

## Execution order

| Phase | Tasks | Why this order | Release |
|---|---|---|---|
| **0 — Rewire** (hours) | F1 descriptions, F2 hook interpreter | Both are silent failures in the installed plugin *right now*; everything else is worthless if triggering and enforcement don't fire | 1.19.0 |
| **1 — Repay & watch** (a day) | F3 `_encoding.py` repayment, F4 `repay_at` mechanism | F3 is the demonstration that F4 is needed; landing them together is the ratchet closing its own gap | 1.19.0 |
| **2 — Decide & delimit** (a day) | F5 ledger decisions (D001/D002/D005), B1 knowledge-tier paragraph, B3 `Repay` class, B4 doctrine budget + first subtraction pass | Doctrine edits; each needs the director once, batched | 1.20.0 |
| **3 — Prove it still works on the world** | B2/B5: LIVE_RUN_005 against an external subject, compute skill-yield | The only phase that tests whether any of the above mattered | 1.20.x |

**Phase 3 — executed, 1.20.1.** `runs/LIVE_RUN_005.md` ran the suite against a director-supplied
external subject (an F1 telemetry app, independent of this suite, already touched once informally
by a copy of it). Found one **(proven)** defect — a debt-ratchet regression the subject's own
baseline had silently missed for one commit — that independently confirms F4 on a second codebase,
plus a clean `threat-model` pass on a Discord-OAuth trust boundary (a new boundary shape for the
suite). Skill-yield computed for the first time (MAP.md). B2's resolution landed as PROTOCOL §12
(the run-cadence obligation + field-report admissibility, formalized rather than left as prose in
this file). B5's self-reference check is the new §12 clause: a future audit states the count if
skill-body-changing releases resume shipping with zero `LIVE_RUN_*` entries between them.

Every phase closes with: full floor green, fresh-eyes `scrutinize` on the diff
(§8.1(a) — the agent, not the marker), CHANGELOG entry, and for Phases 0–1 a version
bump in `.claude-plugin/plugin.json`.

`AUDIT: prescribed(4 phases, top: F1 — nine skills surface without trigger text in a live session)`
