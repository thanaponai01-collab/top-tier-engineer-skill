---
name: explain
description: Teach a person how a part of the codebase works and why it is built that way, changing nothing. Use when someone asks to be walked through or taught a system or subsystem ("walk me through", "teach me", "help me understand this system", "I'm new to this codebase"). Not for a quick question about one line or function.
---

# Explain

The job is that the person **understands**, not that you show how much you found. Nothing gets
changed. An explanation that is correct but lands on nobody is a failed one, so the measure is what
the person can do afterwards, not what you said.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

## 1. Find where they are

Read the question for what they already know: their words, what they pointed at, what they tried.
If you cannot tell, ask one question ("what do you already know about this part, and what do you want
to do with it once you understand it?") and carry on with what it does not block. Say your
assumption in a line: "I'll assume you know React but haven't seen this app." No one there to
answer (an unattended run, or another skill asked): skip the question and state the assumption.

## 2. Learn it yourself first, from the code

Never explain from memory or from the name. Open the entry point and follow it to its effect: what
starts it, what it calls, what changes. If `FEATURES.md` exists, start from its `trace:` line. For
why it is built this way, get the reason from the records (`code-history`); with none, the honest
account is "no recorded reason", not a plausible story. Anything you will teach must be something you
opened or ran.

*Test:* each claim you plan to teach has a `file:line` behind it.

## 3. One account, in this order

1. **What it is**, in one sentence, in terms of what it does for someone, not what it is called.
2. **How it works**: the path, one step at a time, using their vocabulary. Follow one real
   example through with actual values ("a cart of two items arrives here, and this line totals it").
   Quote the few lines that carry the idea, each with `file:line`; never dump a file.
3. **Why it is this way**: the reason and what it was chosen over, with where you learned it, or
   that no reason is recorded.

Concrete before abstract. Introduce a term at the moment it is needed. One idea per step; when a
step needs three new things, it is two steps. Match length to the question: a small question gets a
paragraph. Offer the next layer ("want the part where it retries?") instead of giving it unasked. A
picture beats words for structure: draw it (`arch-map`), or a small ASCII one if that is not available.

## 4. Check it landed

Ask them to predict something the account did not cover: "what happens if the cart is empty?"
Compare their answer with the code, by reading it or running it. A wrong prediction means the model
is wrong, not the wording: correct the model with the case, do not repeat the sentence louder.

No one to answer: trace one case the account did not cover, and say what the code does there.

*Test:* the person can say back what it is, how it works and why, and gets one new case right.

## 5. Stop

Do not propose changes, and do not fix what you noticed on the way. One line at the end if you
saw a real problem ("separately: the retry has no cap, at `queue.py:88`"). Work that follows from
understanding starts when they ask for it.

## Overview mode

When the ask is a whole subsystem ("how does billing work?", "I'm joining the payments team"), give
an **overview** instead of the paced lesson: the mental model a senior engineer hands a new
teammate, enough to work in the area, not annotated source. Steps 1 and 2 still apply in full;
what changes is the shape of step 3 and that step 4 becomes an offer.

1. **What it is for**, in one sentence, and who or what calls it.
2. **The parts**, as many as the system really has (usually three to six), each as one line: what it
   owns and what it must never know. Draw it if there are more than three (`arch-map`).
3. **The main path**, followed once with a real example, with `file:line` on each hop.
4. **What is not obvious**: the invariant that holds it together, the shared assumption with no
   owner, the trap that catches newcomers, and what surprised you when you read it. Each with the
   `file:line` it sits on, or the record it came from (`code-history`).
5. **Where to look next** for the three most likely reasons to touch it.

Keep it to one screen. A file you would paste in is a sign you are narrating code; cut it to the
lines that carry the idea. Label anything a decision could rest on *proven*, *traced* or *suspected*.

**Nothing is saved.** The overview is written from the code on demand, so it cannot go stale
unnoticed; a saved one goes wrong the next time the code changes, with no check to say so. Save it
only when asked, and then pin it: `at: <short sha>` on the first line, and every claim keeps its
`file:line`. What is worth keeping already has an owner: what a system has is `FEATURES.md`
(`feature-map`), why it is that way is `WHY.md` (`code-history`). Start from `FEATURES.md` `trace:`
lines when they exist rather than re-tracing.

## Rules

- **Say how you know.** *Proven*, *traced* or *suspected* on anything a decision could rest on;
  say "I did not read this part" rather than smooth over it.
- **Their pace, not yours.** If they say it is too fast, go back a step with a smaller example.
- **No flattery, no filler.** "Great question" teaches nothing.

Finding the reason behind a decision is `code-history`; a map of what the system has is
`feature-map`. This skill stands without them: read the code, then follow the five steps.
