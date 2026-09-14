---
name: threat-model
description: >
  Find what an adversary can make a system do that it must not — before a build ships or after a review flags a trust concern. Use for auth, sessions, secrets, untrusted input, deserialization, third-party deps, or "is this secure".
---

# Threat Model

> **The question:** What can an attacker make it do that it must not?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

intended-behavior correctness → `correctness-gate`; whole-codebase wisdom → `senior-review`; a not-yet-landed delta → `scrutinize`; deploy reversibility → `ship-gate`.

You assume the attacker has read the source, has a valid account, and is patient. You list what the
system protects, walk every boundary the way an attacker would, and turn each plausible abuse into
a **failing test the gate has to make pass** — so "secure" is never a feeling, always a list of
named attacks that are now defended. You never claim a system is secure; you claim that specific
attacks were modelled and specific defenses were proven.

## The job

1. **Assets before attacks.** Name what is worth stealing or breaking first — credentials,
   sessions, money, PII, integrity of a shared resource (seats, balances), availability. An attack
   with no asset behind it is noise; an asset with no attack modelled is a blind spot.
2. **Trust is something the system gives, and giving it to the wrong place is the usual cause.**
   For every input, ask *where does the system decide to believe this?* Permission taken from data
   the client supplied — a role in a cookie, a price in a form, an id in a URL — is the single most
   common critical finding. Name it as trusting the wrong source, not as a coding slip.
3. **Walk the boundary as the attacker, not as the user.** At each trust boundary, the attacker
   sends what an honest user never would: forged tokens, replayed requests, other users' ids,
   oversized, empty, unicode or encoded payloads, wildcards, duplicate requests sent at once. The
   honest path working proves nothing here.
4. **Every finding becomes a test, not a sentence.** A threat written as prose fades away; a threat
   written as a failing test the gate runs stays defended. This skill *writes the test spec*;
   `correctness-gate` *runs it* — proof that a defense works stops at **(trace-only)** until the
   gate executes it, and the report says so.
5. **Dependencies and configuration count too.** Secrets in the source, debug modes left on,
   unpinned or abandoned dependencies, and permissions that are too broad are all threats that need
   no cleverness from an attacker at all. List them in the same pass; they are usually the easiest
   to exploit.
6. Law 3 and Law 5 apply: a security pattern you don't recognise gets the "what is the best reason
   a competent engineer would do this?" check before you flag it, and Law 5 means a real finding
   ships its fix in the same response — with that fix closing under §7 (reviewed, checked against every other
   surface with the same exposure, shown to gate on the system's real authority check, ending in a
   `FIX` line).
7. **Something left open on purpose is the baseline, not a finding.** Per PROTOCOL §1, a boundary
   the system deliberately leaves open — shown by its own policies, schema comments, docs, or an
   existing surface already serving the same data — is the baseline you measure an attack against.
   The finding, if there is one, is what is *newly* possible on top of that: the same data now
   reachable with a different kind of credential whose exposure is wider (for example, an API token
   that sits in scripts and shared documents, versus a browser session), or a contradiction between
   what the system says it allows and what it actually enforces. Phase 1 always works out exposure
   against this baseline.

## Steps: Assets → Boundaries → Abuse → Prove → Prescribe → Hand off

### Phase 1 — Assets
List what this system protects and what an attacker gains from each, in one table:
`asset | who wants it | what they gain | worst case if it goes wrong`. Rank by that worst case;
the top rows decide where the rest of the audit spends its effort.

### Phase 2 — Boundaries
Map every trust boundary: where data or control crosses from less-trusted to more-trusted
(network → app, user → admin, client → server, untrusted file → parser, third-party → core). For
each, record *what the system currently takes on faith without checking*. This is the phase
everything else rests on — most critical findings are a boundary trusting the wrong side.

### Phase 3 — Abuse (work the attacks out; don't recite a list)
For each top asset at each boundary, work out the attacks this *particular* system allows. The
categories below are a **replaceable checklist**, not a limit — go past them:
- **Identity and permission** — forge, replay, escalate: can a client grant itself more permission
  than it has? Is permission ever read from data the client supplied?
- **Input → sink** — injection (SQL/command/template/path), unescaped wildcards, deserialization
  of untrusted bytes, SSRF.
- **Object access** — can actor A reach actor B's resource by changing an id (IDOR)?
- **Shared resources** — can a shared counter (seats, stock, balance) be raced, or pushed below
  zero, by two requests arriving between the check and the update?
- **Secrets & config** — secrets in source/history, debug modes, default keys, permissive CORS.
- **Supply chain** — unpinned, abandoned, or over-privileged dependencies.
A stronger model will come up with sharper and stranger attacks here — which is exactly why this
is worked out rather than recited.

### Phase 4 — Prove
Move from reading to running on the attacks against the most valuable assets: actually forge the
token, send the crafted input, fire the duplicate requests at once. An attack you executed is
**(proven)**; a complete chain you only read is **(trace-only)**, named with the one command that
would settle it. A boundary that survives the attack is **also a finding** — it tells the director
where not to spend.

### Phase 5 — Prescribe
For each finding: the asset, the boundary, the attack, the evidence tag, which misplaced trust
caused it, and the **contained fix, written in the project's conventions** (Law 5). Fixes that
change the structure of who is trusted (move the permission check to the server, change the
session format) go to `arch-design` as decisions, never slipped in here.

### Phase 6 — Hand off
For each defended threat, write the **abuse-case test spec** — input, expected rejection,
structured-failure shape — and hand it to `correctness-gate` to execute and own as a regression.
Append the asset/boundary/abuse table to the report — a file only when §3 warrants one.
Before any ship, `ship-gate` reads it; an unmodelled top-asset boundary blocks the deploy.

## Report

Shape and wording: `PROTOCOL.md` §9. The opening is the worst thing an attacker can do today, in
one sentence, with its evidence tag.

One row per finding, ordered by blast radius: the boundary, what the attacker gets, the evidence,
the fix. The asset table and the boundaries that came back clean go under `Detail` — clean
boundaries are counted in the verdict line, never dropped.

a `THREAT` line (PROTOCOL §5) — `clean` names how many boundaries were modelled and how many are defended.

## Common mistakes

Running a security checklist with no asset behind each check; treating the happy path as evidence;
findings written as prose that then fade away; claiming "secure" instead of "these named attacks
are defended"; skipping secrets-in-source and debug-left-on as too obvious to bother listing;
flagging a pattern you don't recognise as a hole without the Law 3 check.
