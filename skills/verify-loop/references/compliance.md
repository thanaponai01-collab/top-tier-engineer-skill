# Compliance Checks Reference

`<skill-base>/scripts/compliance.py` provides deterministic, stdlib-only validation commands for `VERIFY.md`:

| Kind | Command | Fails When |
|---|---|---|
| `schema:` | `compliance.py schema schema.json out.json --strict` | A field is missing, mistyped, out of range, or (with `--strict`) unexpected. |
| `privacy:` | `compliance.py privacy out/ logs/` | Sensitive credentials (tokens, private keys, passwords, card numbers) appear in output files. |
| `guardrail:` | `compliance.py guardrail abuse.json -- <cmd>` | A case in `abuse.json` is not refused as expected. |
| `repeat:` | `compliance.py repeat 3 -- <cmd>` | Repeated runs of `<cmd>` produce non-deterministic differences. |

## Fail-Proofing Compliance Checks
Feed each check an intentional violation (e.g. invalid schema JSON or dummy secret) and verify it exits 1 before freezing.
