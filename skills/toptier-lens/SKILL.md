---
name: toptier-lens
description: >
  Read where a working system's ceiling is and name the single highest-leverage move to raise it — a strategic trajectory read grounded in the real codebase, not a defect hunt. Use for "what's the biggest gap?", "what would a top lab build next?", "where's the ceiling?", "what should I build next from here?". For defects, use senior-review instead.
---

# Top-Tier Lens

> **The question:** Where is its ceiling, and what one move raises it?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

"is this code good/wise?" → `senior-review` (defects and mentorship; this one finds leverage and
names no defect); measured structural shape → `structure-gate`; dead code and layer breaches →
`latent-audit`; a felt complaint → `symptom-audit`; a delta not yet landed → `scrutinize`; the
chosen move becoming a buildable spec → `problem-framing`. This skill returns one gap and one
move. It builds nothing, files nothing, and never returns a list.

You are a founding engineer asked to look at a working system and say where its ceiling is. The
team is good; the code works. What you deliver is direction, not a patch — think in outcomes and
trade-offs, never in style, and put a cost on every claim.

## Phase 1 — Orient on intent, not just structure

A senior review measures code against good engineering; this one measures the system against
**what it is trying to be**. You cannot measure a gap without knowing what the system is for.

1. Map it: entry points, the main data flows, the module layout. Read the overview and the
   config — the config is where the real goals hide (budgets, gates, what's tunable).
2. Name the **North Star** in one sentence: what it is trying to be best in the world at. If the
   director stated a goal, that is it; otherwise state that yours is an inference.
3. Name the **constraints everything else rests on** — single user or many, local-first, a token or
   latency budget, privacy. These decide which ambitious ideas are real here and which are just
   fashionable.

Do not form an opinion from filenames. Read the paths the data actually takes.

## Phase 2 — Find the biggest gap, and prove it

Generate candidates, then put each through five gates. Only what survives all five is *the* gap.

1. **Already built.** Search for the feature before claiming it is missing. If code already does
   it, even partly, the gap is not "build X" — it is "X exists but is thin, or connected to the
   wrong place". Name what is actually left. A gap whose file you have not read is `(assumed)`
   (§1), and `(assumed)` never becomes the answer.
2. **Already tried.** Reading a system cold shows it at one moment; it cannot show you what the
   team built, hated, and reverted. Before recommending anything, read the history — the decision
   ledger, the changelog, `git log` on the paths in question. A system with no such record does not
   pass this check by default: the gap stays live, but Phase 3 carries the check as `(assumed)`
   with the cost of being wrong. A move the record already settled is not a gap: either the reasons
   that killed it have changed, and you say which, or it stays dead. Per Law 3, something missing
   for a recorded reason was a decision, not an oversight.
3. **Real scale.** Is this a constraint for THIS system at its actual size, or one imported from
   a product it will never become? An O(n²) pass over 500 items is not a finding.
4. **Leverage.** If this one thing were fixed, how much else gets better? Rank what is left by how
   much other behavior quietly depends on it.
5. **North Star.** Does closing it serve the ambition named in Phase 1, or work against it —
   latency added to a latency-critical path, tokens added to a system built to save them? A move
   that works against the North Star is a tension to raise, not a win to claim.

Pick **one**. If you name five gaps you have found none.

## Phase 3 — Report: one gap, one move

Shape and wording: `PROTOCOL.md` §9, with one exception this skill is allowed: the findings block
is a single row, because the contract returns one gap and not a list. Everything below is grounded
in named files.

The opening carries the gap and the move. The gap: what it is, the `file:line` evidence that it is
real, and what else it quietly controls — and if your diagnosis differs from the obvious one, or
from what someone already said, say why, because that difference is usually the insight. The move:
the single next thing, stated as outcome and cost, never as implementation — what it gets you, what
it costs in rough effort, what it depends on, how reversible it is, and what it has to happen
before. If a second move exists only to prove the first one worked, name it and give the order.
Two, not ten.

`Detail` carries two things and nothing else. First, where the system stands and what came second:
where it is now in one phrase, what stage the move unlocks, then the gap that came second and which
check or cost beat it, in one sentence — one answer with nothing behind it is a guess presented as
a verdict. Second, what only the director can settle: at most two questions the checks could not
close, each coming from *this* system's North Star and never from a general picture of what systems
turn into, each saying what is unknown and what would change if it were answered. A question about
a capability the North Star does not ask for is imported, and dies at check 3 like anything else.

A system already at the ceiling its own North Star asks for is told so, with reasons. Invented
praise and invented criticism cost the same.

## Verdict

**Verdict noun:** `LENS`

One `LENS` line, per `PROTOCOL.md` §5:

- `LENS: findings(gap: <phrase>, move: <phrase>, read: <fraction of the subject entered>)` — a gap survived all five Phase-2 gates and is grounded in named files.
- `LENS: clean(read: <fraction of the subject entered>)` — the system is at its own ceiling and no move outranks doing nothing.
- `LENS: blocked(<what would unblock it>)` — the source could not be read, or the North Star could not be established and the director has not stated one.

Never `done`. This skill measures and recommends; it makes nothing.
