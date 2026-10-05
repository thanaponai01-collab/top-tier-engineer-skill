# A reusable project recipe

Discover this from the repo when the app is awkward to drive or verification will recur. Put the
short recipe in VERIFY.md; link to existing harness docs for detail. Generate no extra framework.

## Find the surface

Read the actual entry point: route, browser action, CLI dispatcher, public API or library call.
Take the expected outcome from the user's requirement, spec or existing contract. Source code
locates the action; it does not decide whether its current result is correct.

Start with the changed behavior and one risk-relevant failure or seam. Record alternate entry
points and prerequisites that remain untested as gaps. Build a complete FEATURES.md only when a
whole-app inventory is useful or requested.

## Launch and doctor

Use existing dev/test commands, a disposable data directory and owned ports/profiles. Record the
readiness signal, build identity, login/role and material flags. Verify the instance is yours and
is the intended build; a responsive port alone may be an old server. A short-lived CLI needs a
known binary and isolated invocation, not a background server.

VERIFY.md's `## Run` supports executable `setup`, `start`, `ready`, `doctor`, and `stop` commands,
plus free-text `login`. Keep secrets out of the document and captured output.

After a surprising failure, doctor the instance again before continuing. If process health is
good but UI/data state is wedged, reset to the documented baseline or relaunch the owned instance.

## Drive and observe

`verify.py scaffold-driver [--type web|api|cli]` drafts a driver to start from; a draft is not
proof until it rejects a wrong result.

Use the existing test/browser/PTY/HTTP harness with stable selectors and public entry points.
Capture the action and observed result; assert a concrete expected value. Internal setters and
test-only routes can skip the wiring you need to verify. Keep mocked boundaries explicit.

For writes, observe the stored effect through a second read: save, reopen, compare; submit,
then query; export, then read the file. Include restart/retry/concurrency only when relevant to
the changed behavior. A success toast is insufficient evidence of persistence.

## Demonstrate rejection

Run the finished mapped check on the original bug or a controlled wrong state with
`verify.py run`. Confirm the failure is the intended assertion; startup/syntax errors and zero
cases are broken verification machinery. Restore, run, and require the same check to pass.
Use a scratch worktree/copy for deliberate mutations when the working tree has user edits.

The helper captures failed command output, but cannot determine whether a failure was meaningful.
Inspect the signal and explain it in `fail-proof:`. A scratch copy owns its own receipts; perform
the final strict verification there, or safely carry its reviewed checks and state back before
running again. A newly edited check needs a new rejection demonstration.

## Evidence and cleanup

Name where screenshots, response bodies or transcripts go, and retain useful, redacted proof.
Record the tested build/revision, relevant configuration, real/mocked boundary and entry point.
Checks' output tails and rejection receipts live in .verify-state.json; larger artifacts can live
in an existing ignored evidence folder. Evidence files are outputs, not frozen oracle inputs.

Stop only owned instances and remove disposable data. Preserve evidence through successful and
failed cleanup; confirm it is still readable afterwards. If cleanup changed tracked inputs,
repeat the checks against the final state. Exercise docs/harness corrections again; a product
regression stays a failure rather than becoming a new expected result.

Finish with `verify.py run --strict` and `verify.py status`. Report verified mapped claims, failed
claims and unverified paths separately. An inaccessible environment is a limit on the verdict.
