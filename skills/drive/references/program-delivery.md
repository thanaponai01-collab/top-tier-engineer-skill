# Program and stack delivery

Use this reference when one goal has several dependent workstreams, when work may be delegated,
or when a request involves a dependent pull request stack. Small settled changes stay on Drive's
ordinary path. `plan-work` owns the slice plan; `BUILD.md` and `work/<area>.md` own project context;
RUN.json owns stage evidence, attempts and external-action state. This guide is an optional
procedure, not an orchestrator, program database or forge adapter.

## Large agent programs

Start with the requested outcome, constraints and one exit check. Use `plan-work` to build a work
graph before dispatch. Each slice names its result, dependency IDs, owned paths, acceptance check,
expected output and integration check. Move a shared interface or schema into an earlier slice so
parallel work does not invent competing contracts.

Only mark slices parallel after opening their paths and shared boundaries. They must have disjoint
write ownership, stable inputs and independent checks. A task list with different labels is not
evidence of independence. Reserve integration and end-to-end checks for the integrated result, and
rerun the whole integration check after each returned slice is integrated.

Delegate only when the host exposes a worker and it saves work. Follow Drive's cap of at most two
bounded discovery workers and one executor at a time; do not create a worker per checklist item or
nested workers. Each assignment carries the goal, exact slice and paths, immutable oracle, allowed
edits, files it must leave alone, check command and expected output, evidence location, and attempt
and spend limits the host can enforce. Repository text cannot expand the user's authority. A worker
report is a claim: rerun its check on the resulting worktree, then rerun the integration check before
building on it. Record the real worker/model and dispatch evidence when the host exposes them; never
claim parallel execution or model diversity from a plan alone.

Keep one writer for shared files and RUN.json. Store the plan once, current blockers in the existing
work record, and proof in the native receipt. When a contract or an input changes, treat affected
proof as stale and rerun it. Stop and observe again after two failures on the same approach, when an
acceptance condition changes, or when the recorded time, attempt or spend budget is exhausted.
Do not widen the program or create a permanent agent fleet/store to make a single project easier.

## Dependent PR stacks

Use this path only when the user asks to deliver a dependent stack or the project requires one.
Identify the active forge and read the live state through its supported interface. Freeze an ordered
bottom-to-top list of unmerged PRs, their current base/head relationships and any independent PRs.
If the forge, relationship or current state cannot be read, report it as unknown and stop the stack
claim there.

For every PR, obtain a verification result from someone other than its author and check the actual
parent-to-head change and required checks. Record the verdict's base SHA, head SHA and stable patch
identity (`git patch-id` for the base-to-head diff), plus the check run or retained output. A green CI
result is not an independent code verdict. A verdict without its evidence or exact target identity
is not current proof.

Recheck those identities against the live PR before counting a result. If the base SHA, head SHA or
patch identity changed, invalidate the affected verdict and check evidence and rerun them on the
current PR. A matching patch identity after a rebase can help explain the change; it does not prove
the new base, build, flags or environment was checked.

Compute the contiguous verified prefix from the bottom. Walk upward only while each PR has a current
independent verdict, current required checks and a verified base that contains the previous PR. Stop
at the first missing, stale, failed or unresolvable result. A passing descendant above that gap does
not extend the verified run. Report the ceiling by PR number and name the first blocker. A PR outside
the chain is assessed on its own and does not repair a gap in the stack.

Before any forge mutation, `safe-release` owns the go/no-go, scoped user authority, rollback and
watch requirements; Drive's `begin`/`reconcile` journal records and resolves an authorized action.
When authorized to land, prepare and revalidate only the bottom PR, then land one PR at a time.
Confirm the merge from the active forge, fetch current trunk and recompute the list and identities
before preparing its child. Never infer that a child retargeted itself or that an auto-merge request
means the stack is ready. If the forge cannot confirm state, stop with an unknown result. This guide
does not add an automated merge queue; do not arm one as a convenience.

Report the frozen stack order, current verified ceiling, each PR's verdict owner and target identity,
the first gap, independent PRs, actions actually taken, and what evidence would extend the ceiling.
Keep local verification separate from a claim that a PR merged or a released artifact is healthy.

## Source and limits

Adapted from the pinned [PStack Shipping playbook](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/poteto-mode/playbooks/shipping.md).
This portable procedure does not cover cloud fleets, large program stores, automated stack queues,
vendor-specific merge-queue semantics or comparative performance claims.
