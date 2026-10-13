# Context records and storage

## Record format

Existing files work without migration. Sections become records automatically. New area records may
use these optional HTML comments before their heading:

```markdown
<!-- context-id: task:login -->
<!-- context-type: task -->
<!-- context-area: auth -->
<!-- context-status: active -->
<!-- context-paths: src/auth.py, tests/test_auth.py -->
<!-- context-links: feature:login -->
# Preserve login return URL
Result: return URL retained; verification not run.
Remaining: expiry behavior unverified.
```

Explicit IDs identify one record per file. Existing multi-section files use path plus heading.
An ID must be unique. Types can include intent, task, feature, command, decision and evidence.
Status describes work, never proof. Record evidence command/result/baseline in its actual receipt;
for uncommitted code use relevant file hashes or the verifier's receipt rather than pretending HEAD
identifies the working tree. Replaced decisions retain their replacement link and original source.

## Retrieval and indexing

The stdlib helper discovers root context documents, startup intent/work pointers, and their local
Markdown/include links. It does not index source trees, dependencies or arbitrary hidden files.
External links are references, never fetched. SQL stores records, relationships, source hashes and
full-text search terms. Default queries exclude archived/completed/superseded records; pass
--history explicitly for historical questions. Search returns at most 20 results and summaries,
show returns a bounded excerpt and a source pointer for further reading.

Full index/rebuild traverses this context graph. Routine index --files reads only selected files,
replacing their records transactionally, including deletion. Cache schema mismatches/corruption
can be repaired by index --rebuild. Add `.project-context/` to existing Git ignore conventions.
Query cache results are checked against source hashes; changed sources are read directly and marked
stale-index. File fallback reads at most 50 linked files and reports truncation; a full index
discovers at most 500. Beyond that, index explicit areas incrementally. No query silently writes SQL.
Code impact is a path association, not a complete dependency graph: use feature-map and inspect
shared callers when necessary. Structural checks never certify owner intent or product correctness.
