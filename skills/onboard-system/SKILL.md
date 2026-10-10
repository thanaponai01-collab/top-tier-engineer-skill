---
name: onboard-system
description: >-
  First contact with an unfamiliar codebase — set it up for the skills, then build and leave behind the full picture (what it has, how it's shaped, why it's built that way) so every later session or agent finds it instead of rediscovering it. Runs project-setup itself as its first step; use project-setup alone when only the checks are wanted. Use for "onboard me to this codebase", "get up to speed on this system", "I've never seen this repo before", "learn this system top to bottom", or when a repo has no VERIFY.md, FEATURES.md, docs/architecture.md or WHY.md yet. Manual: run /onboard-system.
disable-model-invocation: true
metadata:
  stage: orient
  card: "first time in this codebase, build the whole picture"
---

# Onboard System

Build a useful understanding without rerunning the setup checkpoints. The project foundation is
owned by `project-setup`; this skill adds explanation, targeted rationale and a prediction check.

*Evidence labels: **proven** = you ran it; **traced** = followed code; **suspected** = neither.*

## 1. Inventory once

Follow existing startup pointers and run project-setup's foundation inventory when installed.
Otherwise inspect the same categories directly: intent, work, feature/check indexes, architecture,
commands and retrieval. Existing but stale documents are refresh candidates; existence is not proof.
Read the root summaries, then only the areas needed for the user's question. Do not read every file.

## 2. Fill the gaps once

Use `project-setup` for missing/stale categories and reuse its inventory, workers and completed
checks. Read its foundation/economy references only when doing that work. It now owns architecture,
commands and memory as well as verification; do not call those skills again just to repeat setup.
Without setup installed, prepare the same bounded sourced notes directly and state the limitation.
Use the lowest-cost available configured worker for independent bounded discovery when worthwhile;
Claude Code's plugin setup-reader uses Haiku. No worker per checkpoint and no full-history handoff.
The coordinator writes shared documents once and checks cited paths; it retains final judgment.

## 3. Explain and investigate only relevant why

Use the feature traces, architecture overview and command index to explain the main flow, ownership
and important constraints. Follow relevant area links. If a surprising boundary matters, consult
`code-history` or inspect available records directly. Save supported rationale in existing WHY/decision
records only when useful; unknown reasons remain unknown. No exhaustive history pass or new store.

## 4. Check one prediction

Choose one requirement-backed example. Predict the outcome from the saved notes, then trace it
against relevant source or use a replay-safe existing check. Do not rerun setup verification merely
to demonstrate understanding; reuse its receipt with baseline and historical/current distinction.
A mismatch is a context or product finding, not permission to rewrite requirements. If external
access is needed, keep the example unverified and identify the missing prerequisite.

## 5. Report and maintain

Give a short system account, sourced facts, categories created/refreshed/kept, scope not read,
current verification boundary and one Next. Update affected records after authorized changes and
index those files only; use `project-update` or direct notes if unavailable. Read-only onboarding
questions explain findings without editing the project. RUN.json owns driven execution state.

*Test:* a fresh reader can explain the relevant flow and check one prediction from saved sources;
current categories are reused, changed architecture is refreshed, unknown rationale is preserved,
and discovery/checks are not repeated for each checkpoint.
