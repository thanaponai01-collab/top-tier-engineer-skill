# Project context handoff

Use during project setup and authorized updates to project code or documentation. For a read-only
review, report context gaps without editing the project. A small direct edit needs only updates
to facts it changes, not a new workflow or document set.

## Capture intent

Preserve the project's existing specification and work record. Use BRIEF.md and BUILD.md only
when equivalents do not exist. Record the owner's job, constraints, decisions and observable
acceptance criteria, citing their source. Mark inferred goals and defaults as assumptions;
record missing intent as an open question rather than deriving desired behavior from code.
An empty project can have a useful intent and next step without verified product behavior.

## Make the next session find it

Keep one start-here block in the existing agent instruction file, bounded to 30 lines. Include
`intent: BRIEF.md` and `work: BUILD.md`, substituting project-relative paths for existing equivalents.
Link relevant feature/check indexes, state when to read area notes, and keep detailed facts in
their authoritative files. Include an upkeep instruction for direct edits too: authorized updates
refresh affected intent, evidence and Next; read-only reviews report gaps. The work document has
`## Next` with one concrete step and completion
check, plus current blockers. RUN.json, if present, owns execution state; the work summary agrees
with it. Setup records a next step even when verification or requirements are blocked.

## Keep it current while changing the project

Before acting on a changed owner requirement, replace its current entry and archive the superseded
entry. Follow relevant brief areas. After work, refresh the current progress, evidence, blockers
and next step; update affected feature/check entries when behavior or entry points changed.
Keep implementation findings distinct from intended behavior. Record the owner's explicit
changes even when their implementation is deferred. Report where updates were saved.

## Scale unfinished work

Keep Next, urgent blockers and a short list of area links in the work index. Move detailed active
backlog, unresolved questions and unverified history to `work/<area>.md` with `include:` links.
Give each link a task condition; keep each area within the work budget (80 lines), splitting further
when needed. Preserve status, dependencies and triggers verbatim where they matter. This is current
work, not archived proof. Completed history follows build-discipline's archival eligibility rules.

## Check the handoff

Run recall's installed `scripts/context_budget.py <repo> --check-handoff`. It checks budgets,
startup markers, discoverable nonempty intent/work documents, Next and existing local context
links, including nested areas. Equivalent paths use the intent/work pointers above. Fix affected
gaps within the task's scope; otherwise report them. A structural pass does not prove requirement
quality, product correctness or that every agent obeys the pointers. Preserve unresolved intent
and label context as partial instead of declaring it complete. Other skills remain usable when
this helper is unavailable; inspect the same handoff manually and disclose that limitation.
