---
name: plan-work
description: >-
  Cut work into ordered slices, each with a runnable check, and say which can run in parallel. Use for "plan this", "break this down".
metadata:
  stage: plan
  card: "split work into ordered, checked slices"
---

# Plan Work

Between "we know what done is" and the first line of code sits a step nobody owns: cutting the work
into pieces, in an order, each with a way to tell it is finished. Skipped, the pieces are found by
trial, two agents edit the same function, and "done" means each of them said so. This skill ends in
one file, `PLAN.md`. `build-discipline` builds from it a slice at a time, and hands a slice to
another agent from it.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

## Steps

1. **Start from the exit check.** The goal's brief (`problem-framing` writes `BRIEF.md`) and the
   check that says the whole goal is met (`verify-loop`). Without them, write the exit check
   yourself as a command plus the output that counts. A plan with no exit check plans toward
   nothing.

2. **Cut into slices.** A slice is the smallest piece that can be shown working from a real entry
   point. One row each: `slice | files it will touch | check | depends on`. The check is a command
   and the output that counts as success, with the expected value worked out before the work
   starts, from the spec or by hand ("subtotal 10000, 10% off, Thai tax → 9630"), never read off
   the code. "Add tests" is not a check.

3. **Order by risk, then by dependency.** The slice most likely to prove the plan wrong (an API you
   have not called, data that may not exist, a speed question) goes first, as a spike whose check
   answers one question. Then whatever the others stand on.

4. **Mark what can run together.** Two slices may run at the same time only if all three hold: they
   touch different files; they share no function, schema or config key whose meaning either changes;
   neither reads what the other writes. Open the shared code and its callers before saying so; a
   mark from the descriptions alone is *suspected*. A shared piece becomes its own first slice, or
   one owner takes both. Two rules that both change one calculation are a shared piece: the order
   they apply in is settled in one sentence before either starts.

5. **Write `PLAN.md`:** the table, one line on what runs together and why, and the integration check
   (the exit check from step 1, run after every merge).

6. **Hand work out only when it pays.** At least two slices that can run together, each bigger than
   the brief it takes to hand over. A brief stands alone: the goal, the slice's check, the files it
   may touch and the ones it must not, an attempt budget, and its own branch or worktree. The report
   it owes back is the command and its pasted output.

7. **Take it back one at a time.** A report is a claim: rerun the slice's check yourself on its
   branch. Merge in plan order, and after each merge run the whole integration check, not the
   slice's own. A slice that was green alone and red after a merge means the "can run together"
   mark was wrong: fix the mark in `PLAN.md`, then the code.

*Test:* every slice has a command and an expected result written before it starts, and every "can
run together" claim names the files and functions you opened to check it.

## Report

Answer first: how many slices, which can run together and which cannot, and why. Then the table.
End with what you did not check.

## Common mistakes

Calling pieces independent because their titles differ; a check that is "the tests pass"; the
risky unknown left for last; handing out a slice whose brief costs more than the slice; trusting a
subagent's "done" and merging everything at once; running only each slice's own check after the
merge.

## Next

Building a slice: `build-discipline`. Filing the slices as tracked issues: `issue-handoff`.
Running the plan with nobody there: `drive-overnight`. Without `problem-framing` or `verify-loop`
loaded, step 1 is done by hand as written.

Project memory: retrieve missing facts with `project-context`; after authorized changes use
`project-update` for affected records. Without helpers, follow/update existing notes directly;
read-only reviews report gaps. Skip upkeep when no durable fact changed.
