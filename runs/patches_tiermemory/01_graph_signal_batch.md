# Patch 01 — Batch the graph-signal fragment fetch (resolves LIVE_RUN_002 F1)

**Cause:** retrieval Signal 2 calls `fragments_linked_to_entity` once per neighbour — O(neighbourhood)
DB round trips per retrieval, growing with the knowledge graph.
**Principle:** fan-in over a collection is one batched query (the pattern `get_fragments_batch` and
`get_neighbors` already use).

## Fix

`memory_system/schema.py` — add a batched finder beside the existing single one:
```python
def fragments_linked_to_entities(self, entity_ids: list[str]) -> list[str]:
    """All distinct source fragments linked to ANY of the given entities, in one query."""
    if not entity_ids:
        return []
    ph = ",".join("?" * len(entity_ids))
    rows = self.fetchall(
        f"SELECT DISTINCT source_fragment FROM triples "
        f"WHERE (subject_id IN ({ph}) OR object_id IN ({ph})) "
        f"AND source_fragment IS NOT NULL",
        (*entity_ids, *entity_ids),
    )
    return [r["source_fragment"] for r in rows]
```

`memory_system/retrieval.py` — Signal 2 collects neighbour ids first, then one batched call:
```python
matched_entities = db.fuzzy_match_entities(project_id, query_text, limit=5)
entity_scope: list[str] = []
for entity in matched_entities:
    entity_scope.append(entity.id)
    entity_scope.extend(db.get_neighbors(entity.id, max_hops=2))
# de-dup preserves the original first-seen ordering used by RRF rank
seen = set(); ordered_entities = [e for e in entity_scope if not (e in seen or seen.add(e))]
graph_frag_ids: list[str] = []
gf_seen = set()
for fid in db.fragments_linked_to_entities(ordered_entities):
    if fid not in gf_seen:
        gf_seen.add(fid); graph_frag_ids.append(fid)
```

**Ordering note:** the original appended fragments in neighbour-iteration order, which feeds RRF
rank. The batched query returns them in DB order, a *different* rank ordering for the graph signal.
This is a behaviour change in graph-signal rank (not in which fragments are candidates). Verify
recall@k is unchanged on the eval set before landing — `data-tier` flags this as the one place the
fix is not purely mechanical, and hands the before/after recall check to the project's `eval.py`.
If rank-order matters, fetch batched but re-sort `graph_frag_ids` by each fragment's best
neighbour rank computed from the in-memory `ordered_entities` index — still one DB round trip.

**Index:** none needed — `idx_triples_subject` and `idx_triples_object` already cover the `IN`
predicate (confirmed by reading the DDL). No `data-evolution` migration required.

**Pre-verify (data-tier → eval.py / correctness-gate):**
- round trips for the graph signal drop from `len(neighbours)+1` to `1` (the LIVE_RUN_002 proof);
- `eval.py` recall@5 is unchanged within noise (the proven 94.4% baseline from the existing ledger).
