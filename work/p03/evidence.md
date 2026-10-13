# P03: end-state execution enforcement

Scope: local eval runner; no skill, release or installed-plugin change.

Selected mistake: counting success text as proof while losing the command verdict.
Two controlled occurrences were executed before the fix with the same enforcement:
`print("OK"); exit(1)` on stdout and `print("OK", file=sys.stderr); exit(3)` on stderr.
Both were incorrectly accepted; retained failures: [before.txt](before.txt).
These are observed local reproductions, not two historical agent incidents.

`evals/run.py` owns command execution and action grading. It now keeps exit/output together
in saved `end_output` records and requires exit 0 plus matching output. Timeout, launch failure,
nonzero exit and old text-only records cannot silently pass. Diagnostics identify the exit
requirement; missing exit evidence requests a rerun. Rescoring uses the same enforcement.
No configurable exception or generic rule engine was added.

Acceptance: `python -m unittest discover tests -p test_p03.py` (4 checks), and
`python -m unittest discover tests -p test_runner.py` (52 checks; [output](runner.txt)).
The existing drive-bug-through-skills behavioral case is reused to verify that an otherwise
passing report cannot overcome failed/unknown end-state execution in the final score.
The same check accepts exit-zero output. This is harness discrimination, not a new live
model-behavior trial or a reliability estimate; no skill instructions changed.

Repository suite and final replay receipts are in RUN.json. Catalog check remains required.
The completed P02 run is preserved in docs/RUN.pre-p03.json. Unrelated
`docs/RUN.project-foundation.json` is preserved. Git history owns the commit identity.
