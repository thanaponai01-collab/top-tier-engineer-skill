---
name: issue-handoff
description: Turn planned work — a document, or something said in the chat — into tracked issues without losing what made it buildable. Use for "file these as issues", "put this in GitHub", "open an issue for this bug", "make issues from this doc / from the audit / from the plan", or picking up a moves file written in another session.
---

# Issue Handoff

A document is a queue nobody opens, and a chat is a queue that closes when the window does. An
issue reaches the person on a machine they weren't sitting at when it was written. This skill moves
work across that gap and leaves nothing buildable behind.

**You copy, you never compose.** Re-describing a planned change in tidier words is where the
evidence, the proof line and the ordering die. The source block is the issue body.

You are invoked to file, so filing needs no further permission. What needs care is *what* gets
filed: a public issue is awkward to take back, and a thin one is worse than none.

## 1. Read the source, whole

The source is either a document or the chat itself. Both are filed the same way from step 2 on; they
differ only in where the words come from and what you do with the issue number.

**From a document.** Read it end to end before writing anything, even if you wrote it yourself
earlier. File from the document, never from memory of the conversation that produced it — the
conversation is the thing that isn't there next week.

**From the chat.** Often there is no document: a bug just got described, or a couple of moves came
out of the last half hour. Then the conversation *is* the source, and it is the one that vanishes —
so file it now rather than writing a document first. Scroll back and take the user's own words for
what changes and why; those are the source block, quoted, the same as a document's would be. What
you inferred, decided or half-fixed along the way is not the source: anything you're carrying in
your head has to be checked against the code before it goes in a body, or it doesn't go in.

Find the **unit**: the smallest thing that lands and reverts on its own. A document already in
blocks (an audit's moves, a spec's requirements) hands you the units. Prose and chat hand you
nothing: split it yourself, and say how you split it.

A chat source has one advantage a document doesn't — the person who wrote it is still here. Before
creating, put the split and the titles in front of them in one line each and wait. That costs a
message now; a wrong public issue costs an awkward close later.

## 2. Lift what's shared

Assumptions written once at the top — "the auth model stays", "this is all behind the new flag",
the link back to the report — are true of every item and present in none of them once they're
separate issues. This is the first thing a handoff loses.

Collect them into a short **Context** block and prepend it to **every** body. Repetition across
issues is correct here; each issue must stand alone.

## 3. Check each item for the five losses

An issue body must answer all five from itself, without the reader opening the source:

*Test:* a reader could act on any one body without opening the source.

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
  interrupted run must leave the two sides agreeing. Filing from the chat, there is nothing to stamp:
  print each number as it's created, so an interrupted run still leaves the numbers somewhere.
- One label for the batch, so both of you can list them again.

*Test:* stop the run at any point and the two sides still agree about what was filed.

No `gh`, no remote, or no tracker: stop and say so in one line, with the bodies you'd built. The
source stays the queue, and nobody should be left assuming issues exist.

## Report

One line: how many filed, where, and the label to list them with. Then a row per item:
`item | issue | created / updated / skipped / held | why, if held`. Held items are the point of the
report — they're the work that silently vanishes in a careless handoff.

## Common mistakes

Summarising a block into a tidy one-liner; filing the clean items and quietly dropping the ones
missing a proof line; filing from the conversation when a document exists, or writing a document
first when the conversation is all there is; filing what you concluded in the chat rather than what
the user said and the code shows; second copies on a re-run; shared assumptions left in the preamble and carried into no issue; `--body` eating the
formatting; stamping numbers back only at the end, so a crash leaves two disagreeing lists.
