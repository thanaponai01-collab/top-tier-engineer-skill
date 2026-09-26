---
name: explain
description: Teach a person what a thing in the codebase is, how it works and why it is built that way, in one plain account at their pace, changing nothing. Use for "explain how X works", "walk me through this", "teach me", "help me understand this system", "I don't get why it does that", or when someone is new to a codebase and needs to build a working picture.
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
assumption in a line: "I'll assume you know React but haven't seen this app."

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

*Test:* the person can say back what it is, how it works and why, and gets one new case right.

## 5. Stop

Do not propose changes, and do not fix what you noticed on the way. One line at the end if you
saw a real problem ("separately: the retry has no cap, at `queue.py:88`"). Work that follows from
understanding starts when they ask for it.

## Rules

- **Say how you know.** *Proven*, *traced* or *suspected* on anything a decision could rest on;
  say "I did not read this part" rather than smooth over it.
- **Their pace, not yours.** If they say it is too fast, go back a step with a smaller example.
- **No flattery, no filler.** "Great question" teaches nothing.

Finding the reason behind a decision is `code-history`; a map of what the system has is
`feature-map`. This skill stands without them: read the code, then follow the five steps.
