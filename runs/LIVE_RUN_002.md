# LIVE_RUN_002 — Tier-Memory (18k-LOC agent memory system)

**Target:** `Tier-Memory` — a real, self-improving agent memory system (~18,300 LOC Python):
asyncio daemon, SQLite (WAL) + HNSW vector index, 4-stage compression pipeline, hybrid retrieval
(vector + graph + BM25 + RRF), a learned reranker, MCP server, Obsidian bridge. This is ~10× the
size of LIVE_RUN_001's target and architecturally serious.

**Why this run matters:** the repo already carries a `REVIEW_LEDGER.md` written *in the suite's own
vocabulary* (unproven bets, confirmed-worse triggers, Chesterton's-Fence discipline). The codebase
has been developed *with* the suite. That makes this the hardest possible test — the cheap findings
are already gone, and the author is demonstrably disciplined. A review that found nothing would be
honest; a review that manufactured findings would be the anti-pattern. This run did neither: it
found one real, proven defect, **disproved one of its own hypotheses**, and confirmed two clean.

**Skills exercised live:** `chief-engineer` (census + route), `senior-review` (invariants, examine),
`data-tier` (its first live use — and it earned its place), `debug-protocol` two-way discipline (the
disproved race), `threat-model` (the daemon boundary), `correctness-gate` reproduce-ladder. Baseline
re-proven first per the decay rule.

---

## Proven baseline (decay rule, PROTOCOL §1)

Installed deps, ran the project's own offline smoke suite: **53 of 54 pass** `(proven)`; the single
failure is the optional `mcp` package not installed, not a code defect. The system is genuinely
well-tested. This is the trustworthy floor the review builds on.

---

## Director summary (Law 4)

This is a healthy, well-engineered system. The review found **one performance defect that scales
with usage** — on every retrieval, the graph signal issues one database query per neighbour node
instead of one batched query, so its database round-trips grow with the size of the knowledge
graph. Proven: 40 neighbours → 41 round trips, collapsible to 1. The fix is small and uses a
batching pattern the codebase already uses elsewhere. Everything else checked came back clean or
already-resolved, including a concurrency concern I tried hard to prove and could not.

`REVIEW: shippable-with-findings(retrieval graph-signal N+1)`
`DATATIER: findings(top: fragments_linked_to_entity, class: O(neighbourhood))`

---

## Invariants derived (senior-review Phase 1)

For an agent memory system: (1) retrieval cost scales sub-linearly with store size, or the system
dies as it succeeds; (2) the vector index and the DB never disagree about which fragments exist;
(3) a write never blocks a read (the daemon's stated design); (4) the daemon's trust surface is
bounded to its intended local caller.

---

## Findings

### F1 — Retrieval graph signal is N+1 over the neighbourhood *(violates invariant 1)* — **(proven)**

**Root cause:** in `retrieval.py` Signal 2, the graph-fragment fetch loops over every neighbour and
calls `db.fragments_linked_to_entity(nid)` once per neighbour — each a separate SQL round trip:
```python
for entity in matched_entities:
    neighbors = db.get_neighbors(entity.id, max_hops=2)
    for nid in neighbors:
        for fid in db.fragments_linked_to_entity(nid):   # one query PER neighbour
            ...
```
`get_neighbors` itself is efficient (one batched `IN`-clause per hop), and Signal 1 *explicitly*
pre-loads IDs to avoid "a SQL query per candidate (which compounds badly)" — the author knows the
pattern. It just wasn't applied to Signal 2. The neighbourhood grows as the knowledge graph
accumulates, so this is cost that worsens precisely as the system is used more.

**Proof (executed against the real `Database` + real queries):**
```
2-hop neighbours discovered : 40
fragments_linked_to_entity() DB round trips : 41   (= neighbours + 1)
FIX (single batched IN-clause): 1 DB round trip for the same 40 fragments
```

**Principle:** *fan-in over a collection is one batched query, not one query per element* — the same
rule `get_fragments_batch` already embodies.

**Fix (shipped):** `patches_tiermemory/01_graph_signal_batch.md` — a `fragments_linked_to_entities`
batch finder (one `IN`-clause over all neighbour ids), replacing the per-neighbour loop. Hands the
index decision to `data-tier` (no new index needed — `idx_triples_subject/object` already cover it,
confirmed by reading the DDL) and nothing to `data-evolution` (no schema change).

---

### F2 (disproved) — VectorIndex concurrency race — **hypothesis, NOT a finding**

**The hypothesis (suspected):** `VectorIndex.add/remove/query` mutate shared state (`_id_map`,
`_rev_map`, `_next_id`, with a `_next_id += 1` read-modify-write) with **no internal lock**, while
the daemon offloads retrieval (`query`) and ingest (`add`) to the *same* thread-pool executor —
a classic data race that would corrupt the id↔fragment mapping.

**The two-way test (executed):** ran the real `VectorIndex` under 3 concurrent writers + 3 readers
for 2.5s, then 4 threads each adding 400 items.
```
concurrent crashes observed : 0
distinct fragments added : 1600 | _id_map size : 1600 | lost mappings : 0 | rev/id disagreement : 0
```
**The race did not manifest.** CPython's GIL makes the individual dict ops and the `+= 1` atomic
enough that the corrupting interleaving doesn't occur at this granularity. Per the suite's own law,
a hypothesis whose two-way test fails **does not become a finding** — I downgrade rather than
assert. This is the discipline that separates a real review from a plausible one.

**Honest residual (trace-only watch, not a finding):** the GIL is an implementation accident, not a
contract. `usearch`'s C-extension `add`/`search` *may* release the GIL, and a future free-threaded
CPython (PEP 703) removes it entirely — either could expose the unlocked maps. Recommended as a
`REVIEW_LEDGER.md` watch entry with trigger "first observed map inconsistency in a live path, or
free-threaded build adoption", **not** a change to make now. Adding a lock speculatively would
violate the suite's own "complexity must be purchased by a proven need."

---

### F3 (clean / resolved) — ledger item N1 `Score.__format__` — **(proven) resolved**

The existing ledger's open watch-item — `Score` impersonating a float was missing `__format__` —
is now closed: `__format__` is implemented (`models.py:236`). The watch-item's own
confirmed-good/worse trigger has fired toward good. No action; noted so the ledger can be updated.

### F4 (clean, with one latent caveat) — daemon trust boundary — **(trace-only)**

The daemon and web dashboard bind to `127.0.0.1` by default — correct for a local-first single-user
system; the absence of auth on the TCP/HTTP protocol is acceptable at loopback. **Latent caveat:**
a `--host` CLI flag allows `0.0.0.0`; if ever set, the unauthenticated retrieve/ingest/**reindex**
operations become network-reachable. Recommend the flag's help text warn that exposing beyond
loopback requires an auth layer that does not currently exist — a one-line doc/guard, not a blocker.

---

## What's genuinely good (earned)

- The `Database` connection is correctly serialized by a reentrant lock, and the author *documented
  why* (`schema.py:300-313`) — the exact concurrency reasoning most systems get wrong, gotten right.
- Signal 1 avoids N+1 deliberately and says so; `get_neighbors` and `get_fragments_batch` are
  properly batched. F1 is the one place the established pattern lapsed — a consistency gap, not a
  knowledge gap.
- The smoke suite runs fully offline with no API keys — real test discipline.
- The existing `REVIEW_LEDGER.md` is model-memory done right: unproven bets with falsifiable
  resolution triggers, pruned over time. This is Law 2 in practice.

## One growth theme

**Apply Signal 1's own batching rule everywhere a loop touches the DB.** The single finding is the
established batch pattern not reaching one of four retrieval signals. A grep for `for … in …:` with
a `db.` call inside the body would catch the class in seconds and is worth adding to the build loop.

---

## Level-2 postmortem — what this run taught the suite

1. **`data-tier` earned its place on first live use.** It was added in v1.6.0 as a candidate, on the
   strength of two external critiques, with the honest caveat "build it from a real N+1, not a
   document's say-so." This run *is* that real N+1. The skill's core method — judge cost *class*,
   count round trips, prove against representative shape — found a genuine usage-scaling defect a
   line-by-line review would likely have read past. The candidate is now validated `(proven)`.

2. **The disproved race is the more important result.** The suite's evidence vocabulary did exactly
   its job: a clean, specific, executable hypothesis ran its two-way test, failed, and was correctly
   refused entry as a finding. A lesser review would have shipped "unlocked shared state under
   concurrency = race" as a confident finding — it reads true. It isn't, here, and only execution
   showed that. This is the single best demonstration in either live run of why the suite forbids
   `(suspected)` from becoming a verdict.

3. **No new skill or process gap surfaced.** Unlike LIVE_RUN_001 (which spawned four skills), this
   run found the suite's current mandate set sufficient for an 18k-LOC system. That absence of new
   gaps is itself signal: the suite may be approaching mandate-completeness for single-process
   application-tier systems. The next gap, if any, is likeliest at the multi-process / distributed
   boundary the daemon only gestures at.

`MAINT LIVE_RUN_002: resolved(validated on 18k-LOC, proven) | data-tier confirmed-good(first live N+1) | race-hypothesis disproved(two-way test negative) | no new mandate gap`
