---
name: latent-audit
description: >
  Sweep an EXISTING codebase with NO felt symptom for the three latent defect
  classes a director cannot see: dead weight (modules and functions nothing
  uses — candidates for deletion), layer breaches (code that imports against
  the declared architecture direction), and dormant bugs (defects on paths
  that happen not to hurt yet). Use whenever the user asks to "find dead
  code", "delete unused components", "check the layers are respected", "clean
  up the codebase", or "find real bugs" with nothing currently felt as wrong.
  Boundaries: a felt complaint ("slow", "clunky") → symptom-audit; observed
  wrong output → debug-protocol; "is this code wise/good?" → senior-review;
  "is it spaghetti?" (shape metrics) → structure-gate; a not-yet-landed
  delta → scrutinize. This skill hunts what nobody has felt yet.
---

# Latent Audit

> **Wiring** — Diagnostic sibling of `symptom-audit`: that skill traces a *felt* complaint;
> this one hunts *unfelt* defects. Mandate within the suite: `structure-gate` asks *"what is
> its measured shape?"*; `senior-review` asks *"is it wise?"*; this skill asks **"what in
> this codebase is provably dead, mislayered, or dormantly broken — with no symptom to guide
> the search?"** Consumes: an existing codebase (+ `ARCHITECTURE.md` and ledgers, read
> first). Mechanical invoker: `tools/graph-audit.py` (Law: prose enforcement is not
> enforcement — the graph pass is never skipped, never hand-simulated). Produces:
> `LATENT_REPORT.md` — findings plus the **deletion manifest**. Hands off: each deletion →
> `scrutinize` (a deletion is a delta) then `build-discipline`; layer breaches →
> `arch-design` (fix the code to the declaration, or the declaration to reality — a director
> decision); dormant bugs found broken → `debug-protocol`; security-shaped findings →
> `threat-model`. Shared vocabulary and laws: `PROTOCOL.md` at the suite root —
> authoritative when present. (Gloss: **(proven)** executed · **(trace-only)** read, chain
> complete · **(suspected)** chain incomplete, flag only · **(assumed)** unverified premise.)

One principle, everything else serves it: **statically unreferenced is not dead — it is
(suspected) dead. Nothing is deleted until its disconnection is proven, because deleting
live code is the one mistake a director who cannot read code can neither see coming nor
diagnose after.**

## Operating contract

1. **The graph runs first, always.** `python3 tools/graph-audit.py <src> [--layers <spec>]`
   is the floor of every audit. Its numbers are **(proven)** measurements of the import
   graph; its dead/unused lists are **(suspected)** and the report says so in those words.
   An audit whose transcript shows no tool invocation is not an audit (Law: a rule with no
   invoker is not enforced — this skill is the invoker's owner).
2. **Layers are checked against a declaration, never against taste.** The layer spec comes
   from `ARCHITECTURE.md` (transcribed into a `--layers` file, quoted in the report) or
   from the director. No declaration → the report states "layers unchecked: no declared
   order" as a gap; it never invents an ordering and never claims clean. A breach is
   **(proven)** — a real import edge at a real line — but the *remedy* is a director
   decision routed through `arch-design`: fix the code, or amend the declaration
   (Chesterton's Fence, Law 3: the breach may be load-bearing).
3. **Deletion requires a disconnection proof.** A **(suspected)**-dead candidate is
   promoted only by the proof ritual: (a) sweep every reference form — imports, string
   names, config keys, CLI/CI mentions, templates, reflection patterns (`getattr`,
   `import_module`, route tables, plugin registries); (b) audit entry points — could
   anything *outside* the tree (cron, webhook, another service, a human) call it?;
   (c) if the environment can execute, run the suite/tracer and confirm the candidate is
   never loaded. All three pass → **(trace-only)** disconnected, eligible for the deletion
   manifest. Any step unfinishable → stays **(suspected)**, listed as *watch, do not
   delete*. There is no path from (suspected) to deleted.
4. **Deletions ship as reversible, scrutinized deltas.** Each manifest entry is one
   bounded diff — the component, its dead tests, its dead config — with the disconnection
   proof attached, routed through `scrutinize` before `build-discipline` lands it in its
   own commit (one candidate per commit, so any mistake reverts in one step). Author ≠
   reviewer (PROTOCOL §8) applies: the scrutiny of a same-session manifest is fresh-context.
5. **Dormant bugs ride the sweep; they do not steer it.** While tracing candidates and
   breaches, defects encountered on the way (resource leaks, unhandled error paths, race
   patterns, injection-shaped string building) are recorded with file:line and an evidence
   tag — then routed to their owners (`debug-protocol` if provably wrong, `threat-model`
   if security-shaped, `senior-review` if a judgment call). This skill never expands into
   a full review; a clean check is also a finding and is recorded as one.

## Procedure

1. **Ground.** Read ledgers if present (`ARCHITECTURE.md`, `TODO_LEDGER.md`, `MAINT_LOG.md`
   — a "dead" module may be a documented deferment). Executability census sets the ceiling:
   no runtime → deletion proofs cap at **(trace-only)** and the report's first lines say so.
2. **Measure.** Run `graph-audit.py`; transcribe the declared layers if `ARCHITECTURE.md`
   states them. Paste the tool's verdict line into the report verbatim.
3. **Prove or demote.** Run the Rule-3 disconnection ritual on every dead/unused candidate;
   sort survivors into the deletion manifest, the rest into the watch list.
4. **Trace breaches.** For each layer breach, read the offending edge in execution order and
   state what it couples; frame the two remedies for the director.
5. **Report.** Write `LATENT_REPORT.md`: tool output, manifest (with proofs), watch list,
   breach table, ride-along findings with routes, clean checks. End with the verdict line.

## Verdict

`LATENT: clean(N modules traced) | findings(dead: A, unused: B, layer-breaches: C) |
blocked(no analyzable source)` — one line, machine-parseable, per PROTOCOL §5. The noun is
also emitted by `tools/graph-audit.py`; the skill's line supersedes the tool's when the
disconnection ritual demotes candidates (counts may only shrink from tool to skill, never
grow — a growing count means judgment was substituted for measurement).

## Boundary — what this skill refuses

A felt symptom arrives mid-audit → the symptom outranks the sweep; reroute to
`symptom-audit`. Asked "is this good code?" → `senior-review`. Asked for shape metrics →
`structure-gate` (its cycles and this skill's layer check share the import graph but answer
different questions: *tangled* vs *pointed the wrong way*). Asked to judge a PR →
`scrutinize`. And it never deletes anything itself — it produces the manifest; the deletion
is a scrutinized, built, gated change like any other.

## Failure modes this contract exists to prevent

Deleting a module that a cron job loads by string name; "cleaning up" a plugin registry's
targets because no import touches them; declaring layers clean when no layers were ever
declared; a 40-file "cleanup" commit nobody can revert; expanding a dead-code sweep into an
unrequested full review; and the quiet one — reporting the tool's (suspected) list as if it
were a list of things safe to remove.
