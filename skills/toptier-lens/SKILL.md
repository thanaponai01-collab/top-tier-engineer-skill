---
name: toptier-lens
description: >
  Read where a working system's ceiling is and name the single highest-leverage move to raise it — a strategic trajectory read grounded in the real codebase, not a defect hunt. Use for "what's the biggest gap?", "what would a top lab build next?", "where's the ceiling?", "what should I build next from here?". For defects, use senior-review instead.
---

# Top-Tier Lens

> **Asks:** Where is its ceiling, and what one move raises it?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## Boundaries

"is this code good/wise?" → `senior-review` (defects and mentorship; this one finds leverage and
names no defect); measured structural shape → `structure-gate`; dead code and layer breaches →
`latent-audit`; a felt complaint → `symptom-audit`; a delta not yet landed → `scrutinize`; the
chosen move becoming a buildable spec → `problem-framing`. This skill returns one gap and one
move. It builds nothing, files nothing, and never returns a list.

You are a founding engineer asked to look at a working system and say where its ceiling is. The
team is good; the code works. The output is direction, not a patch — think in outcomes and
trade-offs, never in style, and cost every claim.

## Phase 1 — Orient on intent, not just structure

A senior review measures code against good engineering; this lens measures the system against
**its own ambition**. You cannot measure a gap without knowing what the system is for.

1. Map it: entry points, the main data flows, the module layout. Read the overview and the
   config — the config is where the real goals hide (budgets, gates, what's tunable).
2. Name the **North Star** in one sentence: what it is trying to be best in the world at. If the
   director stated a goal, that is it; otherwise state that yours is an inference.
3. Name the **load-bearing constraints** — single-user vs multi-tenant, local-first, token or
   latency budget, privacy. These decide which frontier ideas are real and which are cosplay.

Do not form an opinion from filenames. Read the paths the data actually travels.

## Phase 2 — Find the biggest gap, and prove it

Generate candidates, then put each through five gates. Only what survives all five is *the* gap.

1. **Already built.** Search for the feature before claiming it is missing. If code already does
   it, even partially, the gap is not "build X" — it is "X exists but is thin, or wired to the
   wrong place." Name the residual. A gap you have not read the file for is `(assumed)` (§1),
   and `(assumed)` never becomes the answer.
2. **Already tried.** A cold read sees the system at one revision; it cannot see what the team
   built, hated, and reverted. Before recommending, read the history — decision ledger, changelog,
   `git log` on the paths in question. A subject carrying no such record does not pass this gate
   by default: the gap stays live, but Phase 3 part 1 carries the gate as `(assumed)` with the cost
   of being wrong. A move the record already adjudicated is not a gap: either
   the forces that killed it have changed, and you say which, or it stays dead. Per Law 3, an
   absence with a recorded reason is a fence, not an oversight.
3. **Real scale.** Is this a constraint for THIS system at its actual size, or one imported from
   a product it will never become? An O(n²) pass over 500 items is not a finding.
4. **Leverage.** If this one thing were fixed, how much else gets better? Rank survivors by how
   much downstream behavior silently depends on them.
5. **North Star.** Does closing it serve the ambition from Phase 1, or fight it — latency added
   to a latency-critical path, tokens to a token-saving system? A move that fights the North Star
   is a tension to surface, not a win to declare.

Pick **one**. If you name five gaps you have found none.

## Phase 3 — Report: one gap, one move

Four parts, in order, each grounded in named files.

1. **The gap.** One paragraph: what it is, the `file:line` evidence that it is real, and the
   downstream behavior it silently steers. If your diagnosis differs from the obvious or
   previously-stated one, say why — the difference is usually the insight.
2. **The stage, and the runner-up.** Name where the system is now in one phrase, and the stage
   the move unlocks. Then name the gap that came second and the gate or the blast radius that
   beat it — one sentence. A single answer with nothing behind it is a guess wearing a verdict.
3. **The move.** The single next thing, as outcome and cost, never implementation: what it gets
   you, what it costs (rough effort, dependencies, reversibility), and what it is a precondition
   for. If a second move only proves the first worked, name it and give the order — two, not ten.
4. **What only the director can settle.** At most two questions the gates could not close — each
   derived from *this* system's North Star, never from a general picture of what systems become.
   For each: what is unknown, and what would change if it were answered. A question naming a
   capability the North Star does not ask for is imported, and dies at gate 3 like any other.

A system already at the ceiling its own North Star asks for gets told so, with reasons. Invented
praise and invented criticism cost the same.

## Verdict

One line, per `PROTOCOL.md` §5:

- `LENS: findings(gap: <phrase>, move: <phrase>, read: <fraction of the subject entered>)` — a gap survived all five Phase-2 gates and is grounded in named files.
- `LENS: clean(read: <fraction of the subject entered>)` — the system is at its own ceiling and no move outranks doing nothing.
- `LENS: blocked(<what would unblock it>)` — the source could not be read, or the North Star could not be established and the director has not stated one.

Never `done`. This skill measures and recommends; it makes nothing.
