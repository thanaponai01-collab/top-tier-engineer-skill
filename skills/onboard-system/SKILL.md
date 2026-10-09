---
name: onboard-system
description: >-
  First contact with an unfamiliar codebase — set it up for the skills, then build and leave behind the full picture (what it has, how it's shaped, why it's built that way) so every later session or agent finds it instead of rediscovering it. Runs project-setup itself as its first step; use project-setup alone when only the checks are wanted. Use for "onboard me to this codebase", "get up to speed on this system", "I've never seen this repo before", "learn this system top to bottom", or when a repo has no VERIFY.md, FEATURES.md, docs/architecture.md or WHY.md yet. Manual: run /onboard-system.
disable-model-invocation: true
---

# Onboard System

The first agent into an unfamiliar system either does the work of understanding it and keeps that
work to itself, or skips the work and guesses. Neither leaves anything for the next session. This
skill runs the other skills that each hold one piece of the picture, in the order that lets each one
use the last one's output, and ends with every piece written to a file a fresh agent can find with no
chat history at all.

This skill does not replace the skills it calls — it is the sequence and the handoffs between them.
Each step below names the skill that does the real work; read that skill's own file for how it does
it.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

## 1. Check what already exists

Look for `VERIFY.md`, `FEATURES.md`, `docs/architecture.md` and `WHY.md` at the repo root before
doing anything. Say in one line what is already there. Skip straight to the step whose file is
missing; never redraft a file that already exists — that is the job of the skill that owns it, not
this one, and it already refuses to overwrite.

## 2. Set the project up — `project-setup`

Run it if verification, the feature map, the agent startup block or intent/work context is missing
or stale. Follow existing equivalent documents through startup pointers. Skip setup only when
the relevant inputs are current; file existence alone does not establish readiness.

## 3. Map what it has — `feature-map`

Fills in `FEATURES.md` for real: one entry per feature, each with the way a user reaches it and how
that entry is known. `project-setup` only drafts this file's shape; this step is what makes it true.

## 4. Draw how it's built — `arch-map`

As-is view, system altitude, traced from the entry points `feature-map` just found. One diagram, one
headline sentence, to `docs/architecture.md`. This is the shape of the system — it does not explain
why any of it looks this way; that is the next step.

## 5. Get the why — `code-history`

For the two or three things step 4 turned up that look surprising, wrong, or load-bearing (a
box everything points into, a layer that shouldn't call the one above it, a piece with no obvious
reason to exist), ask why. Add each answer to `WHY.md`, cited. Skip anything ordinary — this is not
a pass over every file, only the parts the map just flagged.

## 6. Prove you actually understand it

Give the account from `explain`, overview mode, using `FEATURES.md`'s `trace:` lines and
`docs/architecture.md` instead of re-tracing from scratch. If someone is present, run its step 4 and
have them catch you on a case you didn't cover. No one to answer: trace one case yourself and say
what the code does there. This is the check that step 2–5 produced a real picture and not four files
nobody read back.

*Test:* you can give the overview cold, then get one prediction check right, using only the files
just written — no memory of steps 2–5.

## 7. Report

Answer first: what now exists, one line each, `CREATED` vs `KEPT` vs `SKIPPED` (and why skipped —
usually "already there"). Then the one thing from step 5 most worth remembering, and the one gap
still open (a `TODO` in `VERIFY.md`, an entry point `feature-map` couldn't reach, a `docs/` diagram
still marked *suspected*).

```
FILES:  VERIFY.md (kept) · FEATURES.md (created) · docs/architecture.md (created) · WHY.md (created)
KNOW:   <the one surprising thing from step 5, with its file:line or record>
GAP:    <what's still open, and which skill closes it>
```

## Rules

- **Sequence, not a rerun.** Never redo a step whose file already exists and is current — that skill
  owns keeping it true, not this one.
- **Proportional depth.** Step 5 is bounded to what step 4 flagged. This skill onboards to a working
  picture, not to a complete history of every decision ever made — that is `code-history` run again,
  later, on demand.
- **Every claim in the files this step touches still needs its evidence label or `file:line`.** This
  skill inherits each called skill's own test; it does not relax any of them.

*Test:* a fresh session with no chat history, pointed only at the repo, can answer "what does this do,
how is it shaped, and why" from the files alone — and can name which skill to run next for anything
it can't.

Verifying the checks stay green is `verify-loop`; something breaking after onboarding is
`debug-protocol`; a question this pass didn't cover is `code-history` or `explain`, run directly.
This skill is only the first pass and the order to run the others in.
