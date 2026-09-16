---
name: senior-review
description: Look at code or a project the way a senior engineer would and say what matters. Use for "is this code good?", "review this repo", "is it production-ready?", "what's the biggest gap / what should I fix next?".
---

# Senior Review

Ask the five questions a senior engineer asks when handed a project. Answer each in plain words,
with the file or command that shows it. You don't need to know the stack: read, trace, run.

## The five questions

1. **What is it for?** One sentence. Then the one or two things it must never get wrong ("a payment
   is never recorded twice"). Judge everything else against those.
2. **What breaks it?** Bad input, two things at once, a failure halfway, a restart. Try the cheap
   ones.
3. **What happens when it fails?** Is there a log, a clear error, a way to undo?
4. **Where would the next change land?** One file everything piles into, or one concern spread over
   five places, is where tomorrow's bugs come from.
5. **What's the biggest gap?** The one fix that improves the most else. Check git log first: it may
   have been tried and dropped for a reason.

*Test:* each of the five has an answer with a file or a command behind it. A question you skipped is reported as skipped, not left blank.

## Rules

- **Broken, not unfamiliar.** Broken loses data, races, leaks or lies. "Not how I'd do it" is a
  question, not a finding.
- **Causes, not symptoms.** Ten findings with one cause are one finding.
- **Rank by consequence:** data loss > security > wrong results > downtime > hard to change > style.
- Every finding names `file:line` and comes with the fix.

*Test:* for every finding you can name what breaks, for whom. If the answer is "nothing, but I'd write it differently", it is a question, not a finding.

## Report

First line: can it ship, and the single biggest issue. Then what's genuinely good, specifically.
Then one row per finding, worst first: `severity | finding (file:line) | why it matters | fix`.
End with the one habit that would have prevented most of them, and the one skill to run next on the
biggest gap: cause unknown → `debug-protocol`; structure or duplication → `arch-design` (audit);
slow → `perf-optimize`; abusable → `threat-model`; works but unproven → `correctness-gate`; written
but nothing calls it → `wire-check`; tangled, and you want it measured → `structure-gate`; dead
weight → `latent-audit`; requirements never pinned down → `problem-framing`.
