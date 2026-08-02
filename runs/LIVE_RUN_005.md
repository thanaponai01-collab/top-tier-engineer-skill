# LIVE_RUN_005 — SUBJECT_D (an F1 telemetry pit-wall app, gated by Discord OAuth)

PROTOCOL: 1.20.0 — vintage declaration (§11, rule vintage). Written under 1.20.0; §12 (the
run-cadence obligation this run exists to discharge) was added in the same session, after this
run's evidence made the case for it, so it is cited but did not yet exist when the run began.

> **Redacted for publication.** The subject appears as **SUBJECT_D**; the local path is removed.
> Every finding, command, and file:line reference below is the original, run against the real
> local path. This is a publication edit, not a rules edit.

**Target:** `<redacted local path>` — a personal F1 (motorsport) telemetry/knowledge-base project.
FastAPI + Starlette web server (`webapp.py`, 302 lines) fronting a data layer (`dashboard.py`,
1497 lines) that reads local Parquet telemetry, gated by Discord OAuth into three tiers
(owner/member/public). ~103 code files (97 Python), 725 functions, 21,461 code lines, 34 pytest
files. The subject **already carries its own copy of this suite's structure-gate artifacts**
(`DEBT_LEDGER.md`, `.structure-baseline.json`, both dated 2026-07-28) from a prior informal pass —
this is the first live run against a subject that had already been touched by an earlier,
un-logged use of the suite.

**Why this target:** IMPROVEMENT_PLAN.md B2/B5 named the exact failure this closes — five
consecutive releases (1.14→1.18) were introspection only, and PROTOCOL.md's own §12 (added this
session, see below) now requires a live external run per skill-body-changing minor release. The
director supplied this path directly when asked — this run does not name its own subject, because
a run choosing its own subject is exactly the self-referential-closure risk B5 names (no rule in
`chief-engineer` currently enforces this; it is a discipline this run follows, not a mechanism
it can point to, and is logged here as a gap: nothing stops a future run from picking its own
easy subject).

**Suite version under test:** 1.20.0.

`SUBJECT: SUBJECT_D @ a1abb179203ede7f18750108540d45a56f0f4018` (clean working tree at review time).

**Mode:** review-led. `structure-gate` bound (mechanical, executed against the subject's own
pre-existing baseline — a first for this suite: every prior LIVE_RUN wrote a fresh baseline from
nothing). `senior-review` and `threat-model` bound against `webapp.py`'s auth/tier boundary.
`correctness-gate` bound to the subject's own test suite as the proven floor. No fix was delivered
to the subject repo — SUBJECT_D is the director's own live project and this run has no mandate to
push to it; findings are reported, not committed.

**Headline:** The suite found one **(proven)** defect the subject's own copy of the suite had
already missed once: `static/race-panels.js` grew past its own accepted debt ceiling in the very
next commit after the baseline was frozen, and nothing caught it until this run re-ran the tool.
This is the exact failure IMPROVEMENT_PLAN.md's F4 named in the suite's own repo (`repayment
triggers are prose nobody watches`) — now independently confirmed on a second, unrelated codebase.
`threat-model` and `senior-review` both cleared the OAuth/tier boundary with no defect found — a
clean pass is itself evidence, not a non-result (LIVE_RUN_004 precedent).

---

## Proven baseline (decay rule, PROTOCOL §1)

Ran SUBJECT_D's own test suite before judging anything (via its checked-in `.venv`, since the
system Python lacked `itsdangerous`):

```
$ .venv/Scripts/python.exe -m pytest -q
.................................................................... (34 files, 1 skipped, 0 failed)
exit code: 0
```

All tests pass, one deliberate skip **(proven)**. This is the trustworthy floor the review builds
on.

---

## Director summary (Law 4)

Your F1 app's own copy of this suite already caught most of its structural debt a week ago and
froze it as known-and-accepted. One file — `static/race-panels.js` — grew past that accepted
ceiling in the very next commit (1365 → 1422 lines, adding the driver/team click-to-highlight
feature) and nothing told you, because nothing re-ran the check after that commit landed. That is
the whole finding: not that the file is unmanageable, but that your own debt ledger has been
silently wrong for a day. The Discord-gated access control (`webapp.py`) was checked end to end —
OAuth state, session handling, tier derivation, route gating — and came back clean; no fix is
needed there.

```
ASKED: "here the local path" (target for LIVE_RUN_005, IMPROVEMENT_PLAN.md Phase 3)
DID:   Ran this suite's review lens against SUBJECT_D end-to-end: proven test-suite floor,
       structure-gate re-run against its own pre-existing baseline, threat-model + senior-review
       on the Discord OAuth/tier boundary.
SO:    You know the one place your own accepted-debt ledger has silently drifted (race-panels.js),
       and you have an independently-checked clean bill of health on the login/access-tier code.
COST:  One file (`race-panels.js`) needs either a `--write-baseline` re-lock (if the growth is
       accepted) or a split (if not) before its next edit; nothing else changes.
```

`STRUCTURE: regressed(new: 3, worse: 1, top: opaque_code) | review-needed`
`REVIEW: shippable-with-findings(structure-only; no correctness or security defect found)`
`THREAT: clear(Discord OAuth + tier gate, no defect found)`

---

## What each skill bound to, and what it found

Per chief-engineer Phase 1 census: SUBJECT_D carries `DEBT_LEDGER.md` and
`.structure-baseline.json`, both frozen at commit `1178684` (2026-07-28) — evidence this repo has
been touched by (a copy of) this suite before, informally, with no `runs/` record of that pass on
either side. Inferred lifecycle state: **live, actively developed** (5 commits in the 24h before
this run, latest `a1abb17`), single-owner. No PROBLEM_BRIEF/ARCHITECTURE/THREAT_MODEL ledgers
exist — built without the full suite.

### structure-gate — bound (mechanical, executed against the subject's own baseline)

```
$ python tools/structure-report.py --baseline .structure-baseline.json \
    --debt-ledger DEBT_LEDGER.md .          # run from inside SUBJECT_D

Scanned: 103 code files (97 Python, deep-analyzed; 6 other, length+duplication only) · 725 functions
RATCHET — measured against 69 accepted breach(es) in the baseline.

⛔ 3 NEW breach(es) — not in the baseline:
     opaque_code = 86   [tests/test_dashboard_auth.py :: L16]
     opaque_code = 86   [tests/test_race_trace.py :: L32]
     opaque_code = 212  [tests/test_session_pace.py :: L55]
⛔ 1 accepted breach(es) GOT WORSE:
     file_lines: 1365 → 1422   [static/race-panels.js]
✅ 2 baselined breach(es) REPAID — gone from the source.

STRUCTURE: regressed(new: 3, worse: 1, top: opaque_code) | review-needed
```

**Finding S1 — `static/race-panels.js` breached its own accepted ceiling one commit after the
freeze, undetected — (proven).** Trace: `.structure-baseline.json` and `DEBT_LEDGER.md` are both
timestamped to commit `1178684` / 2026-07-28. `git log --date=short -- static/race-panels.js`
shows two commits since: `6797306` (`Split the race panels out of app.js, and pin the split`,
2026-07-29) and `a1abb17` (`Session pace: click-to-highlight a driver or team`, 2026-07-29, HEAD).
The second commit is the one that pushed the file from 1365 to 1422 lines — past whatever ceiling
made it debt-worthy to begin with — and the baseline was never re-run or re-locked after either
commit. This is not a defect in `race-panels.js` itself (Chesterton's Fence: a UI panel file
growing by a feature commit is not inherently wrong); it is a **proven gap in this subject's own
enforcement loop** — the ratchet only ratchets if someone re-runs it, and here nobody did, for the
project's most recent commit. It independently confirms IMPROVEMENT_PLAN.md's F4 finding
("repayment triggers are prose nobody watches") on a second, unrelated codebase: the failure mode
is not specific to this suite's own repo, it is a property of any debt ratchet with no CI wiring.
**Root cause difference from F4:** F4 was about a *repayment* trigger going unwatched; this is
about the *regression* side of the same ratchet going unwatched — SUBJECT_D has no CI step running
`structure-report.py --baseline` on push, so drift in either direction is invisible until someone
runs the tool by hand, which is what this run just did.

**Finding S2 — three new `opaque_code` flags, all in test fixtures — (trace-only), dismissed as a
tool limitation, not a subject defect.** All three are literal test data (session/telemetry
fixture blobs) inside test files, which `structure-report.py`'s opacity signal is not designed to
distinguish from opaque *production* logic. Per structure-gate's own handoff (wisdom call deferred
to review) and the LIVE_RUN_004 precedent for dismissing a mechanically-true-but-not-load-bearing
flag: not promoted to a finding.

**Recommendation:** re-run `--write-baseline` if `race-panels.js`'s growth is accepted (it looks
like ordinary feature growth, not decay), or split it first if not — the same fork IMPROVEMENT_PLAN
B3 gives `evolve-maintain`'s `Repay` class for this suite's own repo. Either way, wire
`structure-report.py --baseline` into whatever this subject uses for CI (none was found) so the
next drift is caught the day it lands, not a week later by an outside audit.

### threat-model — bound (Discord OAuth + tier boundary; first live use against this boundary
shape — LIVE_RUN_004 was RLS, this is session-cookie + third-party-IdP)

- **Assets:** the owner-only knowledge-base API (facts/patterns/docs — every route in
  `OWNER_ONLY_ROUTES`) and the member-tier telemetry API (everything under `/api/telemetry/`).
- **Boundary:** network → FastAPI app, authenticated by a Starlette session cookie populated via
  Discord OAuth (`webapp.py:134` `auth_callback`). What the app believes without re-verifying on
  every request: nothing — tier is *recomputed* server-side on every call (`_tier()`,
  `webapp.py:212`) from the session's bare Discord ID, never trusted from client-supplied state.
  This is the one property LIVE_RUN_004's finding (F1, stale-trust BOLA) hinged on being absent,
  and here it is explicitly absent by design (`webapp.py:179-181`'s own docstring: *"the client
  session only carries a Discord ID, never its own tier, so it can't spoof access"*) — checked by
  reading `api_proxy` (`webapp.py:263`) and confirming every dispatch path calls `_tier()` fresh;
  no cached-tier-in-session field exists to spoof.
- **CSRF/state on the OAuth callback:** `login()` mints `secrets.token_urlsafe(24)` into the
  session, `auth_callback()` requires an exact match before proceeding (`webapp.py:136-138`) —
  standard OAuth state-parameter defense, correctly implemented, checked by trace.
- **Fail-open bounded correctly:** `_is_member()` fails open to the *last-known* result on a
  transient Discord error, never to `True` from nothing (`webapp.py:197-206`) — an attacker cannot
  force a first-time grant by triggering a timeout; they can at most extend an already-granted
  member's window by ~5 minutes past a role revocation, a documented, bounded, accepted trade-off.
- **Exception-message surface checked and found narrow (trace-only):** `api_proxy` returns
  `str(exc)` to the caller on any handler exception (`webapp.py:292-294`). Traced every `raise` in
  the dispatch path it can reach (`dashboard.py:265,293,1037,1047,1053,1072`) — all are
  `ValueError`s carrying only caller-supplied identifiers (session id, driver, lap number), never a
  file path, credential, or stack detail. Not a finding: the pattern (echoing exception text to the
  caller) is a real anti-pattern in general, but every reachable exception on this boundary is
  already clean by construction, so promoting it would be pattern-matching without a
  concrete abuse case (Law 3: violation ≠ deviation; this is a deviation from best practice with
  no live deviation-to-harm path found).
- **Clean boundaries (findings too, Phase 4):** owner-only routes correctly gated by exact Discord
  ID match; member routes correctly gated by role lookup; static file serving traversal-checked
  (`dashboard.py:1408-1409`, `path.resolve()` + `parents` containment check, independently
  reachable from `webapp.py`'s `StaticFiles` mount which delegates to Starlette's own equivalent
  check).

`THREAT: clear(Discord OAuth + tier gate, no defect found)`

### senior-review — bound

Same invariants derived as `threat-model`'s (a user's tier reflects the server's own check, never
client state) plus one design-quality read: `webapp.py` and `dashboard.py` are cleanly separated
(thin gating layer over a pure data layer, per the module's own docstring), and inline comments at
every non-obvious decision (fail-open windows, salt separation, gate-the-prefix-not-the-list)
consistently name the *why*, not the *what* — the same discipline this suite's own Law asks of
its own tools. No structural or design finding beyond S1/S2 above.

### data-tier — not bound

No SQL/ORM query paths exist; the data layer reads local Parquet files directly. Not applicable,
correctly returned empty per Law 3 (empty return is a pass, not a skip).

### Skills that correctly returned not-applicable

`problem-framing` (no brief requested), `arch-design`, `build-discipline`, `data-evolution`,
`evolve-maintain`, `wire-check`, `scrutinize` (no delta to review — this run reviews the whole
subject, not a pending change), `debug-protocol` (no observed failure), `perf-optimize`,
`ship-gate` (not a deploy request), `symptom-audit` (no felt complaint — this is a proactive audit),
`meta-skills` (always-on discipline, not a bound skill).

---

## Skill-yield (PROTOCOL §12 / MAP.md, computed for the first time)

**Pre-run knowledge** (everything already documented about SUBJECT_D before this run started):
69 currently-accepted structural-debt entries in `.structure-baseline.json`, frozen 2026-07-28.
(`DEBT_LEDGER.md`'s row count reads higher than 69 at a glance because it also carries a separate
`## Repayments` table of already-closed rows kept for provenance, not currently-open debt — the
69 in `.structure-baseline.json` is the authoritative "open today" figure this run measured
against.) Zero security findings, zero live-run records on either side (no `runs/` entry existed
for the prior informal pass that produced the baseline).

**Post-run findings:** one **(proven)** defect (S1 — one commit's worth of undetected debt-ratchet
drift, confirming F4 on a second, independent codebase) plus one dismissed tool-limitation
observation (S2) and one clean, positively-checked security boundary (first threat-model bind
against a session-cookie + third-party-IdP shape, as opposed to LIVE_RUN_004's RLS shape).

**Yield = 1 proven defect + 1 confirmed cross-codebase pattern + 1 new boundary shape checked
clean**, from a subject that had already been touched by this suite once informally and believed
itself current. The size of the gap is modest (one commit, one file) precisely *because* the
subject was already well-tended — which is itself the useful signal: skill-yield on a
well-maintained subject should be small and mechanical, not zero. A yield of zero would have meant
either the subject was flawless (unlikely on any real system, per every prior LIVE_RUN) or the
suite failed to look hard enough; a yield this size, landing exactly on the one place a mechanical
ratchet is known to silently fail, is evidence the lens is still working on a subject that isn't
the suite auditing itself.

---

## run-trace + verdict-lint on this transcript

This run classifies as a `review` run (`REVIEW`, `STRUCTURE`, `THREAT` present, no `GATE` —
correctly, since no new code was built or gated here). `run-trace.py`'s `THREAT`-classification gap
recorded in LIVE_RUN_004 does not bite this transcript for the same reason it didn't bite that one:
`REVIEW` is present alongside `THREAT`, so the completeness profile has a verdict it recognizes to
check against.
