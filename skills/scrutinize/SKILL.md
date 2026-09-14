---
name: scrutinize
description: >
  Outsider second opinion on a delta that has NOT landed yet — a PR, a diff, a plan, a design doc. Asks whether the change should exist, then traces the real code path to verify it does what it claims. Use for "scrutinize / sanity-check / second opinion on this PR, diff, or plan", or before a change costs a build. For a whole codebase, use senior-review instead.
---

# Scrutinize

> **The question:** Should this change exist, and does it do what it claims?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

for reviewing a whole codebase, or for teaching the author, use `senior-review` instead; this skill judges one change, not a codebase, and owes its author nothing.

Stand outside the change and ask whether it should exist at all, then check that it actually does
what it claims, end to end. The diff is where you start, never the limit of where you look.

## The job

- **An outsider, not a contrarian.** Take no confidence from the author, the PR description, or how
  well the plan is written — read it cold. But being an outsider does not make unfamiliar mean
  wrong: per Law 3, before flagging an odd choice, state the best reason a competent engineer might
  have had for it, and check the recorded decisions and assumptions first — a "surprise" the record
  already explains is history, not a finding. Until you can show it is wrong, an odd choice is a
  question in the report, never a finding. And when this same session wrote the change, being a
  real outsider takes fresh eyes (§6): run this skill in a fresh context with only the artifacts,
  or mark the report `(same-context review)`.
- **End to end, not just the changed lines.** Follow the calls through the real code paths,
  including the unchanged code on both sides of the diff — bugs hide where they meet.
- **What the change claims is a quote; what you conclude carries a tag.** "The PR says X" is a
  claim. "I followed X: …" is **(trace-only)**. "I ran X: …" is **(proven)**. Never let the first
  pass for one of the others — and if running it is one cheap command away, trace-only is not an
  acceptable final answer.
- **Say what to do, briefly, and why.** Every finding states what to change, why it matters, and
  the evidence that showed it. No filler, and don't read the diff back to its author.

## Steps — run in order, never skip ahead

### 1. Intent — should this exist at all?

- State the goal in one sentence, in your own words. If you cannot, the change is not specified
  well enough: stop, report `SCRUTINY: blocked(underspecified: what's missing)`, and send it to
  `problem-framing` for the missing criteria.
- Run the subtraction pass (meta-skills Discipline 7) on the whole change, top-down:
  1. **Do nothing** — is the problem real and does anything depend on it, or does it come from an
     assumption that stopped being true?
  2. **Reuse** — does something in this codebase already do this? Anything new needs a reason.
  3. **Shrink** — is there a change that gets 90% of the goal for 10% of the risk?
  4. **Move it** — does this belong somewhere else (config instead of code, the framework instead of
     the app, build time instead of run time)?
- A better alternative, named and argued, is the most valuable thing this skill can produce — say
  it *before* any line-by-line work, at the top of the report.

### 2. Trace — walk the real path

- For each behavior the delta claims, trace end-to-end through the actual code: entry point →
  call sites → branches taken → state mutated → exit, return, or side effect.
- For a plan or design doc: trace the proposed flow against the existing system. Every assumption
  the plan makes that the code does not support is a finding; tag what the plan never checked as
  **(assumed)** and log it.
- Note every place the trace surprises you — a branch you did not expect, dead code being reached,
  state you did not know existed. Once you have checked the recorded decisions, whatever still
  surprises you is worth reporting.

### 3. Verify — does it do what it claims?

For each claim, in this exact shape: *"Claims X. Path: A → B → C. At C, [observation] (tag).
Therefore holds / does not hold."* Then attack:

- **Breaking inputs and states** — empty, null, unicode, huge, concurrent callers, error paths,
  partial failure, retries, ordering assumptions.
- **Things it changes without saying so** — performance, what errors now mean, what is visible in
  logs, the contract other callers rely on, stored or transmitted formats. A change is responsible
  for everything it changes, not only what it mentions.
- **The tests** — do they actually run the path you traced, or go around it (mocks covering the
  join, assertions on intermediate state, happy path only)? A green test that skips the path you
  traced is itself a finding.
- Move from reading to running wherever it is cheap: run the test, send the request, import the
  module.

### 4. Report

Shape and wording: `PROTOCOL.md` §9. If a simpler alternative survived step 1, it leads.

One row per finding, ordered by consequence (blocker → major → minor; scale per `senior-review`
Rule 6). Columns: the finding in one sentence, with `file:line`; why it matters — the consequence,
not the principle; the evidence — the trace step, input, or command that showed it, with its tag;
and the change, specific and as small as possible. Per Law 5, a small fix ships as corrected lines
under `Detail`, never as an exercise for the reader.

**Verdict noun:** `SCRUTINY`

End every run with a `SCRUTINY` line (PROTOCOL §5). This skill judges one delta and makes nothing,
so it never says `done` — a fix it ships under Law 5 closes separately, with its own `FIX` line
(§7). `clean(traced: <what you followed>, ran: <what you executed>)` — never a bare `clean`, per
the no-rubber-stamps rule below; `findings(top: <finding>, count: K)`;
`blocked(underspecified: <what is missing>)` when step 1 could not state the goal.

## Rules

- **No rubber stamps.** "LGTM" is not an answer. A clean pass lists what you traced and what you
  ran, so the reader can judge whether it covered the part they care about.
- **Cite it or it didn't happen.** Every claim about the code names a path, file, line, or command.
  "Might break under load" with no mechanism is **(suspected)** at best, and says so.
- **Step 1 is not optional**, even for small changes — skip it only if the user explicitly says
  "don't question the scope", and then say in the report that it was skipped.
- **Structure beats nitpicks.** If step 1 or 2 finds a structural problem, lead with it and drop
  the small stuff; polishing a change that should not exist is the mistake to avoid.
- **No flattery, no hedging.** Teaching and earned praise belong in `senior-review`; this report
  serves whoever has to live with the change.
