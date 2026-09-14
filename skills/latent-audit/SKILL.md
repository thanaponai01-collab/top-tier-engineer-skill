---
name: latent-audit
description: >
  Sweep an EXISTING codebase with NO felt symptom for dead weight, layer breaches, and dormant bugs. Use for "find dead code", "delete unused components", "check the layers are respected", "clean up the codebase", or "find real bugs".
---

# Latent Audit

> **The question:** With nothing visibly wrong, what is provably dead, in the wrong layer, or broken but not yet firing?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

a felt complaint ("slow", "clunky") → `symptom-audit`; observed wrong output → `debug-protocol`; "is this code wise/good?" → `senior-review`; "is it spaghetti?" (shape metrics) → `structure-gate`; a not-yet-landed delta → `scrutinize`; "what do we serve / what did I build that nothing ever calls" → `reach-audit`.

One principle, and everything else serves it: **code that nothing appears to reference is not
dead — it is (suspected) dead. Nothing is deleted until it is proven that nothing reaches it,
because deleting live code is the one mistake a director who cannot read code can neither see
coming nor work out afterwards.**

## The job

1. **The graph runs first, always.** `python3 tools/graph-audit.py <src> [--layers <spec>]`
   is the minimum for every audit. Its numbers are **(proven)** measurements of the import
   graph; its dead and unused lists are **(suspected)**, and the report says so in those words.
   An audit with no tool run in the transcript is not an audit — a rule nobody runs is not a rule,
   and this skill is where it gets run.
2. **Check layers against a written declaration, never against taste.** The layer order comes
   from `ARCHITECTURE.md` (copied into a `--layers` file and quoted in the report) or from the
   director. If there is no declaration, the report says "layers unchecked: no declared order" as
   a gap — never invent an order, never claim clean. A breach is **(proven)** — a real import at a
   real line — but what to *do* about it is the director's decision, routed through `arch-design`:
   fix the code, or change the declaration (Law 3: the breach may be holding something up).
3. **Nothing is deleted without proof that nothing reaches it.** A **(suspected)**-dead candidate
   moves up only by passing all three checks: (a) search every way something can be referenced —
   imports, names in strings, config keys, mentions in CLI or CI, templates, dynamic lookups
   (`getattr`, `import_module`, route tables, plugin registries); (b) check the entry points —
   could anything *outside* this tree call it, such as a cron job, a webhook, another service, or
   a person?; (c) if the code can be run here, run the test suite or a tracer and confirm the
   candidate is never loaded. All three pass → **(trace-only)** disconnected, and it can go on the
   deletion list. Any check you cannot finish → it stays **(suspected)** and is listed as *watch,
   do not delete*. There is no route from (suspected) to deleted.
4. **Deletions ship as small, reviewed, reversible changes.** Each entry on the list is one
   contained diff — the component, its dead tests, its dead config — with the proof attached,
   passed through `scrutinize` before `build-discipline` commits it on its own (one candidate per
   commit, so any mistake reverts in one step). Author ≠ reviewer (§6) applies: a list written this
   session is reviewed in a fresh context.
5. **Bugs you find along the way come with you; they do not set the route.** While tracing
   candidates and breaches, record anything broken you pass — leaked resources, error paths
   nothing handles, race conditions, strings built in a way that invites injection — with its
   file:line and an evidence tag, then send it to the skill that owns it (`debug-protocol` if it is
   provably wrong, `threat-model` if it is a security issue, `senior-review` if it is a judgment
   call). This skill never grows into a full review. A check that came back clean is also a
   finding, and is recorded as one.

## Procedure

1. **Ground yourself.** Read what the project already records (§3 — architecture, deferred work,
   past changes): a "dead" module may be work that was deliberately postponed. Check what can be
   run here, because that sets the limit: with no runtime, deletion proofs cap at **(trace-only)**,
   and the report says so in its first lines.
2. **Measure.** Run `graph-audit.py`; transcribe the declared layers if `ARCHITECTURE.md`
   states them. Paste the tool's verdict line into the report verbatim.
3. **Prove it or drop it.** Run the three checks from Rule 3 on every dead or unused candidate;
   whatever passes goes on the deletion list, the rest go on the watch list.
4. **Trace breaches.** For each layer breach, read the offending edge in execution order and
   state what it couples; frame the two remedies for the director.
5. **Report.** In the report itself — a file only when §3 warrants one: tool output, the deletion
   list with its proofs, the watch list, the breach table, anything found along the way with where
   it was sent, and the checks that came back clean. End with the verdict line.

## Verdict

One `LATENT` line per PROTOCOL §5 — `findings(dead: A, unused: B, layer-breaches: C)`. The noun is
also emitted by `tools/graph-audit.py`; the skill's line supersedes the tool's when the
three checks drop candidates (the count may only shrink from tool to skill, never grow — a count
that grew means somebody's judgment replaced a measurement).

## What this skill will not do

A felt symptom arrives mid-audit → the symptom comes first; reroute to `symptom-audit`. Asked "is this good code?" → `senior-review`. Asked for shape metrics →
`structure-gate` (its cycles and this skill's layer check read the same import graph but answer
different questions: *tangled* vs *pointing the wrong way*). Asked to judge a PR → `scrutinize`.
Asked what the system serves and what nothing reaches → `reach-audit` (its orphans and this
skill's dead list are not the same thing and do not hold the same members: *unreferenced* means
nothing points at it, *unreached* means no live path runs to it from an entry point — a module can
be one without being the other, and only this skill may turn either into a deletion). And it never
deletes anything itself — it produces the list; the deletion is a reviewed, built, gated change
like any other.

## Common mistakes

Deleting a module a cron job loads by name; "cleaning up" the things a plugin registry points at
because no import mentions them; calling the layers clean when no layers were ever declared; a
40-file "cleanup" commit nobody can revert; turning a dead-code sweep into a full review nobody
asked for; and the quiet one — handing over the tool's (suspected) list as if it were a list of
things safe to remove.
