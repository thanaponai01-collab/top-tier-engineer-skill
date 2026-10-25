---
name: structure-gate
description: >-
  Measure complexity, nesting, length, import cycles and duplication, and say plainly whether it is spaghetti. Use for "is this code a mess?" or a CI check.
disable-model-invocation: true
metadata:
  stage: review
  card: "is it spaghetti, measured"
---

# Structure Gate

**Goal:** say plainly whether the code reads as spaghetti (yes, in places, no). Say where it is
tangled and what that costs the next person who changes it. Say how much of the code was
actually measured, and say it first: code no parser entered scores zero on every signal, so
unmeasured code looks clean unless you say it wasn't measured. How you read the code is up to you:
read all of it if it fits, run it, use any linter installed. The helper checks what counts as done.
`S` is `python <this skill's base directory>/scripts/structure.py`, run from the repo root.

`S <paths>` lists what it measured and what needs a note. Run `S --gate <paths>` whenever you like.
It says which stage is open and what fixes it, appends the slots it needs to
`.structure/notes.md`, and prints the answer once all three hold (`STRUCTURE-GATE: done`).

## The stages

| Stage | Holds when |
|---|---|
| **1. Measure** | `S --gate <paths>` found code under the paths and measured it: the share a parser entered (deep on Python; length and copies only for other languages), and every region it never entered, by `file:line` (code inside a string literal, a file that does not parse, a language with no parser here) |
| **2. Account** | Every such region, and every finding over threshold (tangled function, long file, import cycle, copied block), has a filled line in `.structure/notes.md`. For a region: `read: <what it holds, counted>`, or `unknown: <why>`. For a finding: `cost: <what it costs the next person who changes it>`, or `none: <why the shape is right>`. A note naming something not measured now fails |
| **3. Answer** | `- verdict: yes \| in places \| no` is one the measurement allows. `no` fails while any region is `unknown`, while any finding has a cost, or while code sits in a string or a file that does not parse: no linter or test can reach that anywhere. `yes` fails when nothing measured or noted says so |

Report only. Give the drafted answer with its `[[fill: ...]]` slots filled, measured share before
the first finding. Delete `.structure/` afterwards, or commit it with a change. To hold the shape in
CI, `scripts/structure-report.py --write-baseline FILE <paths>` freezes today's findings, and
`--baseline FILE` then exits 1 only on a new or worse one.
