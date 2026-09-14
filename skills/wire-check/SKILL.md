---
name: wire-check
description: >
  Verify a newly built tool/feature/module is actually connected end-to-end to its running system, not just written. Use when something "was built but isn't working", asks "is this hooked up?", suspects dead code, or after multi-file additions.
---

# Wire Check

> **The question:** Is it connected?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

"is it right?" → `correctness-gate`; "why is it wrong?" → `debug-protocol`; dead code with no new build behind it → `latent-audit`; a whole system with no component named → `reach-audit` (it runs this skill's method as a census). This skill answers one question only: is it connected?

Code that exists is not code that runs. This skill checks the whole chain, from where the system really starts to where the new component really has an effect — and when a link is broken, says *why* it broke, so the same kind of gap does not happen again. It exists because more and more code is generated, and generators are very good at writing components and very unreliable at connecting them.

## The job

Stated once; binding everywhere.

1. **Trace from the entry point inward.** Start where the system actually starts — the process launch, the route table, the event loop, the CLI dispatcher — and walk *towards* the new code. Never trace outwards from the new code: that only shows what the code *could* connect to, and misses the most common failure of all — a component that is complete, convincing, and never imported by anything.
2. **Work the chain out; never assume it.** You carry no recipe for any particular framework. Find out how *this* system registers components, routes requests, and calls things, by reading its code — whatever the language, framework, or year. A recipe written for today's frameworks dies with them; working it out yourself holds for frameworks that don't exist yet, and works better the smarter you are.
3. **Proven always beats traced.** Every verdict on every link carries a tag per `PROTOCOL.md`: **(proven)** — you ran something that showed the link working; **(trace-only)** — you followed it by reading. State the tag explicitly, and never let confidence from reading pass as something you observed. If running it is cheap and possible, trace-only is not an acceptable final answer.
4. **A broken link gets a cause, a fix, and a way to prevent it.** Report *which* link failed, *why* it was missed (the generator stopped early; the registration file was never edited; the naming convention quietly drifted), ship the code that connects it, and name the habit or check that stops this happening again.

## The Five Links

Every component in every system, whatever the stack, has to pass through these five states. They are what "being connected" means, not features of any one framework — which is why they don't go out of date:

| # | Link | Invariant | Typical break |
|---|------|-----------|---------------|
| 1 | **Exists** | The file is there, complete, and can be loaded | Empty stub bodies, half-written files, syntax errors |
| 2 | **Registered** | Whatever the system uses to find components knows about it | Missing import or export, absent from the manifest, config, or container |
| 3 | **Routed** | Some external trigger maps to it | Route, handler, or subscription never declared; name doesn't match the convention |
| 4 | **Invoked** | Real execution reaches it, with real arguments | A branch nothing takes, a feature flag left off, a caller passing the wrong shape |
| 5 | **Reachable** | Its effects land where they should (response, DB, file, event) | Result thrown away, error swallowed, side effect pointed at the wrong target |

Walk them **in order** and report the **first** broken link as the main finding — the later links cannot be checked until the earlier ones hold (mark those *blocked*, not *failed*).

## Procedure

### 1. Map the system

Find the real entry points and how this system does each link: how does *this* codebase find components, declare routes, dispatch calls, and produce effects? Build a small table — each component against where each of its five links should be declared — before checking anything. That table is the backbone of the report.

### 2. Walk the chain

For each link, get the cheapest evidence that settles it, working up this **ladder** and stopping at the first step this environment can actually run:

1. **Read it through** — follow the connecting code end to end (gives trace-only).
2. **Load it** — import, compile, or boot the relevant part; many breaks show up on load.
3. **Call it through the system** — invoke the component the way the system does, not by importing it directly, which skips the very wiring you are testing.
4. **Trigger it for real** — fire the actual external trigger (request, CLI command, event) and watch the real effect.

The rule is *the cheapest step you can actually run*, not *the highest one*: if step 4 is one command away, take it; if the environment cannot run the system, say so plainly and give the best read-only verdict, honestly tagged.

### 3. Verdict and repair

Report:

1. **Chain table** — the five links for each checked component, each with ✅/❌/⛔(blocked) and its (proven)/(trace-only) tag.
2. **First break** — the exact missing declaration, with the connecting code shipped in the same response.
3. **Why it was missed** — what the generator or the person did that left the gap. This is the line that makes the *next* build better.
4. **Prevention** — the check to add to the build loop (e.g., "every new handler PR must show the route table diff," or a one-line smoke command to run after generation).
5. **What's left uncertain** — anything still trace-only, and the one command that would make it proven.

End every run with a `WIRE` line (PROTOCOL §5); `clean` carries the §1 tag, a dead link is `findings(link N: cause)`.
