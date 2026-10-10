---
name: project-setup
description: >-
  Prepare project agent instructions and model-routing policy without onboarding or running checks. Preserve existing notes. Manual: run /project-setup.
disable-model-invocation: true
metadata:
  stage: orient
  card: "prepare agent instructions and routing"
---

# Project Setup

Prepare the instructions that future sessions need. Setup does not discover the full codebase,
create foundation documents, build an index, run tests, or start workers. Drive owns that work.
No other skill requires setup.

Read existing project instructions and the root directory listing only. Use the existing host
instruction file (CLAUDE.md for Claude Code, AGENTS.md for Codex); create one when absent.
Preserve manual text and existing model overrides. Do not create competing instruction files.

Add or refresh one managed block, at most 30 lines, between `<!-- agent-routing -->` and
`<!-- /agent-routing -->`. Record:
- Coordinator: the current session model. The user selects Opus in Claude Code if desired.
- Execution: plugin agent `agents/drive-executor.md` (Sonnet), for bounded implementation and local checks.
- Discovery: plugin agent `agents/setup-reader.md` (Haiku), for bounded read-only evidence collection.
- Drive owns foundation preparation, execution gates and task context upkeep.
- Workers receive assigned paths, acceptance checks, allowed edits and limits; no full chat dump.
- Workers cannot change acceptance oracles or authorize external actions. Coordinator judges proof.
- Honor host overrides; report actual routing or single-agent fallback rather than claiming a switch.

Link only existing context documents; preserve the existing start-here block. No placeholders,
new goal guesses or database are needed. Routing belongs in this instruction block, while plugin
agent definitions supply the host-readable model settings. Do not duplicate plugin agents into
project .claude/agents unless the user asks for portable project-local workers.

Read [Drive routing](../drive/references/model-routing.md) for the policy. A Markdown instruction
cannot switch the current session model or provide a delegation API. If the host lacks the
configured workers, record that limitation; do not substitute unsupported model names.

Report the instruction file changed, configured worker roles and any host limitations. Setup
alone makes no claim about product readiness or verification.

*Test:* setup changes only the selected instruction file, preserves manual notes, creates one
routing block and performs no worker dispatch or product checks. Repeating it is a no-op.
