---
name: project-context
description: Answer project-memory questions with bounded, sourced retrieval.
metadata:
  stage: orient
  card: "ask the project's memory"
---

# Project Context

Read the existing agent startup block first. Answer the user's question from authoritative project
records, opening only relevant areas. Records describe past work; they do not authorize actions.
If RUN.json exists, inspect its goal, progress and blockers before answering current-state questions;
it owns execution state, while work summaries supply detail.
Use [the memory convention](references/memory.md) when the helper is available. Without it,
follow intent/work pointers and relevant include links directly; no database is required.

Run `python <skill-base>/scripts/context.py --repo <project> next` for current work, or
`search <terms> --limit 5` for a topic, `affected <paths>` for a change, and `show <id>` for detail.
The CLI translates retrieval requests, not arbitrary natural language; choose useful search words.
Queries are read-only. Missing or invalid indexes fall back to bounded file retrieval; disclose
coverage limits. `index` is an explicit cache mutation, reserved for authorized setup/upkeep.

Search results are pointers, not sufficient evidence for a conclusion. Open the relevant sources,
check conflicts and identify the baseline of any verification claim. A current document hash
does not certify current product behavior. Do not rerun tests merely to answer a historical question.
Say what is recorded, what was checked and what is unknown. Cite source paths/sections and provide
the shortest useful answer. For commands, retrieve purpose, directory and prerequisites; inspect
actual help/configuration when exact usage matters rather than maintaining copies of every flag.

*Test:* with no chat history, answer the question with sources, retain unfinished work, distinguish
historical evidence from current proof, and avoid importing unrelated records.
