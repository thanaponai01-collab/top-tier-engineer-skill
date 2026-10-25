---
name: threat-model
description: >-
  Find what an attacker can make a system do, and turn each abuse into a test. Use for auth, secrets, untrusted input, "is this secure?", "can this be abused?"
disable-model-invocation: true
metadata:
  stage: design
  card: "can this be abused?"
---

# Threat Model

**Goal:** say what an attacker (a signed-up account, or anyone) can make the system do today,
worst first. Every way in is either attacked or shown to have nothing behind it, and every attack is
left behind as a test the project's suite runs, so a later change that reopens a door turns the suite
red. Never claim it is secure: claim which attacks were run and how each came out. How you find the
abuses is yours: read it all if it fits, probe it, think like the attacker. What counts as done is
checked by the helper. `T` is `python <this skill's base directory>/scripts/threat.py <repo>`.

`T` lists the doors it found. Run `T --gate` whenever you like; it says which stage is open and what
fixes it, and prints the answer once all three hold (`THREAT-GATE: done`).

## The stages

| Stage | Holds when |
|---|---|
| **1. Doors** | The scan found the ways in: functions in a route table, behind a registering decorator, handler methods, `__main__` blocks. Code it cannot parse is listed too. A door it misses is named with `--door FILE::FUNC` |
| **2. Attack** | Every door is entered by a recorded attack, or has `- DOOR: out: <why an attacker gains nothing>` in `.threat/doors.md` (the gate appends the slots). An attack is a test that passes only when the abuse is refused, in a `tests/test_*.py` file: `T --attack "<cmd naming that test>" --door FILE::FUNC --gets "<what the attacker gets>"`. It runs in a throwaway copy under a call tracer and is refused if it never enters the door, runs no tests, or crashes instead of failing an assertion. `out:` is refused when the reason leans on a defense: a defense you read about is what an attack has to prove |
| **3. Hold** | Every attack reruns as recorded. After a fix, each attack passes now, and each one that was open fails again with the changed files put back |

Fix only when asked. Fix where the decision really belongs, and keep the owner's own path working.
A secret found in source is reported by location and kind, never pasted, with "rotate it" as the fix.
Report the drafted answer with its `[[fill: ...]]` slots filled. Keep the attack tests; delete
`.threat/` afterwards, or commit it with a fix.
