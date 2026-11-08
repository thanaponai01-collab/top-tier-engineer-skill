---
name: threat-model
description: >-
  Find what an attacker can make a system do, prove each abuse by running it, and keep each one as a test. Use for auth, secrets, untrusted input, "is this secure?", "can this be abused?"
disable-model-invocation: true
metadata:
  stage: design
  card: "can this be abused?"
---

# Threat Model

Say what an attacker can make the system do today, worst first: someone with a signed-up account,
or anyone at all. Every claim comes from an attack that was run, not from reading the code. Never
call the system secure; say which attacks were run and how each came out. How you find the abuses
is up to you: read it all if it fits, probe it, think like the attacker.

**What done looks like**

- Every way in is on the list: routes, handlers, registered plugins, scripts, jobs, a second door to
  the same data. Each one is either attacked or given a reason an attacker gains nothing through it.
- Each attack was run and came out open (the abuse works) or blocked. It is kept as a test in the
  project's own suite that passes only when the abuse is refused, so a later change that reopens the
  door turns the suite red. Open ones are marked so the suite's red is expected, not a surprise.
- An attack really goes through the door it names: it reaches the handler the way an attacker
  would, not a helper or a wrapped name the real route never calls.
- Fix only when asked. Fix where the decision belongs, keep the owner's own path working, and show
  each fixed attack passing now and failing again with the fix taken back out.

**Avoid**

- Calling a door safe because of a guard you read about. A defense is what an attack has to prove:
  a decorator, a check or a role filter that looks applied may never reach the route.
- An attack that crashes, runs no test, or lives outside the repo and is deleted after. A probe
  nobody keeps protects nothing.
- Pasting a secret found in the source. Name its file:line and kind; the fix is to rotate it.
- Ranking by how clever the attack is. Rank by what the attacker gets.

**The answer**

```
Attacker: <who: anyone / signed-up account / staff / ...>
1. <door: file::function> — <what the attacker gets>: open | blocked | fixed
   Attack: `<test command>` (<file:line of the kept test>)
   (one per attack, worst first)
No attack: <door>: <why an attacker gains nothing through it>     (one per door)
Secrets: <file:line, kind: rotate it>                             (or: none found)
Fixed: <door>: <change>; the attack passes now and fails with the change taken out   (or: not asked)
Not attacked: <doors, services or configs no run here reached>
```
