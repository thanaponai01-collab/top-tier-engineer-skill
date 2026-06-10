---
name: wire-check
description: Verify that a newly built tool, feature, module, or integration is actually connected end-to-end to its running system — not just written. Use whenever the user says something was built but isn't working, asks "is this hooked up?", wants to confirm a new component is live, suspects dead code, or just finished a build (especially via AI coding tools) and wants proof it's wired in. Also trigger after any multi-file feature addition when the user asks to verify, validate, or sanity-check the result.
---

# Wire Check

> **Wiring** — Service skill, callable from any stage. Invoked by `build-discipline` as the exit
> gate of every slice (its Phase 3), by `chief-engineer` on "is it hooked up?" requests, or
> standalone. Consumes: a component or slice plus its host system. Produces: the chain table and
> any connecting code, returned to the invoker. Distinct mandate: this skill asks *"is it
> connected?"* — `debug-protocol` asks *"why is it wrong?"*, `correctness-gate` asks *"is it
> right?"*. Shared vocabulary and laws: `PROTOCOL.md` at the suite root — authoritative when present.

Code that exists is not code that runs. This skill verifies the full chain from a system's real entry point to a new component's real effect — and when a link is broken, names *why* it broke so the same wiring failure never recurs. Built for the world where code is increasingly generated: generators are excellent at writing components and notoriously unreliable at connecting them.

## Operating Contract

Stated once; binding everywhere.

1. **Trace from the entry point inward.** Start where the system actually starts — the process launch, the route table, the event loop, the CLI dispatcher — and walk *toward* the new code. Never trace outward from the new code: outward tracing finds what the code *could* connect to and misses the most common failure class, the component that is complete, plausible, and never imported.
2. **Derive the chain, never assume it.** You carry no framework-specific recipe. Identify *this* system's actual registration mechanism, routing mechanism, and invocation mechanism by reading its code — whatever the language, framework, or year. A recipe written for today's frameworks dies with them; derivation works on frameworks that don't exist yet, and works better the smarter you are.
3. **Proven beats traced, always.** Every verdict on every link carries a tag per `PROTOCOL.md`: **(proven)** — you executed something that demonstrates the link live; **(trace-only)** — you followed it statically. State the tag explicitly; never let static confidence masquerade as empirical fact. If execution is cheap and available, trace-only is not an acceptable final answer.
4. **A broken link gets a cause, a fix, and a prevention.** Report *which* link failed, *why* it was missed (the generator stopped early; the registration file wasn't in the edit set; the naming convention silently diverged), ship the connecting code, and state the habit or check that prevents the class.

## The Five Links

Every component in every system, regardless of stack, must pass through these five invariant states. They are properties of "being connected," not properties of any framework — which is why they don't age:

| # | Link | Invariant | Typical break |
|---|------|-----------|---------------|
| 1 | **Exists** | The artifact is present, complete, and syntactically loadable | Stub bodies, half-written files, syntax errors |
| 2 | **Registered** | The system's discovery mechanism knows about it | Missing import/export, absent from manifest/config/DI container |
| 3 | **Routed** | A live path maps some external trigger to it | Route/handler/subscription never declared, name mismatch with convention |
| 4 | **Invoked** | Real control flow reaches it with real arguments | Dead branch, feature flag off, caller passes wrong shape |
| 5 | **Reachable** | Its effects land where intended (response, DB, file, event) | Result dropped, error swallowed, side effect pointed at wrong target |

Walk them **in order** and report the **first** broken link as the primary finding — downstream links are unverifiable until upstream ones hold (note them as *blocked*, not *failed*).

## Procedure

### 1. Map the system

Identify the true entry point(s) and the system's own mechanisms for each link: how does *this* codebase discover components, declare routes, dispatch calls, and emit effects? Build a small **cross-system reference table** — component ↔ where each of its five links should be declared — before checking anything. This table is the spine of the report.

### 2. Walk the chain

For each link, gather the cheapest sufficient evidence, escalating up the **reproduce ladder** and stopping at the first rung that is actually executable in this environment:

1. **Static trace** — read the wiring code end to end (yields trace-only).
2. **Load probe** — import/compile/boot the relevant slice; many breaks announce themselves at load.
3. **Direct invocation** — call the component through the system's own dispatch path (not by importing it directly — that bypasses the very wiring under test).
4. **End-to-end trigger** — fire the real external trigger (request, CLI command, event) and observe the real effect.

The rule is *cheapest executable rung*, not *highest rung*: if rung 4 is one command away, take it; if the environment can't run the system, say so explicitly and deliver the best static verdict honestly tagged.

### 3. Verdict and repair

Report:

1. **Chain table** — the five links for each checked component, each with ✅/❌/⛔(blocked) and its (proven)/(trace-only) tag.
2. **First break** — the exact missing declaration, with the connecting code shipped in the same response.
3. **Why it was missed** — the generative or human failure mode that produced the gap. This is the line that makes the *next* build better.
4. **Prevention** — the check to add to the build loop (e.g., "every new handler PR must show the route table diff," or a one-line smoke command to run after generation).
5. **Residual risk** — anything left trace-only and what single command would promote it to proven.

End every run with: `WIRE: connected(proven|trace-only) | broken(link N: cause) | blocked(environment)`.

## Why this skill improves as models improve

The five links are invariants of connectedness, not facts about frameworks. The contract demands deriving each system's mechanisms fresh and climbing the reproduce ladder as far as the environment allows. A stronger model reads stranger codebases, derives more exotic wiring mechanisms, and executes deeper reproductions — through this same file, unchanged.
