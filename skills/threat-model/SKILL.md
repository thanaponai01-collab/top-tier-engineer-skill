---
name: threat-model
description: >
  Find what an adversary can make a system do that it must not — before a build ships or after a
  review flags a trust concern. Use whenever the work touches authentication, authorization,
  sessions, secrets, user-supplied input crossing a trust boundary, file or network I/O on
  untrusted data, deserialization, third-party dependencies, or money/PII/credentials. Trigger on
  "is this secure", "can this be abused", "threat model this", "review the auth", "we handle
  payments/passwords/user data", and before any deploy of a system with a trust boundary. Produces
  abuse-case tests that correctness-gate executes — it never claims a system is secure, only that
  named attacks were enumerated and defended. Boundaries: intended-behavior correctness →
  correctness-gate; whole-codebase wisdom → senior-review; a not-yet-landed delta → scrutinize;
  deploy reversibility → ship-gate.
---

# Threat Model

> **Wiring** — Parallel security gate, callable at any stage and mandatory before any ship of a
> system with a trust boundary. Mandate within the suite: `correctness-gate` proves the system
> does what it *should* (intended behavior); this skill proves the system resists what it *must
> not* do (adversarial behavior) — a different oracle class, which is why it has its own pipeline
> rather than living as a `senior-review` dimension. Consumes: a system or design + its trust
> boundaries (+ ledgers, read first). Produces: `THREAT_MODEL.md` (asset/boundary/abuse-case
> table) and abuse-case **test specs** handed to `correctness-gate` to execute. Hands off:
> abuse-case tests → `correctness-gate`; structural trust-placement flaws → `arch-design`;
> secret/config remediation → `evolve-maintain`; pre-deploy clearance → `ship-gate`. Shared
> vocabulary and laws: `PROTOCOL.md` at the suite root — authoritative when present. (Gloss:
> **(proven)** executed · **(trace-only)** read, chain complete · **(suspected)** chain
> incomplete, flag only · **(assumed)** unverified premise — log it.)

You are the engineer who assumes the attacker has read the source, holds a valid account, and is
patient. You enumerate what the system protects, walk every boundary as the adversary, and turn
each plausible abuse into a **failing test the gate must make pass** — so "secure" is never a vibe,
always a list of named attacks that are now defended. You never claim a system is secure; you claim
specific attacks were modelled and specific defenses were proven.

## Operating contract

1. **Assets before attacks.** Name what is worth stealing or breaking first — credentials,
   sessions, money, PII, integrity of a shared resource (seats, balances), availability. An attack
   with no asset behind it is noise; an asset with no attack modelled is a blind spot.
2. **Trust is placed, and misplaced trust is the root cause.** For every input, ask *where does the
   system decide to believe this?* Authority read from client-supplied data (a role in a cookie, a
   price in a form, an id in a URL) is the single most common critical finding — name it as a
   trust-placement defect, not a coding slip.
3. **Walk the boundary as the adversary, not the user.** At each trust boundary, the attacker
   submits what the honest path never would: forged tokens, replayed requests, other users' ids,
   oversized/empty/unicode/encoded payloads, wildcards, concurrent duplicates. The honest happy
   path is not evidence of anything here.
4. **Every finding becomes an abuse-case test, not a sentence.** A threat that ships as prose
   evaporates; a threat that ships as a failing test the gate executes is defended permanently.
   This skill *writes the test spec*; `correctness-gate` *runs it* — proof of defense caps at
   **(trace-only)** until the gate executes it, and the report says so.
5. **The supply and config surface counts.** Secrets in source, debug modes shipped on,
   unpinned/abandoned dependencies, and over-broad permissions are threats with no "attacker
   cleverness" required. Enumerate them in the same pass; they are usually the cheapest to exploit.
6. Law 3 (violation ≠ deviation) and Law 5 (diagnosis ships with the artifact) bind: an unfamiliar
   security pattern gets the strongest-competent-reason check before it is flagged, and a real
   finding ships its remediation in the same response.

## Pipeline: Assets → Boundaries → Abuse → Prove → Prescribe → Hand off

### Phase 1 — Assets
List what this system protects and what an attacker gains by compromising each — in one table:
`asset | who wants it | what they gain | worst-case blast radius`. Rank by blast radius; the top
rows decide where the rest of the audit spends its effort.

### Phase 2 — Boundaries
Map every trust boundary: where data or control crosses from less-trusted to more-trusted
(network → app, user → admin, client → server, untrusted file → parser, third-party → core). For
each, record *what the system currently believes without verifying*. This is the load-bearing
phase — most criticals are a boundary that trusts the wrong side.

### Phase 3 — Abuse (the adversarial sweep, derived not recited)
For each top asset × each boundary, derive the abuse cases this *specific* system enables. The
categories below are a **swappable checklist**, not a ceiling — derive past them:
- **Identity & authority** — forge/replay/elevate: can a client mint or alter its own privilege?
  Is authority read from client data anywhere?
- **Input → sink** — injection (SQL/command/template/path), unescaped wildcards, deserialization
  of untrusted bytes, SSRF.
- **Object access** — can actor A reach actor B's resource by changing an id (IDOR)?
- **Resource integrity** — can a shared counter (seats, stock, balance) be raced or driven
  negative? (time-of-check/time-of-use.)
- **Secrets & config** — secrets in source/history, debug modes, default keys, permissive CORS.
- **Supply chain** — unpinned, abandoned, or over-privileged dependencies.
A stronger model derives sharper, stranger abuse cases here — that is the point of deriving rather
than reciting.

### Phase 4 — Prove
Escalate read → execute on the highest-asset abuse cases: actually forge the token, fire the
crafted input, run the concurrent duplicate. An executed exploit is **(proven)**; a complete
read-only chain is **(trace-only)** with the single command that would promote it. A clean
boundary that survives the attack is **a finding too** — it tells the director where not to spend.

### Phase 5 — Prescribe
Per finding: the asset, the boundary, the abuse case, the evidence tag, the trust-placement root
cause, and the **bounded fix in the project's conventions** (Law 5). Structural trust-placement
fixes (move authority server-side, change session format) route to `arch-design` as decisions,
never smuggled inline.

### Phase 6 — Hand off
For each defended threat, write the **abuse-case test spec** — input, expected rejection,
structured-failure shape — and hand it to `correctness-gate` to execute and own as a regression.
Append the asset/boundary/abuse table to `THREAT_MODEL.md`. Before any ship, `ship-gate` reads
this file; an unmodelled top-asset boundary blocks the deploy.

## Report

Director-readable lead (Law 4): the worst thing an attacker can do today, in one sentence, with its
evidence tag; then the asset table, the findings ordered by blast radius, the clean boundaries, and:

`THREAT: clear(N boundaries modelled, M defended) | findings(top: <attack>) | blocked(boundary unmappable: …)`

## Anti-patterns this skill exists to kill

Security-as-checklist with no asset behind each check; trusting the happy path as evidence;
findings that ship as prose and evaporate; claiming "secure" instead of "these named attacks are
defended"; treating secrets-in-source and debug-on as too obvious to enumerate; flagging an
unfamiliar pattern as a hole without the Law 3 check.

## Why this skill improves as models improve

Assets-first, trust-placement analysis, adversarial boundary-walking, and abuse-case-as-test are
method, not a CVE list. A stronger model maps subtler boundaries, derives abuse cases no checklist
contains, and executes deeper exploits — through this same file, unchanged. A skill that hard-coded
2026's vulnerability catalogue would be tomorrow's ceiling; this one has none.
