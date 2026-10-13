# Task context

Use this from any skill when a material task fact is missing or uncertain. Keep the original task
and its authority; retrieve context for the next decision rather than starting another workflow.

1. Name the task's target (feature, path, symbol or work item), the fact needed, and whether the
   question concerns current intent, implementation, history or proof. Read startup intent/work
   pointers first. Inspect RUN.json for current execution state when relevant.
2. Follow task-conditioned area links to the current requirement, unfinished work and feature/check
   mappings. Search using the target's name and terms from those records; open the returned sources.
   If no mapping exists, use a scoped file/symbol search and disclose the gap. An empty index result
   means nothing found in indexed context, not that the project has no relevant code or history.
3. Inspect the mapped implementation and actual callers where the task touches shared behavior. Search the target symbol in repository source (for example, `rg -n --glob '*.py' '<symbol>' src tests`) and open production call sites across area boundaries; mappings are starting points, not a complete caller list. Keep searches inside the repository, not the host filesystem.
   Check the working-tree diff so uncommitted changes are not mistaken for committed behavior.
4. When the reason or prior task matters, use scoped Git history: `git log -n 10 -- <paths>`,
   `git log -S '<symbol or value>' -- <path>`, and `git show <sha> -- <paths>` as appropriate.
   For a renamed file, use `git log --follow -- <file>`. Open referenced PRs/issues only through
   available read tools. A commit message is a lead; inspect its patch and current requirements.
   Git identifies the committed baseline, while the working-tree diff identifies additional work.
5. Resolve claims by role: owner records establish desired behavior, code establishes implemented
   behavior, Git/decision sources explain history, and receipts establish only their recorded checks
   at their recorded baseline. Report conflicts and missing sources. For current proof, inspect
   the recipe's command, directory and prerequisites; run it only when the task authorizes a safe
   check. Otherwise identify it as unrun. Retrieval alone never authorizes a live mutation or retry.

Stop when the next decision has its relevant requirement, state, code/history sources, verification
status and material unknowns. Expand only for a specific unresolved question or shared dependency;
record unavailable/shallow history, missing mappings and unread areas instead of claiming completeness.
Pass those facts and source paths/SHAs back to the calling skill; a short paragraph is enough for a
small task. Reuse context already opened in this session unless the baseline or task has changed.

For a broad resumption, `recall` supplies a state capsule when requested. For disputed rationale,
`code-history` supplies a deeper source trail when available. Neither is a required dependency:
perform the scoped reads above directly when that is sufficient or the skill is unavailable.
Verification stays with the skill performing the task; context preparation supplies its inputs.
