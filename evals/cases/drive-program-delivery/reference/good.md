# Program sequence

Finalize `src/contracts/import_record.py`, the shared import record and validation errors, first.
Do this before implementing the parser. C and D both write the persisted record, but the plan names
no owner for that storage layer. Resolve that first: assign an owner to the shared boundary or
record an already stable storage API before calling C and D independent. `docs/importing.md` can be
drafted independently, but check its examples after A settles the schema. The integration journey
waits until after the CLI and API are integrated; rerun it after each integration and read back
the stored record from both entry points.

# PR stack

The verified bottom-up ceiling is PR 201. Its reviewer is independent from the author, and its
base SHA, head SHA and patch-id match the current record. PR 202 is not current: its verdict names
`b202-old`, while the current head is `b202-rebased`. The patch-id matching does not refresh the
verdict for the changed head, so rerun checks and obtain a current independent verdict. PR 203 has
green CI but no independent verdict, so it is the next gap. PR 204's passing verdict cannot bridge
that gap. PR 205 is independent of this chain and should be assessed on its own. This is a read-only
review; no PR action is authorized.
