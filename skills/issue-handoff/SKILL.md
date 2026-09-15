---
name: issue-handoff
description: Turn a document of planned work into tracked issues without losing what made it buildable. Use for "file these as issues", "put this in GitHub", "make issues from this doc / from the audit / from the plan", or picking up a moves file written in another session.
---

# Issue Handoff

A document is a queue nobody opens. An issue reaches the person on a machine they weren't sitting at
when it was written. This skill moves work across that gap and leaves nothing buildable behind.

**You copy, you never compose.** Re-describing a planned change in tidier words is where the
evidence, the proof line and the ordering die. The source block is the issue body.

You are invoked to file, so filing needs no further permission. What needs care is *what* gets
filed: a public issue is awkward to take back, and a thin one is worse than none.

## 1. Read the source, whole

Read the document end to end before writing anything, even if you wrote it yourself earlier. File
from the document, never from memory of the conversation that produced it — the conversation is the
thing that isn't there next week.

Find the **unit**: the smallest thing that lands and reverts on its own. A document already in
blocks (an audit's moves, a spec's requirements) hands you the units. Prose hands you nothing: split
it yourself, and say how you split it.

## 2. Lift what's shared

Assumptions written once at the top — "the auth model stays", "this is all behind the new flag",
the link back to the report — are true of every item and present in none of them once they're
separate issues. This is the first thing a handoff loses.

Collect them into a short **Context** block and prepend it to **every** body. Repetition across
issues is correct here; each issue must stand alone.

## 3. Check each item for the five losses

An issue body must answer all five from itself, without the reader opening the source:

| | Without it |
|---|---|
| **What changes**, in one line | nobody knows when it's done |
| **Why** — what it costs today | it gets deprioritised forever, or done after it stopped mattering |
| **Where** — paths with line numbers | the evidence is found again from scratch |
| **Proof** — the command, and the output that counts as success | "done" becomes an opinion |
| **Order** — what must land first | moves land in an order that breaks the middle ones |

Missing a field? Open the code and fill it **now**, while you're still here — that is cheaper than
it will ever be again. Can't fill it? **Don't file that item.** Say which and why. An issue reading
"clean up the date helpers" is a note, not work, and it will sit open for a year.

## 4. Reconcile before you create

```
gh issue list --label <label> --state all --json number,title,body
```

Match each item against what exists: first by the number stamped in the source, then by title.
Already filed → update it or leave it, never a second copy. A re-run of the audit that doubles the
backlog is the failure this step exists to stop.

## 5. Create, one per unit

- `gh issue create --title "…" --body-file <path> --label <label>`. Always `--body-file`; passing
  markdown through `--body` on a shell mangles backticks, quotes and newlines silently.
- File in dependency order so prerequisites get lower numbers, then write `Blocked by #N` into the
  bodies that need it.
- **Stamp the number back into the source document** (`issue: #12`) as you go, not at the end — an
  interrupted run must leave the two sides agreeing.
- One label for the batch, so both of you can list them again.

No `gh`, no remote, or no tracker: stop and say so in one line. The document stays the queue, and
nobody should be left assuming issues exist.

## Report

One line: how many filed, where, and the label to list them with. Then a row per item:
`item | issue | created / updated / skipped / held | why, if held`. Held items are the point of the
report — they're the work that silently vanishes in a careless handoff.

## Common mistakes

Summarising a block into a tidy one-liner; filing the clean items and quietly dropping the ones
missing a proof line; filing from the conversation instead of the document; second copies on a
re-run; shared assumptions left in the preamble and carried into no issue; `--body` eating the
formatting; stamping numbers back only at the end, so a crash leaves two disagreeing lists.
