---
name: senior-review
description: Look at code or a project the way a senior engineer would and say what matters. Use for "is this code good?", "review this repo", "is it production-ready?", "what's the biggest gap / what should I fix next?".
---

# Senior Review

Ask the five questions a senior engineer asks when handed a project. You don't need to know the
stack: read, trace, run. What separates this from an opinion is that every answer carries the file
you opened, the command you ran, or the output you pasted.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

## Non-negotiables

1. **Say what you read, before what you found.** Name roughly how much of the project you actually
   opened and what you deliberately left out. A review that reads a tenth of a repo and reports as
   though it read all of it is the most common way this skill lies.
2. **Question 2 is run, not imagined.** At least two breakages actually attempted, output pasted.
   "It would probably fail on empty input" is a guess wearing a finding's clothes.
3. **An answer with nothing behind it is reported as unanswered.** Five confident paragraphs and no
   evidence is the failure this skill exists to stop.
4. **Praise is a claim too.** "Well structured" with no file behind it is filler: name the file or
   cut the line.

*Test:* the report opens with what you read and what you skipped, and contains pasted output from at least two attempted breakages.

## The five questions

1. **What is it for?** One sentence. Then the one or two things it must never get wrong ("a payment
   is never recorded twice"). Take these from the README, the tests, or the user — not from your
   own impression of the code. Everything below is judged against them.
2. **What breaks it?** Attempt them, cheapest first: empty input, oversized input, malformed input,
   two callers at once, a kill halfway through, a restart. Paste what happened for each one you
   ran, including the ones that held — a defense that survived is a finding too. Nothing can run
   here? Say so in the first line of the report and mark every answer below *traced*.
3. **What happens when it fails?** Trigger one real failure and read what the user and the operator
   actually see: the message, the log line, the state left behind. Then: is there a way to undo it?
4. **Where would the next change land?** One file everything piles into, or one concern spread
   across five places, is where tomorrow's bugs come from. Name the file and its length, or name
   the five places.
5. **What's the biggest gap?** The one fix that improves the most else. Search the history first
   (`git log`, and `git log -S` for the thing itself): name the commit where it was tried and
   dropped, or say plainly that the history shows no attempt.

*Test:* each of the five names a file, a command, or pasted output. One that doesn't is listed as unanswered, not left blank.

## Rules

- **Broken, not unfamiliar.** Broken loses data, races, leaks or lies. "Not how I'd do it" is a
  question, not a finding.
- **Causes, not symptoms.** Ten findings with one cause are one finding.
- **Rank by consequence:** data loss > security > wrong results > downtime > hard to change > style.
- Every finding names `file:line` and comes with the fix.

*Test:* for every finding you can name what breaks, for whom. If the answer is "nothing, but I'd write it differently", it is a question, not a finding.

## Report

First line: can it ship, and the single biggest issue. Second line: what you read and what you
skipped. Then what's genuinely good, with the file that shows it. Then one row per finding, worst
first: `severity | finding (file:line) | why it matters | proven / traced / suspected | fix`.

End with the one habit that would have prevented most of them, and the one skill to run next on the
biggest gap: cause unknown → `debug-protocol`; structure or duplication → `arch-design` (audit);
slow → `perf-optimize`; abusable → `threat-model`; works but unproven → `correctness-gate`; written
but nothing calls it → `wire-check`; tangled, and you want it measured → `structure-gate`; dead
weight → `latent-audit`; requirements never pinned down → `problem-framing`.
