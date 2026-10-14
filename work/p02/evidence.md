# P02 application recipe evidence

2026-10-13, Asia/Bangkok. Authorized by `/drive implement the p02`.
Local implementation, committed in the P02 slice (see Git history); no version bump, release or installed-plugin update.
RUN.json owns the execution gate; work/runs/RUN.pre-p02.json preserves the completed P01 run.

## Result and implementation

Bounded API, short-lived CLI and browser application trials passed. This establishes the tested
fixture on this Windows/Python host, not general application support or reliable agent compliance.
The existing project recipe and verifier were reused; no application-driver framework was added.
Fixture: evals/fixtures/p02. Runnable checks: tests/test_project_recipe.py.

The trials exposed two helper gaps: stop commands were skipped without a background process
(CLI), and stop-command failures were silently accepted. verify.py now runs cleanup for both
surfaces, retains its result/output, rejects cleanup failure in exit status and JSON output, and
preserves feature evidence. It also retains doctor output so stale-instance rejection remains
readable after teardown. Source snapshots remain conservative: disposable data uses build/data,
which the existing verifier excludes; tracked/source cleanup changes still invalidate proof.

## Executed discrimination

`python -m unittest discover tests -p test_project_recipe.py` passes three tests covering both
API and CLI, an unrelated old server, and failed cleanup (text and JSON verdicts).
Before helper repair, CLI disposable data survived and failed cleanup returned exit 0.
The initial API status failure was a fixture layout gap: disposable data was in the source snapshot.
[Before output](before.txt) retains these failures after the fixture layout correction;
[after output](after.txt) retains the passing check.

- API: isolated loopback port and owner token; ready probes usable HTTP, doctor checks build,
  owner and actual PID. POST /note acknowledges the write; a separate GET /note must match.
- CLI: isolated invocation of the known fixture source/interpreter; `put` and a second `get`
  process exercise persistence. No background server is required.
- Both reject disabled persistence with `expected persisted note, got None`, restore saving,
  freeze unchanged checks, then pass `run --strict` and `status` with VERIFY-STATE: green.
- Old server: a separately owned responsive instance on the expected port has a different
  owner. Doctor rejects it before writes. Its PID stays alive and a subsequent identity query
  succeeds; only the test's own finally block terminates its control process.
- Cleanup: a failing stop command makes the helper return 1, records a red state and retains
  `cleanup deliberately failed`; JSON also reports red. Feature evidence remains readable,
  disposable data is absent and the owned server PID is no longer alive.
- Retained [trial artifacts](trials/) contain command output, state/receipts, observed responses
  and doctor identity. Temporary application trees are removed after each test.

Browser was exercised separately through Codex's in-app browser, using the public page:
fill Note, Save, reload, Reopen. The same expectation rejected `null` with saving disabled and
accepted `"P02 browser persisted note"` after restoration. A separate HTTP query confirmed the
stored value. The owned process was terminated only after checking its owner/PID; its temporary
directory and tab were removed. Screenshots and observations remain readable after teardown.
[Observations](browser-observations.json), [cleanup/identity](browser-instance.json),
[negative screenshot](browser-negative.png), [positive screenshot](browser-positive.png).
The first browser initialization timed out; the inventory/retry succeeded. That attempt was
harness failure, not product rejection. This is a coordinator-driven smoke trial, not an
independently graded browser-agent compliance experiment or a reusable automated browser driver.

## Behavioral replay and limits

Actual replay: `python evals/run.py --cases verify-loop-make-it-verified --arms with --repeats 1
--jobs 1 --timeout 180 --budget-usd 2 --out evals/results/p02-replay --keep-workdirs`.
The agent loaded verify-loop and repaired a test that ran zero cases. Independent replays showed
its check rejected broken refunds and accepted correct refunds. Overall verdict **FAIL**:
no baseline and final state red. The agent treated the request as assessment, declined product
repair and stopped for approval. No expectation was weakened and no success was inferred.
[Grade](../../evals/results/p02-replay/verify-loop-make-it-verified/with-1/grade.txt),
[result](../../evals/results/p02-replay/verify-loop-make-it-verified/with-1/result.json),
[report](../../evals/results/p02-replay/verify-loop-make-it-verified/with-1/report.md).
RESULTS.md retains the replay. One run establishes no reliability, comparison or savings.

Three scratch mutations were rejected by the application assertions: skip CLI cleanup,
ignore the stop failure, and skip doctor. `python work/p02/mutations.py` reproduces them;
individual outputs are retained beside this file. The user's working tree was never mutated.

Existing test_verify.py's 64 tests passed after the first cleanup repair; the final full suite
(488 tests passing) and replay-safe completion gate are retained in RUN.json. Catalog check passed (36 skills).
An initial completion replay passed all 488 tests but was rejected because RESULTS.md
changed during the check while preserving historical scores. That attempt remains in RUN.json;
the gate was rerun after the scorecard settled.
Existing prerequisite/timeout/zero-case discrimination remains harness evidence; startup errors
are not counted as behavioral rejection. No new model workflow instructions were changed.
Authentication, production environments, remote dependencies, concurrent writes and general
browser automation remain untested. Generated scaffold drivers still remain unverified drafts.

Broader project Next and P01's larger fresh-reader trial remain open in BUILD.md and the handoff.
