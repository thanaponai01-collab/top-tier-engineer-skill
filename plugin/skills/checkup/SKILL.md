---
name: checkup
description: >-
  One report on how well a codebase is structured, and what to fix first, ranked by where changes land. Use for "is this codebase well structured?", "give it a checkup", "what should we fix first?"
disable-model-invocation: true
metadata:
  stage: review
  card: "how well structured is it, and what first?"
---

# Checkup

**Goal:** say how well structured the codebase is, property by property, and name the three
things to fix first: the ones that cost the next change, not the ones that look worst. A tangled
function nobody changes costs less than two files that keep changing together with nothing
linking them. Say what was measured before any finding: a section nothing measured is
`not checked`, never clean. How you read the code behind a finding is up to you. What counts as
done is checked by the helper. `C` is `python <this skill's base directory>/scripts/checkup.py <repo>`;
it needs git.

`C` alone runs the sibling helpers that are installed (structure-gate, latent-audit, arch-design,
feature-map) over the git-tracked files and prints one report in eight sections: easy to find
things, one change in one place, dependencies point one way, deep modules, one way per job, logic
apart from I/O, no dead code, tests that can fail. Each finding has a weight: commits plus twice
the fix commits of its files in the last 300 (for a pair, only the commits that touched both). A
finding no commit in the last 100 touched is `idle`. Run `C --gate` whenever you like. It says
which stage is open and what fixes it, appends the slots it needs to `.checkup/notes.md`, and
prints the answer once all four hold (`CHECKUP-GATE: done`). The report is reused while the
tracked files are the same, so rerunning the gate after editing only the notes is cheap.

## The stages

| Stage | Holds when |
|---|---|
| **1. Measure** | The report is current with the tracked files and at least one code file is tracked. It opens with what was measured: files, history, each helper's status, every region no parser entered, and findings dropped because they sit in untracked or ignored paths |
| **2. Account** | Going down by weight, each finding has `- <id>: cost: <commits that show what it costs>` or `- <id>: none: <why the shape is right>` under `## account`, until three have no `none:` (or twelve were looked at). A `none:` hands its slot to the next finding. A cost cites a commit that touched the finding's files. An idle finding's cost can be `cost: next: <the coming change it will slow down>`. Add a line for any other finding you want in the top three. A line naming a finding the report does not hold fails |
| **3. Read** | Under `## read`, each file the report lists to read (the eight non-test code files changes land in most) has `- <path>: risk: <name>(): <what can go wrong>` or `- <path>: nothing: <name>(): <what it does>`, where `<name>` is in that file. This is for what no section measures: a wrong result, a retry that can repeat a payment, a missing check. Every `risk:` is printed in the answer, before the fixes |
| **4. Answer** | Under `## answer`, each section is `good`, `in places`, `poor` or `not checked`, as the measurement allows: `not checked` only where nothing measured it, `good` not while a finding in it has a cost, `poor` only with one that does. `- fix 1:` to `- fix 3:` are the findings with a cost, highest weight first |

Read the commits behind a finding before you write its cost: a pair that changes together by
design (a version written in two manifests) is a cost if it ever drifted, `none:` if it never can.
"Tests that can fail" is never measured here; verify-loop does that by running the tests against
broken code.

Report only. Give the answer the gate prints, and for each fix the skill that does it, when it is
installed (untangle, arch-design, latent-audit, cleanup, feature-map). Delete `.checkup/`
afterwards, or commit it with a change.
