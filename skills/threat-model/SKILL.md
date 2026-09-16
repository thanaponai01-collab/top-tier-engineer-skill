---
name: threat-model
description: Find what an attacker can make a system do that it must not, and turn each abuse into a test. Use for auth, sessions, secrets, untrusted input, deserialization, third-party dependencies, or "is this secure / can this be abused?".
---

# Threat Model

Assume the attacker has read the source, has a valid account, and is patient. List what the system
protects, walk every boundary as the attacker, and turn each plausible abuse into a **failing test
that must pass**. Never claim a system is secure. Claim that specific attacks were modelled and
specific defenses were proven.

## Rules

1. **Assets before attacks.** Name what's worth stealing or breaking first: credentials, sessions,
   money, personal data, shared resources (seats, balances), availability. An attack with no asset
   is noise.
2. **Ask where the system decides to believe each input.** Permission taken from client-supplied
   data (a role in a cookie, a price in a form, an id in a URL) is the most common critical
   finding. Name it as trusting the wrong source.
3. **Walk the boundary as the attacker.** Forged tokens, replayed requests, other users' ids,
   oversized, empty, encoded or unicode payloads, wildcards, duplicate simultaneous requests. The
   honest path working proves nothing.
4. **Every finding becomes a test spec**, not a sentence: input, expected rejection, error shape.
   A defense you only read about is traced, not proven, until the test runs.
5. **Config and dependencies count.** Secrets in source or git history, debug modes on, default
   keys, permissive CORS, unpinned or abandoned dependencies, over-broad permissions. These need no
   cleverness to exploit.
6. **Judge against the system's intent.** If the system deliberately leaves something open (its own
   policies, docs, or an existing surface already serving that data), that's the baseline. The
   finding is what's *newly* possible on top of it: the same data reachable with a more widely
   exposed credential, or a contradiction between stated and enforced policy.
7. **Unfamiliar isn't broken.** Before flagging an odd security pattern, state the best reason a
   competent engineer might have for it.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

## Phases

### 1. Assets
`asset | who wants it | what they gain | worst case`. Rank by worst case; top rows get the effort.

*Test:* every attack below names one of these assets.

### 2. Boundaries
Map every place data or control crosses from less to more trusted: network → app, user → admin,
client → server, uploaded file → parser, third party → core. For each, note what's taken on faith.
Most critical findings are a boundary trusting the wrong side.

### 3. Abuse
For each top asset at each boundary, work out the attacks *this* system allows. Starting points,
not a limit:
- **Identity & permission:** forge, replay, escalate. Is permission ever read from client data?
- **Input → sink:** SQL, command, template, path injection; unescaped wildcards; untrusted
  deserialization; SSRF.
- **Object access:** can user A reach user B's resource by changing an id?
- **Shared resources:** can a counter be raced or pushed below zero between check and update?
- **Secrets & config**, **supply chain.**

### 4. Prove
For attacks on the most valuable assets, run them: forge the token, send the crafted input, fire
the concurrent requests. An attack you only read is traced: give the command that would settle it.

*Test:* each top finding is either proven by an attack you ran, or carries the exact command that would settle it.

### 5. Fix
For each finding: asset, boundary, attack, proven / traced / suspected, the misplaced trust, and a contained
fix in the project's conventions. Before calling a permission fix complete, list **every** surface
exposing the same data or operation (pages, API routes, exports, background jobs, webhooks) and
leave them consistent or name the gap. Show the check you gate on (membership, role, ownership) is
how the system really decides access, not a field anyone can write. Fixes that change who is
trusted (moving a check server-side, changing the session format) are design decisions: raise them.

## Report

Open with the worst thing an attacker can do today, in one sentence, proven, traced or suspected. Then one row
per finding by blast radius: boundary, what the attacker gets, evidence, fix. Then the abuse-case
test specs, the asset table, and how many boundaries were modelled and held.

## Common mistakes

Checklists with no asset behind them; the happy path as evidence; findings as prose that fades;
claiming "secure"; skipping secrets-in-source as too obvious; fixing one door and leaving the others
open.
