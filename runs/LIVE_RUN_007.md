# LIVE_RUN_007 — the improvement-backlog workflow, run live: hunt → file → real GitHub issues

PROTOCOL: 1.22.0 — vintage declaration (§11, rule vintage).

`SUBJECT: yt-zero-touch @ 5ad98ad11e85b4ce8bc255396050fb570087c864` (clean working tree at hunt
time; the three issues below were filed after reading this revision, and touch no code in it).

**Target:** `D:\YT DLP\yt-zero-touch-clean` (`github.com/thanaponai01-collab/yt-zero-touch`) — a
real, actively-used project, not owned by this suite. A single-user Windows zero-touch downloader:
Tk GUI (`app.py`) + CLI file-watcher (`watcher.py`) sharing a batch/retry layer (`orchestrator.py`),
a URL resolver (`resolver.py`), a transcode/merge decision module (`transcode_plan.py`), a format
policy (`format_policy.py`), and a downloader skill (`ytdlp_skill.py`) — 3,581 lines across the
seven modules. Its own `CONTEXT.md`: *"A zero-touch downloader for a single video editor on a
single Windows machine."* Its `git log` already carries nine issues (#1–#10), all closed
2026-08-13 via a prior, less formal improvement-hunt pass — real commits, real ADRs
(`docs/adr/0001`–`0004`) — so this run lands on a codebase that has already absorbed one full round
of issue-driven hardening on its highest-stakes subsystem (the merge/transcode pipeline).

**Why this target:** discharges §12 for the 1.22.0 release, which shipped a skill-body change
(`improvement-backlog`) with no live run behind it yet — `LIVE_RUN_006` was the field report that
motivated the skill, explicitly carrying no verdict lines and no run against an external subject
(*"no skill lifecycle executed against an external checkout here, so it carries no verdict
lines"*). This is the first live exercise of `improvement-backlog`'s actual pipeline — hunt → file
→ a real tracker — chosen because `yt-zero-touch` already speaks the tracker's vocabulary (nine
issues, closed with commit references) and its owner is the same director who described the
workflow LIVE_RUN_006 reports on.

**Scoping, made explicit before the run started** (director's own choices, asked up front because
they affect a real external repo): file real issues via `gh issue create`, not a dry-run list;
filing only, no drain/implementation in this run; broad-sweep hunt (architecture, correctness, and
UX/cohesion lenses together), not a single-lens pass.

**Headline:** the mechanical dead-code/layer sweep came back clean (0 dead, 0 unused, no layer
declaration to check breaches against). Three real, provable findings survived the hunt and were
filed as `yt-zero-touch#12`, `#13`, `#14` — all dormant or minor (an unreachable `IndexError`
landmine, a UX busy-state asymmetry between two buttons, and a failure-swallowing shutdown path) —
consistent with a codebase whose highest-stakes logic has already been through nine rounds of
issue-driven review. One additional item was found and deliberately **not** filed: a paywall-bypass
code path that improvement-backlog's contract has no rule for (§ below) — flagged directly to the
director instead.

---

## Ground (chief-engineer Phase 1)

Census: `CONTEXT.md` + `docs/adr/0001`–`0004` + `docs/agents/{domain,issue-tracker}.md` exist;
no `ARCHITECTURE.md`, no `PROBLEM_BRIEF.md`, no `DEBT_LEDGER.md`. Inferred state: **live system,
maintenance mode** — a working, shipped tool with nine closed issues and session logs (`logs.md`)
going back to 2026-05-07. Issue tracker confirmed live and real: `gh issue list --repo
thanaponai01-collab/yt-zero-touch --state all` returns #1–#10, all `CLOSED`, plus a pre-existing
open `#11` unrelated to this run. `gh auth status` confirmed an authenticated account
(`thanaponai01-collab`) with `repo` scope before any issue was filed.

Executability census: no attempt made to run the Tk GUI or drive a real download in this
environment (out of scope for a hunt-and-file run) — findings below are **(proven)** by reading,
not by execution; nothing here required runtime evidence to prove.

## Classification (chief-engineer Phase 2)

*"Find improvements in every area... output to issue on repo... implement one by one"* is exactly
the row `improvement-backlog`'s own routing table names: several lenses at once, findings that must
outlive the session → the owning audits hunt, `improvement-backlog` carries the merged result out.
`latent-audit` supplied the mechanical floor and the dead-code/layer-breach/dormant-bug lens; the
architecture and UX lenses were read directly against `latent-audit`'s rule 5 (*"dormant bugs ride
the sweep... recorded with file:line and an evidence tag"*) since no felt complaint existed to route
through `symptom-audit`, and no `ARCHITECTURE.md` declaration existed for a layer check.

---

## latent-audit — mechanical floor (rule 1: the graph runs first, always)

```
$ python3 tools/graph-audit.py "D:/YT DLP/yt-zero-touch-clean" --entry app.py --entry watcher.py

GRAPH — 12 modules, 23 import edges traced.
LAYERS — not checked: no --layers file declared. This is a gap, not a clean result.
DEAD MODULES (suspected sweep) — none found.
UNUSED DEFS (suspected sweep) — none found.
LATENT: findings(dead: 0, unused: 0, layer-breaches: UNMEASURED(no --layers declared))
```

A clean sweep is a finding too (latent-audit rule 5): nothing statically dead, nothing statically
unused, across all seven modules and both entry points. No layer order is declared anywhere in the
subject (only prose in `CONTEXT.md`), so the breach question is honestly unmeasured rather than
claimed clean.

## Findings that rode the sweep (rule 5), checked and filed

Full source read (all seven modules, 3,581 lines) against `latent-audit` rule 5's dormant-bug lens
and a direct architecture/UX read, cross-checked against the nine already-closed issues to avoid
re-filing settled ground. Three survived rules 1–2 of `improvement-backlog`'s contract (a real
defect, an observable acceptance check, a `file:line` location) and were filed:

**F1 — `download_with_retry` indexes `retry_delays` by `attempt` with no length guard against
`retry_max`** — (proven) reachable, (suspected) ever triggered. `orchestrator.py:272,290-291`:
the loop runs `retry_max` attempts before the last one, each indexing
`retry_delays[attempt - 1]`. Every current call site pairs the matched defaults
(`_DEFAULT_RETRY_MAX = 3` / `_DEFAULT_RETRY_DELAYS = (5, 15, 30)`, a pairing the code's own comment
says is deliberate but nothing enforces) — so this is a landmine for the first future caller that
decouples them, not a live bug today. Filed as
[`yt-zero-touch#12`](https://github.com/thanaponai01-collab/yt-zero-touch/issues/12).

**F2 — "Update tools" gives no busy-state feedback, unlike the Download button** — (proven).
`app.py:651-652` / `733-737` disable and relabel `dl_btn` for the duration of a run; `_update_ytdlp`
(`app.py:585-606`) has the identical background-thread-plus-guard-flag shape but never touches the
button's own state. A click during `update_tools`'s up-to-180s pip reinstall looks like nothing
happened. Filed as
[`yt-zero-touch#13`](https://github.com/thanaponai01-collab/yt-zero-touch/issues/13).

**F3 — the Ctrl+C drain in `watcher.py` swallows every in-flight failure, including a genuine
one** — (proven). `watcher.py:255-267`: the `KeyboardInterrupt` handler's
`except Exception: pass` around `future.result(timeout=600)` discards a real download failure, a
600s timeout, or any worker exception with no counting and no log line — unlike the steady-state
path, `_harvest_completed` (`watcher.py:104-140`), which classifies and counts the identical
outcome shape. The printed "Session stats" line right after under-reports any URL still in flight
at shutdown. Filed as
[`yt-zero-touch#14`](https://github.com/thanaponai01-collab/yt-zero-touch/issues/14).

Each issue body carries the finding's evidence tag, its `file:line`, and a pre-written acceptance
check per `improvement-backlog` rule 2 — filed intact per rule 3 (the tag crosses unchanged: all
three are titled as the defect they are, none inflate a **(suspected)** into a fact).

## Found, not filed: a boundary `improvement-backlog`'s contract does not name

**`resolver.py:303-349`, `_outseta_js`** injects a fabricated subscription object
(`HasGoldPlan/HasMotorsportsPlan/HasPlatinumPlan/.../HasAnyPaidPlan: true`) into the page before
interception, spoofing a third-party streaming service's (Outseta-gated) client-side entitlement
check regardless of the actual account's plan. This is real, and it rides the sweep exactly the way
`latent-audit` rule 5 describes — but it is not an engineering defect with an acceptance check; it
is a policy/legal decision about paywall circumvention that only the director can make, and
`improvement-backlog`'s contract (rule 2, "incomplete in, nothing out") has no clause for a finding
that is complete but *not homework the tracker should own*. Filing it as a normal issue would dress
a policy question in the tracker's engineering vocabulary; not mentioning it at all would drop a
real finding on the floor. Flagged directly to the director in this session's own chat, not filed —
logged here as the improvised call, per `improvement-backlog`'s own instruction *"log that... do
not absorb the decision silently."*

---

## Director summary (Law 4)

Ran the new `improvement-backlog` workflow live, for the first time, against a real project with a
real GitHub tracker: swept `yt-zero-touch` for dead code, dormant bugs, and UX gaps; the codebase's
core (nine issues deep already) came back clean of anything new and serious, three small dormant
issues got filed (`#12`–`#14`, ready for you to work whenever), and one thing that isn't really an
engineering bug — a real paywall-bypass in the F1 stream resolver — got flagged to you directly
instead of dumped in the tracker, because filing it there would have made a policy call for you.

```
ASKED: "i want to live run for this plugin new system" (→ clarified: file real issues, filing
       only / no drain, broad-sweep hunt — director's own choices, asked before touching the
       external repo)
DID:   Ran latent-audit's mechanical floor (graph-audit.py) plus a full-source dormant-bug and
       architecture/UX read against yt-zero-touch-clean (3,581 lines, 7 modules); filed three
       surviving findings as real GitHub issues via gh issue create; held back a fourth as
       out-of-mandate and flagged it directly instead.
SO:    You have three concrete, acceptance-checked issues (#12-#14) ready to pick up whenever, a
       confirmed-clean dead-code/layer sweep, and a direct flag on the Outseta spoof in
       resolver.py that needs your call, not an issue.
COST:  No code in yt-zero-touch was changed — filing only, as scoped. The retry_delays landmine
       (#12) is unreachable today; the other two are small.
```

`LATENT: clean(7 modules traced) | findings(dead: 0, unused: 0, layer-breaches: UNMEASURED(no
--layers declared))`
`BACKLOG: filed(3, top: #14 Ctrl+C drain swallows failures) | blocked(none)`

---

## Skill-yield (PROTOCOL §12)

**Pre-run knowledge:** nothing — `improvement-backlog` had never been run against a real tracker;
`LIVE_RUN_006` (the report that motivated the skill) explicitly executed no skill lifecycle and
carried no verdict lines. Zero evidence existed that the skill's pipeline — *gather → check against
rules 1–2 → `gh issue create` → state the merge rule* — actually executes as written against a
real `gh` auth session and a real repo, as opposed to reading correctly as prose.

**What external use taught that introspection could not:**

1. **The pipeline runs.** `gh issue create --repo ... --title ... --label ... --body ...` executed
   three times against a live, authenticated repo and returned real issue numbers (#12, #13, #14)
   — the mechanical half of the skill's only previously-unverified claim.
2. **A real boundary gap, found by hitting it, not by reading the contract.** The Outseta finding
   (above) is a finding `improvement-backlog` rule 2 cannot classify: not incomplete (it has
   evidence, file:line, and is unambiguously true), but wrong to file as engineering homework
   because the fix isn't a fix, it's a policy decision. No amount of re-reading the skill's five
   rules surfaces this — only a real subject that happened to contain a paywall bypass could, and
   `yt-zero-touch` did. This is the same shape of gap `LIVE_RUN_006` names for the *suite's* own
   discovery process: a between-session, real-artifact gap no self-audit could see coming, because
   self-audits don't contain paywall bypasses to trip over.
3. **The tag-crossing rule (rule 3) held under real pressure.** All three filed issues state their
   evidence tags in the issue body verbatim ((proven)/(suspected)) rather than flattening them into
   bare assertions — worth checking explicitly because a GitHub issue title is exactly the
   "read alone" context rule 3 warns a hedge is most likely to be lost in, and titles here were
   written defect-first, tag deferred to the body, matching the worked pattern.

**Open watch, honestly held:** whether `improvement-backlog` needs an explicit rule for the
Outseta-shaped case (a complete, real finding that is not tracker-shaped homework) is unresolved —
this run improvised the call and logged it rather than filing or dropping the finding, per the
skill's own instruction, but the contract itself is unchanged. Whether that gap is worth a sixth
rule, a boundary note, or is rare enough to leave as director-judgment-on-the-day is a decision for
whoever next touches `improvement-backlog`'s contract, not this run.

---

## run-trace + verdict-lint on this transcript

```
$ python3 tools/run-trace.py runs/LIVE_RUN_007.md
  Request type (inferred by verdict-presence): Sweep for latent defects with no symptom
  Required stages: ✅ LATENT   ✅ SUBJECT pin
TRACE: complete

$ python3 tools/verdict-lint.py runs/LIVE_RUN_007.md
verdict-lint: clean — 3 verdict noun(s) present (BACKLOG, LATENT, TRACE), all well-formed.
```

(First pass of `run-trace.py` flagged `incomplete(latent: missing SUBJECT)` — this report had no
`SUBJECT: <name> @ <sha>` pin. Added per PROTOCOL §1 and re-run above; both tools now report clean.
Left in as evidence the mechanical checks were actually run against this file, not narrated.)
