---
name: project-setup
description: Set a fresh project up for these skills, once, so every later session finds its checks. Drafts VERIFY.md and FEATURES.md from whatever code is there and adds a pointer block to the project's CLAUDE.md. Use when starting these skills in a new or different codebase, "set up this project for the skills", "start fresh here", or when a repo has code but no VERIFY.md or FEATURES.md.
---

# Project Setup

The skills create their own files on demand, but nothing tells a new project they exist. The next
session, or an agent that never met these skills, has to rediscover the checks or never learns they
are there. This skill runs once per project: draft the two files from the code, then leave a pointer
where every session reads first.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

## 1. Look before writing

Read what is there: the top-level tree, the manifest (`package.json`, `pyproject.toml`, `go.mod`,
`Cargo.toml`, `pom.xml`, a `Makefile`), the test folder, and whether `VERIFY.md`, `FEATURES.md` and
`CLAUDE.md` already exist. Say in one line what kind of system this is (web app, CLI, library,
service) and how you know. An empty repo has nothing to draft: say so and stop at step 4.

## 2. Draft the two files

Both scripts read the code, write a draft, and refuse to overwrite (exit 2 if the file exists), so
running them twice is safe. They belong to two other skills and sit in those skills' `scripts/`
folders:

```
python <verify-loop base directory>/scripts/verify.py init <repo>      # VERIFY.md from the test files
python <feature-map base directory>/scripts/features.py init <repo>    # FEATURES.md from the entry points
```

Where a file already exists, leave it and say so. Where the scripts are not available, write the
file by hand: `VERIFY.md` is one `##` section per feature listing the command that proves it and one
that breaks it on purpose; `FEATURES.md` is one `##` section per feature with the way a user
reaches it (route, click, shortcut or command).

A draft is a starting point, not a result. `features.py init` on a stack it cannot read reports
"0 entry point(s)", and `verify.py init` leaves `TODO` lines. Do not fill those in here: list them.
Making each check real is `verify-loop`; making the map true is `feature-map`.

## 3. Leave the pointer

Add this block to the project's `CLAUDE.md`. If there is no `CLAUDE.md`, create one holding only this
block (the built-in `/init` writes the rest). If a `## Project checks` heading is already there,
rewrite it only if its content differs, never append a second.

```
## Project checks
- `VERIFY.md`: each feature and the command that proves it. Run every check before saying done;
  `verify-loop` builds and maintains it.
- `FEATURES.md`: what the system has and how a user reaches each feature. Read it before driving or
  changing the app; `feature-map` keeps it true.
- `docs/architecture.md`, if present: the system traced as a diagram; `arch-map` draws and updates it.
- `WHY.md`, if present: recorded reasons behind decisions that took real digging to find;
  `code-history` looks them up and adds to it before you change something that looks wrong.
- Something broken and the cause unknown: `debug-protocol`. Need the system explained plainly, not
  changed: `explain`.
- None of the files above exist yet and this is first contact with the system: `onboard-system` builds
  the whole set in one pass, in the order that makes each one true.
```

Use the real names of the files that exist. If one was not created, leave its line out.

If the project also has a `GEMINI.md` or `AGENTS.md`, put the same block in each so other agents find
the checks too. Never create either one.

## 4. Report

Answer first: what now exists. Leave the files uncommitted and include the `git status` lines for
them. Then what is still a draft, by file and count (`TODO` lines,
entry points found), and the one skill that finishes each. Nothing here is verified yet, so do not
call the project set up in the sense of *done*; call it *ready for* the skills.

```
CREATED: <files written>            KEPT: <files that were already there>
DRAFT:   <file: N TODOs / N entry points>
NEXT:    <one step, e.g. "verify-loop: replace the TODOs in VERIFY.md">
```

## Rules

- **Once, then hands off.** A second run changes nothing that exists.
- **No code changes.** This skill writes `VERIFY.md`, `FEATURES.md` and the pointer block (in `CLAUDE.md`, and in
  `GEMINI.md` / `AGENTS.md` where they exist), and nothing else.
- **Say what you could not see.** A stack the scripts do not read is a finding, not a failure.

*Test:* a second run on the same repo leaves every file byte-for-byte unchanged, and the report names
every `TODO` still open.

Checks that an agent has run its own work is `verify-loop`; a map of what the system has is
`feature-map`; why code is the way it is, is `code-history`. This skill stands without them: it
drafts by hand and leaves the pointer. Called as step 2 of a full first-contact pass, it's
`onboard-system`; run this skill directly when only the checks need setting up.
