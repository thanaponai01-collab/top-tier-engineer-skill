# P09 implementation plan

Exit check: `python -m unittest discover tests` and `python tools/catalog.py --check` pass;
`python work/p09/check_behavior_evidence.py` confirms the retained Drive arm passes the read-only
case while the no-skill arm misses the targeted planning gap; the repository suite and catalog
check pass in RUN.json. No external PR action is run.

| Slice | Files | Check | Depends on |
|---|---|---|---|
| Freeze case and pre-change replay | `evals/cases/drive-program-delivery/`, `work/p09/baseline/` | baseline output retained; report grades against frozen answer key | none |
| Add optional Drive guidance for large programs and dependent PR stacks | `skills/drive/SKILL.md`, `skills/drive/references/program-delivery.md` | reference contract assertions; post-change replay | baseline |
| Record adoption and proof | `work/p09/`, `work/pstack-handoff.md`, `BUILD.md`, `evals/RESULTS.md` | full suite and catalog check; evidence paths resolve | guidance |

The docs task may run while constructing the fixture only if it does not read or edit the skill
guidance; this run uses one writer and no parallel workers. Integrate by replaying the complete case,
then the repository suite and catalog check. Forge integration, PR mutation, cloud fleets and an
automated program store remain outside the local implementation.
