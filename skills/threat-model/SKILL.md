---
name: threat-model
description: >
  Find what an attacker can make a system do that it must not, and turn each abuse into a test. Use for auth, sessions, secrets, untrusted input, deserialization, third-party dependencies, or "is this secure / can this be abused?".
---

# Threat Model

Assume the attacker has read the source, has a valid account, and is patient. List what the system
protects, walk every boundary as the attacker, and turn each plausible abuse into a **failing test
that must pass**. Never claim a system is secure. Claim that specific attacks were modelled and
specific defenses were proven.

## How to work

A senior engineer is expensive for what they check, not for how much they say. These are the habits,
each with the test that shows you did it. Scale them to the stakes: a typo needs none of the ritual,
a migration needs all of it.

**1. Understand before you change.** Read the code the work touches and trace the real flow from its
entry point. For a bug, reproduce it first. Before editing a function, find every caller: the fix
belongs where they all route through. Say in one line what you read the request as (and not as); if
two readings lead to different work, ask the one question that separates them and keep working on
what it doesn't block.
*Test:* you can name the files involved and the observation that would prove you wrong.

**2. Ground truth over memory.** Check APIs, versions, config and behavior against the installed
code, `--help`, the lockfile, or a run. Anything remembered is an assumption until looked at.
*Test:* every fact the work rests on came from something you opened or ran in this session.

**3. Decide what done looks like first.** Turn the task into a check: "fix the bug" → a repro that
fails, then passes; "refactor" → the same tests green before and after; "is it secure" → the abuse
case that now fails. Loop until the check passes. Never weaken the check to get there.
*Test:* the check was written down before the work started.

**4. Smallest change that holds.** No features, options or abstractions nobody asked for; an
abstraction earns its place on the second real use. Boring beats clever. Match the existing style,
leave adjacent code alone, and mention unrelated problems instead of fixing them. Clean up only what
your own change orphaned.
*Test:* every changed line traces to the request.

**5. Size the risk before the move.** Ask what breaks if you're wrong and whether it can be undone.
Reversible: move fast. One-way (deleted data, sent messages, deploys, public APIs): slow down and
confirm first.
*Test:* you can state the rollback in one sentence, or you asked before acting.

**6. Stop when you're guessing.** A second failed attempt on the same idea means your model of the
system is wrong. Go back to step 1 and re-check the assumption instead of trying a third variation.
*Test:* each attempt tested a different hypothesis.

**7. Say how you know, briefly.** Answer first: the verdict in plain words, evidence after. Label
claims *proven* (you ran it), *traced* (you read the whole chain) or *suspected* (neither); a clean
result names what you checked. Disagree in one line, then do what was asked, unless the step can't be
undone or would fake the result: then stop and ask.
*Test:* a busy reader can act on your first two lines. Cut words, never verification.

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

## Phases

### 1. Assets
`asset | who wants it | what they gain | worst case`. Rank by worst case; top rows get the effort.

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

### 5. Fix
For each finding: asset, boundary, attack, proven or traced, the misplaced trust, and a contained
fix in the project's conventions. Before calling a permission fix complete, list **every** surface
exposing the same data or operation (pages, API routes, exports, background jobs, webhooks) and
leave them consistent or name the gap. Show the check you gate on (membership, role, ownership) is
how the system really decides access, not a field anyone can write. Fixes that change who is
trusted (moving a check server-side, changing the session format) are design decisions: raise them.

## Report

Open with the worst thing an attacker can do today, in one sentence, proven or traced. Then one row
per finding by blast radius: boundary, what the attacker gets, evidence, fix. Then the abuse-case
test specs, the asset table, and how many boundaries were modelled and held.

## Common mistakes

Checklists with no asset behind them; the happy path as evidence; findings as prose that fades;
claiming "secure"; skipping secrets-in-source as too obvious; fixing one door and leaving the others
open.
