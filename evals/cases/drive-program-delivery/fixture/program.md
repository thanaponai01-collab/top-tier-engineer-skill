# Import pipeline rollout

Goal: accept JSON imports through both the CLI and API while preserving one canonical import
record. The work is split into these proposed changes:

| ID | Work | Owned paths | Depends on | Check |
|---|---|---|---|---|
| A | Define the canonical import record and validation errors | `src/contracts/import_record.py`, `tests/contracts/test_import_record.py` | — | unit tests for valid, empty and malformed records |
| B | Parse JSON into the canonical record | `src/parsers/json_import.py`, `tests/parsers/test_json_import.py` | A | parser tests include malformed input and round-trip fields |
| C | Add CLI import command | `src/cli/import_command.py`, `tests/cli/test_import_command.py` | A, B | invoke the CLI and inspect persisted record |
| D | Add API import endpoint | `src/api/import_endpoint.py`, `tests/api/test_import_endpoint.py` | A, B | call the endpoint and read the stored record |
| E | User documentation | `docs/importing.md` | none | examples match the accepted schema |
| F | Full integration journey | `tests/integration/test_import_journey.py` | B, C, D | submit through both entry points, read back identical fields |

The shared record is not finalized. C and D are proposed for parallel implementation after A and B
are complete; E has no code dependency. F must use the integrated result. The project has no
existing agent roster or dispatcher configured.
