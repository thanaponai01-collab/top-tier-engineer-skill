Treat `src/contracts/import_record.py` as the first gate: finish A before parser work in B. C and D
both write the persisted record, yet no slice owns the shared storage layer. Resolve that first by
adding a small slice for the shared storage contract or assigning it to A. `docs/importing.md` can
be drafted now; check its examples after A settles the schema. The integration journey should run
after the CLI and API are integrated, then rerun after each integration.

For the stack, the highest verified ceiling is PR 201. It has a current independent PASS tied to
its exact base, head and patch identity. PR 202, the next child, has a stale verdict from
`b202-old` but now points to `b202-rebased`;
the unchanged patch-id is not enough to make that old head verdict current. PR 203 only has CI, so
it has no reviewer verdict. PR 204 sits above the gap and cannot extend the safe prefix. PR 205
doesn't depend on these changes and belongs in a separate review. Nothing should be changed on the
forge from this read-only request.
