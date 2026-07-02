# LIVE_RUN_004 — TickIt (the intended LIVE_RUN_001 target, finally reachable)

**Target:** `E:\Me\5.Claude\TimeTracker` — the **TickIt** app (`package.json` name: `tickit`).
Next.js 14 App Router + Server Actions, Supabase Postgres with **Row-Level Security declared as
the security boundary** (its own `CLAUDE.md`: *"The DB is the security boundary — Postgres RLS
enforces all permissions; the app is a thin client over it."*). ~135 TS/TSX source files, 8 vitest
suites, 9 SQL migrations.

**Why this target:** LIVE_RUN_001 records verbatim that its intended target was *"`tickit`,
private, unreachable from the run environment"* and used a Flask stand-in instead. This repo is
that `tickit`, now reachable — running it closes a loop the suite's own history left open. It also
fills an evidence hole: it is the first live run against a **declared trust boundary** (real auth +
RLS), so `threat-model` binds against a real subject for the first time.

**Suite version under test:** v1.9.1.

**Mode:** review-led, with `threat-model` (trust boundary present), `structure-gate`, and
`data-tier` binding. Fixes for the top finding are delivered inline per Law 5 (diagnosis ships with
the artifact) but **not committed to the TickIt repo** — TickIt is a live, deployed project and
this run has no mandate to push to it; the corrected code is delivered here as the artifact.

**Headline:** The suite routed correctly and its skills, followed as contracts, **derived and
caught a real broken-access-control defect** on the public API's `project` scope — a proven-by-
trace BOLA where any authenticated token reads any project's full time ledger. That is a suite
success. The run also surfaced **one proven gap in the suite's own tooling**: `run-trace.py` has no
completeness profile for a security-audit request, so a pure `threat-model` run cannot be
completeness-checked (it is either silently declared "complete" with zero checking, or
misclassified as a `review` run and falsely flagged incomplete). Both behaviors were reproduced by
executing the tool.

---

## Proven baseline (decay rule, PROTOCOL §1)

Ran TickIt's own test suite before judging anything:

```
$ npx vitest run
 Test Files  8 passed (8)
      Tests  71 passed (71)
```

71/71 pass **(proven)**. This is the trustworthy floor the review builds on. Note the ceiling this
establishes for the rest of the run: TickIt's security-relevant behavior lives in Postgres RLS +
Supabase, and **no live Supabase instance or credentials are reachable from this environment**, so
security findings below cap at **(trace-only)** — the reasoning chains are complete, but no exploit
was fired against a running database. This cap is stated, not hidden (threat-model contract 4).

---

## Director summary (Law 4)

TickIt's public export API has a **hole in one of its four access modes**. Three of the four modes
are correctly gated (your own data needs no gate; "everyone's data" and "another member's data"
both require an admin token). The fourth — *"give me this whole project's data"* — has **no gate at
all**: anyone holding any valid API token can read the complete time ledger of any project in the
company simply by supplying that project's id, which is itself readable by any logged-in user. This
exposes who worked on what, when, and for how long, across every team — a confidentiality breach,
not a style issue. The fix is small and shown below. Everything else checked came back healthy or
correctly gated.

`REVIEW: shippable-with-findings(project-scope BOLA on /api/v1/entries)`
`THREAT: findings(top: object-level authorization missing on scope=project)`
`STRUCTURE: findings(top: duplication, count: 20)`
`DATATIER: clean(2 ledger queries bounded by project size, no N+1)`

---

## What each skill bound to, and what it found

Per chief-engineer Phase 1 census: **no PROTOCOL-registry ledgers exist in the TickIt repo**
(no PROBLEM_BRIEF, ARCHITECTURE, THREAT_MODEL, etc.) — TickIt was built without the suite. Its own
`CLAUDE.md` is a project map, not a suite ledger. Inferred lifecycle state: **live system**
(deployed to Vercel per git log), so the maintenance/review lens governs, and `threat-model` is
mandatory because a trust boundary exists (chief-engineer Phase 2 + Phase 3 parallel-gates rule).

### senior-review — bound

**Invariants derived** (no checklist; derived from what a shared time-tracker *is*):

1. A user's time entries are visible only to that user, members of the project the work belongs to,
   and admins.
2. Privilege (admin vs member) is decided by the server, never asserted by the client.
3. An API token authenticates exactly one user and carries no authority its owner lacks.
4. The documented security model ("RLS enforces all permissions") matches the code.

**Finding F1 — `project` export scope has no object-level authorization (violates invariant 1)
— (trace-only).**

Root cause — *authorization has no single owner*: read-scoping is split between permissive RLS
(`time_select` = `auth.role() = 'authenticated'`, i.e. **every authenticated user may read every
time-entry row** — `supabase/schema.sql:224`) and ad-hoc per-query `user_id` filters in application
code. The `project` scope fell through the crack between the two.

Trace (complete chain, no execution — no live DB):
- `src/app/api/v1/entries/route.ts:53` `GET` resolves the bearer token to `{userId, isAdmin}`.
- `route.ts:82` the `member`/`all` scopes are gated: `if (!isAdmin) return err(..., 403)`.
- `route.ts:93` the `project` scope has **no gate** — it calls
  `getProjectLedger(scope.projectId, svc)` directly.
- `svc` is `createServiceClient()` (`src/lib/supabase/admin.ts:10`), which **bypasses RLS by
  design** ("RLS is bypassed by the service role").
- `getProjectLedger` (`src/lib/queries/time.ts:112`) applies **no `user_id` and no membership
  filter** — it returns every entry for every task/subtask in the project.
- Project ids are enumerable: `projects_select` RLS is `auth.role() = 'authenticated'`
  (`schema.sql:191`), so any logged-in user can list all project ids.

Result: any holder of any valid, non-admin API token can read the full time ledger of any project
by calling `GET /api/v1/entries?scope=project&projectId=<any id>`. The same hole exists on the
Server Action path (`exportEntries`, `src/lib/actions/time.ts:129`): it uses the RLS-bound client,
but `time_select` RLS is permissive, so the read is not scoped there either.

**Why (trace-only) not (proven):** promoting this to (proven) needs one executed request against a
live TickIt+Supabase with two ordinary users and one project. That environment is not reachable
here. The single command that would promote it is recorded in the fix section.

**F2 — documentation contradicts code (drift; precedence code > docs — chief-engineer Phase 1).**
`CLAUDE.md` states RLS "enforces all permissions"; in fact RLS on `time_entries` and `projects` is
read-open to all authenticated users and the real scoping is application-side. This is the *reason*
F1 was easy to introduce: a maintainer trusting the doc would assume the DB already scopes reads.
**(trace-only).**

### threat-model — bound (first live use against a real trust boundary)

- **Assets:** every employee's time-tracking history (who worked on what, when) — a
  confidentiality + privacy asset; and admin privilege.
- **Boundary:** network → app at `/api/v1/entries`, authenticated by API token. What the app
  believes without verifying on the `project` scope: *"the caller is entitled to this project."* It
  is not verified. **Trust-placement defect** (contract 2): object-level authorization is absent,
  not merely weak — classic IDOR/BOLA (Phase 3 "object access" category).
- **Clean boundaries (findings too, Phase 4):** the `me` scope (self-only via explicit `user_id`
  filter) and the `member`/`all` scopes (admin-gated) survive the adversarial walk. Token handling
  is sound: tokens are stored as SHA-256 hashes, never plaintext (`src/lib/api-token.ts:12`),
  bearer parsing is strict (`bearerFrom` regex), and expiry/revocation are checked
  (`src/lib/api-auth.ts:25-26`). Role is read server-side from `profiles`, not from the token —
  invariant 2 holds.
- **Abuse-case test spec (handed to correctness-gate, u. to run against a live DB):**
  *Given* user A (non-admin) with a token and a project P that A is not a member of, *when* A calls
  `GET /api/v1/entries?scope=project&projectId=P`, *then* the response must be `403`, not P's
  entries. This test **cannot be executed here** (no live DB) — it is recorded as the promotion
  command, and the finding stays (trace-only) until the gate runs it (threat-model contract 4).

`THREAT: findings(top: object-level authorization missing on scope=project)`

### structure-gate — bound (mechanical, executed)

```
$ python tools/structure-report.py "…/TimeTracker/src"
STRUCTURE: findings(top: duplication, count: 20) | review-needed
```

All 20 flags are 6-line duplicated blocks across `loading.tsx` skeleton files — near-identical
route-level loading skeletons. **Wisdom call (deferred to review, per structure-gate's own
handoff): not a defect.** Loading skeletons are cheap, independently-evolving view boilerplate;
DRY-ing them behind a shared component trades a trivial duplication for a coupling that would make
per-route skeleton tuning harder. Chesterton's Fence / Law 3 (violation ≠ deviation): flagged,
examined, dismissed as a deviation, not promoted to a finding. **(proven)** the tool ran;
**(trace-only)** the wisdom call.

Note: `structure-report.py` deep-analyzes Python only; on this TS/TSX codebase it emitted
length+duplication signals but `0 functions` analyzed — a known limitation stated in its own output,
logged below as a (trace-only) suite observation, not a TickIt finding.

### data-tier — bound

The two ledger fetch paths (`getProjectLedger`, `getTaskLedger`, `time.ts:85,112`) each issue
**two** queries — one to collect task/subtask ids, one `time_entries … .in.(ids)` — not one query
per task. Cost class is O(rows-in-project), bounded by project size, **no N+1**. `getRecentTasks`
scans a bounded `limit*4` slice and dedupes in app code (documented trade-off, `time.ts:176`).
**(trace-only)** — read the query construction; no `EXPLAIN` run (no live DB).

`DATATIER: clean(2 ledger queries bounded by project size, no N+1)`

### Skills that correctly returned not-applicable

`problem-framing` (no brief to reconstruct was requested), `arch-design`, `build-discipline`,
`correctness-gate` (no new code was gated — the fix is delivered trace-only, not built here),
`debug-protocol` (no observed failure; F1 is a design gap, not a repro'd bug), `perf-optimize`,
`ship-gate`, `data-evolution`, `evolve-maintain`, `wire-check`, `scrutinize` (no delta),
`symptom-audit` (no felt complaint), `meta-skills` (always-on discipline). Forcing verdicts where
there is no subject would violate Law 3 — the empty returns are a pass, not a skip (same principle
as LIVE_RUN_003).

---

## The fix for F1 (Law 5 — delivered, not committed)

Add the missing object-level gate on the `project` scope, mirroring the existing `member`/`all`
gate. The project-membership source of truth already exists (`project_members` table,
`migration_v2.sql:67`). Minimal correct fix in `route.ts` and `exportEntries`:

```ts
// route.ts, inside the scope.kind === "project" branch, BEFORE fetching:
} else if (scope.kind === "project") {
  if (!isAdmin) {
    const { data: member } = await svc
      .from("project_members")
      .select("user_id")
      .eq("project_id", scope.projectId)
      .eq("user_id", userId)
      .maybeSingle();
    if (!member) return err("Not a member of this project", 403);
  }
  const all = await getProjectLedger(scope.projectId, svc);
  ...
```

The same membership check belongs in `exportEntries` (`time.ts:129`) for the Server Action path.
The deeper root-cause fix (route to `arch-design` as a decision, threat-model Phase 5) is to give
read-authorization a **single owner** — either tighten RLS so the DB actually is the boundary the
doc claims, or make every read path go through one authorization helper — rather than leaving it
split between permissive RLS and per-query filters.

**Promotion command (turns F1 (trace-only) → (proven)):** against a live TickIt with users A
(non-admin, token `tk_…`) and B, and project P owned by B with A not a member:
`curl -H "Authorization: Bearer tk_…" ".../api/v1/entries?scope=project&projectId=P"` — today
returns P's entries (bug); after the fix returns `403`.

---

## Suite self-observations from this run (the gap ledger drives these — see handoff)

1. **(proven) — `run-trace.py` has no completeness profile for a security-audit request.**
   A `threat-model` run is the one routed-skill run whose verdict the completeness checker cannot
   check. Reproduced by executing the tool three ways:

   ```
   # THREAT verdict + neutral threat phrasing:
   $ printf 'Can this be abused? Threat model the auth boundary.\n\nTHREAT: findings(top: BOLA)\n' | python tools/run-trace.py
   TRACE: complete(unclassified: 1 verdict(s) present, no completeness profile to check against)   # exit 0

   # THREAT verdict only:
   $ printf 'THREAT: findings(top: BOLA)\n' | python tools/run-trace.py
   TRACE: complete(unclassified: ...)                                                               # exit 0

   # THREAT verdict + prose containing "review"/"secure"/"audit":
   $ printf 'is this secure, review the auth.\n\nTHREAT: findings(top: BOLA)\n' | python tools/run-trace.py
   TRACE: incomplete(review: missing REVIEW) | review-needed                                        # exit 1
   ```

   Two wrong outcomes, no correct one: either **false green** ("complete" with zero checking — the
   exact "I don't know if it ran" feeling the tool exists to kill, but for the security stage), or
   **false red** (misclassified as `review`, demanding a REVIEW verdict a pure threat run correctly
   never emits). Root cause: `THREAT` is absent from `NOUN_TO_TYPE`, `TYPE_PRIORITY`, `PHRASE_HINTS`
   and `PROFILES` in `tools/run-trace.py`, even though `threat-model` owns the `THREAT` noun in
   PROTOCOL §5, appears in the §4 handoff chain, and is mandatory before ship when a trust boundary
   exists. `verdict-lint.py` *does* know `THREAT` (`tools/verdict-lint.py:38`), so the gap is
   isolated to `run-trace.py`. **This gap was earned by this run:** the run needed a THREAT verdict
   for the TickIt BOLA and the completeness checker could not account for it.
   → Recommended action: **check** (extend the existing invoker). See PROPOSED EDITS.

2. **(trace-only) — doc/code drift detection is prose-only.** chief-engineer Phase 1's drift rule
   ("if artifacts contradict the code … reported first") caught F2 correctly *because a model read
   both*, but nothing mechanical enforces it. Generic doc-vs-code contradiction is a semantic
   judgment, not obviously mechanizable, so this is **logged for a future run**, not acted on
   (per the task's rule: no action on non-proven gaps).

3. **(trace-only) — `structure-report.py` deep-analyzes Python only.** On this 135-file TS/TSX
   codebase it produced only length+duplication signals (`0 functions` analyzed), so its
   complexity/cycle/god-file checks did not run at all against the actual system. Real limitation,
   but converting it (a TS/TSX AST analyzer) is a large build, not a small check — **logged**, not
   acted on this run.

---

## run-trace + verdict-lint on this transcript

(Output pasted verbatim in the run summary below; this run classifies as a `review` run — REVIEW
present, THREAT/STRUCTURE/DATATIER noted — and traces **complete**. The `run-trace` threat gap does
*not* bite this transcript precisely because REVIEW is present alongside THREAT; it bites only when
THREAT is the sole verdict, which is why observation 1 was proven with targeted minimal transcripts
rather than this file's own trace.)
