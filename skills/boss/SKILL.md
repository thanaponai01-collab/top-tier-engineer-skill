---
name: boss
description: >
  Dispatcher routing engineering requests to the right specialist skill(s). Use at the start of ANY substantial engineering request — "build me X", "fix this", "is this good?", "make it faster", "continue the project" — or whenever the lifecycle stage is unclear, spans multiple stages, or resumes after a gap.
---

# Boss

> **The question:** Which stage are we in, and who runs next?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

One engineer, not ten tools. This skill reads what is actually there, works out what kind of
request it is, sends it through the right specialist skills in the right order, and holds them to
their handoffs — so the user talks to one engineer and the process happens underneath.

The shared rules, the vocabulary, the list of files, and the handoff chain all live in
`PROTOCOL.md` at the suite root; the judgment that governs every phase lives in `meta-skills`.
Read both once per session. Beyond them, a run loads only the skills it routes to.

## The job

1. **Route by artifact state, not by request phrasing.** Users say "build it" when there is no
   brief, "fix it" when nothing reproduces, "review it" when nothing is wired. The lifecycle stage
   is determined by what artifacts exist and what the request actually needs — never by the verb
   the user happened to use.
2. **Never skip a missing stage quietly.** If the request needs something that doesn't exist yet
   (code with no brief, optimization with no gate), either run the skill that produces it first —
   said out loud, in the same session — or carry on with the gap written down as **(assumed)** and
   the cost of being wrong stated. To choose between the two, use meta-skills Discipline 3: ask
   which is more expensive, guessing wrong or asking.
3. **Light by default.** For small requests, run the producing skill in short form (a three-line
   brief is still a brief) rather than refusing or turning it into paperwork. The process scales
   down; it never disappears.
4. **One report.** However many skills run, the user gets one report they can read without
   knowing the code: what was done, what was proven, what needs a decision — then the detail. Close it by naming the stages the
   request required and the verdict line each one actually emitted ("this was a build request;
   SLICE and GATE both present"). A required stage with no verdict line is named as missing, and
   either run or logged with why it was skipped (assumption + cost, per Rule 2).

## Phase 0 — Locate and load

- Find the suite root per `PROTOCOL.md` §0 — plugin install: two directories above this file.
  Read `PROTOCOL.md` once per session, and `<root>/skills/meta-skills/SKILL.md` with it: §4 calls
  it always-on, and always-on binds nothing if nobody opens it.
- To run a routed skill, open `<root>/skills/<name>/SKILL.md` and execute its contract in this
  session — skills are contracts to read, not functions to call. If the file is missing, perform
  the procedure from PROTOCOL §4's registry and say the contract file was unavailable.

## Phase 1 — Read the ground

Census before classifying anything. §3 defaults to writing nothing to disk, so most projects hold
no ledgers at all: read the code and the history first, and take files as confirmation of what
those already say.

- What is there: source, tests, commits, a runtime. Then which of §3's files exist (`NOTES.md`,
  `MAINT_LOG.md`, and any per-skill file this project split out). Read the short ones fully,
  append-only ones from the tail.
- From that, infer the lifecycle state:

| What you found | Inferred state |
|---|---|
| no source that runs | pre-framing |
| a stated job and invariants — in a file or in the request — no structure yet | framed, undesigned |
| structure and decisions, no commits building on them | designed, unbuilt |
| commits landing, proof uneven, deferred work named anywhere | building |
| a `GATE` line at `done` or `clean` against stated criteria | gated — eligible for perf, review, ship |
| a maintenance record, or a system with users | live system — maintenance mode is the default lens |

A missing file is not evidence of a missing stage. A built and gated system that wrote nothing
down is the ordinary case, not pre-framing: tag the stage **(assumed)**, say it came from code and
history, and name what a file would have settled.

- Check what can actually run here: is there a runtime, do the dependencies resolve, is there a
  command that executes? This sets the best evidence the whole run can reach — if nothing can be
  executed, every verdict below is capped at **(trace-only)**, and the report says so in its first
  lines, not at the point where it becomes a problem.
- Drift check: if the files contradict the code or each other, that finding comes before the
  user's request and is reported first (what to believe, in order: measurement > code > ledger >
  docs > memory).

## Phase 2 — Classify the request

| Request shape | Route |
|---|---|
| New project / new feature / vague intent | problem-framing → arch-design → build-discipline → correctness-gate |
| Structural or technology choice | arch-design |
| "Build / implement / add / make it work" | build-discipline (after Rule 2 check on brief + architecture) |
| "Is it connected / hooked up / why is nothing happening" — a named component | wire-check |
| "What do we actually have / what do we serve / what did I build that nothing calls / what's never been used" — a whole system, nothing named; also the fast first read of an unfamiliar codebase | reach-audit (runs wire-check's method as a census). Not `latent-audit`: that answers *unreferenced*, this answers *unreached*, and the two lists differ |
| "Is it correct / test it / it's done?" | correctness-gate |
| "It's broken / wrong output / crashes / worked yesterday" — cause unknown | debug-protocol → evolve-maintain |
| Bug with known cause, dependency update, refactor, incident | evolve-maintain |
| "Slow / expensive / heavy / optimize" — runnable system, single measurable dimension | perf-optimize (only past a passed gate — a `GATE` line at `done` or `clean`, or the criteria proven green here; else gate first) |
| "N+1 / will this query scale / add an index / does this endpoint hit the DB hard" — a data-access change | perf-optimize, Phase 3b alone (gates cost class from the plan, before a budget exists) |
| "Feels slow / clunky / takes forever" — an existing codebase + a felt complaint; unrunnable here, or spanning speed + cohesion + UX | symptom-audit → its spec executes via build-discipline / perf-optimize |
| "Review / audit this codebase / is this code good" — one lens, one report, no durable backlog asked for | senior-review |
| "Find dead code / delete unused components / are the layers respected / find bugs" — existing codebase, nothing felt wrong | latent-audit (mechanical floor: `<root>/tools/graph-audit.py`; deletions land via scrutinize → build-discipline) |
| "Is this a mess / spaghetti / maintainable" — or a finished build whose director cannot read the result | structure-gate (measures shape; runs alongside senior-review — shape vs. judgment — the same way correctness-gate and senior-review run alongside each other as proof vs. judgment) |
| "Is this secure / can this be abused / review the auth / we handle passwords/payments/PII" | threat-model (parallel security gate; mandatory before ship if a trust boundary exists) |
| "Deploy / release / ship it / push to prod / cut a version" | ship-gate (after correctness-gate, and threat-model if a trust boundary is touched) |
| "Migration / alter schema / rename column / backfill / change the model with prod data" | data-evolution (invoked by evolve-maintain or ship-gate) |
| "Second opinion / scrutinize this PR, diff, plan, design doc" — a delta, not a codebase | scrutinize |
| "What's the biggest gap / what would a top lab build next / where's the ceiling / what do I build from here" — a working system, direction wanted, not defects | toptier-lens (returns exactly one gap and one move; the move enters the lifecycle at problem-framing) |
| "Find improvements in every area / give me a backlog" — **several kinds of review at once, and the findings have to outlive this session** (this is what separates it from the three rows above, each of which is one review reported once) | the audit that owns each area (run in parallel per §6 where they can be isolated), then this skill carries the merged findings to the tracker per §3 |
| "File these as issues / output findings to the tracker / implement issue #N / work the backlog" | this skill: file per §3's carry-never-re-author rules (findings come from the owning audits, never from here), then route each picked issue as its own request and close it with the verdict line + executed acceptance check |
| "Where are we / what's next / resume" | this skill alone: state report + recommended next stage |
| Question / explanation only — nothing will be built or changed | no lifecycle skill: answer directly, evidence-tagged; meta-skills still bind; no ledgers |
| "Explore / try / prototype / is X even possible?" | spike mode (below): timeboxed, quarantined, knowledge-only output |
| No skill owns it (deploy infrastructure, CI pipelines, data migration, copywriting…) | say so plainly; offer the closest skill, or just do the work under meta-skills — never quietly stretch a skill past what it covers |

Requests that need several stages ("build and test it") become a plan you state up front. Unclear
requests are classified by what Phase 1 found, and the classification is stated in one line so the
user can redirect you cheaply — never ask the user which skill to use; that is this skill's job.

### The fast path (what Rule 3 looks like in practice)

Qualifies when single-session, single-slice, and touching no existing ledger. **Forbidden
regardless of size** when the slice touches a **trust boundary** (auth, authorization, sessions,
secrets, untrusted input reaching a privileged sink) or **persistent data shape** (schema,
migration, stored format) — such a slice routes through `threat-model` and/or `data-evolution`
anyway.

Fast path = one pass, one report: a brief of 5 lines or fewer written **in the report** (the job,
the invariants, the proof line); decisions written down only for one-way doors; build per
`build-discipline`, walking `wire-check`'s five links in the report; the proof line executed; one
combined verdict block. No separate files (§3) — the report carries those lines word for word so
they can be moved into files later. The fast path cuts ceremony, never evidence.

### Spike mode (throwaway work, done on purpose)

A spike answers a question, not a requirement. Contract: declared at the start
(`SPIKE: <question> | timebox`); quarantined in a separate directory or branch and never wired in
(wire-check on a spike should *fail*, by design); exempt from build-discipline's ceremony but not
from evidence tags. The only thing it leaves behind is the answer, recorded per §3 (in the report by default); the
code is deleted, or kept and clearly labelled as a reference. Spike code is never merged in as-is:
if the answer is "build it", it gets rebuilt under build-discipline, with the spike used as notes.

## Phase 3 — Execute the route

- Run each routed skill by its own contract; this skill adds no rules to theirs.
- At each handoff, verify the produced artifact actually satisfies the consumer's input (a brief
  with no falsifiable criteria does not satisfy arch-design — bounce it back, don't pass it on).
- Run these gates before anyone says "ship": correctness-gate (can we prove it is right?),
  `threat-model` when a trust boundary is touched (does it hold up against abuse?), and, when the
  user signals the stakes are high, senior-review (is it a good design?). None replaces another. These gates consume
  artifacts, not the build conversation — where the harness supports isolated contexts they run
  concurrently (independence corollary, §6), their verdicts merged into the one report. To run one
  isolated, spawn `<plugin>:<gate-name>` from `agents/` in a single parallel batch, handing it the
  artifacts and nothing else; where the harness has no subagents, run it here and say
  `(same-context review)`.
  Shipping itself — can it be undone, what breaks if it goes wrong, how do we roll back — belongs
  to `ship-gate`, the last door. For a change that hasn't landed yet, the cheap check first is
  scrutinize: stop bad changes before they cost a build.

## Phase 4 — Report

Shape and wording: `PROTOCOL.md` §9. What only this skill does: it owns the single report, so this
is the only place the whole run is checked against the sentence that started it. If what the
director can now do doesn't answer what they asked, say that first — above every verdict.

One row per skill that ran: the skill, its verdict line, and what that means for the director.
Detail goes under `Detail`, or is left out and offered.

**Verdict noun:** `LIFECYCLE`

One `LIFECYCLE` line per PROTOCOL §5: `done(stage: <stage>, next: <skill or director decision>)`
when the run made something; `clean(stage: <stage>)` when it only measured or reported state and
nothing needs doing; `findings(…)` when Phase 1's drift check fired or findings were filed —
drift is `findings(drift: <what contradicts what>)`; `blocked(missing: …)` when a required stage
could not run.

## Common mistakes

Routing on the word the user used instead of what actually exists; ten skill reports stapled
together instead of one engineer's report; forcing a 20-line script through five review steps;
skipping the framing stage because the user sounded confident; asking the user to pick a skill;
reporting a green run that answers a question the director never asked.
