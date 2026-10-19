# Create a project verify skill

Use when a repo has no scripted way to launch and drive its real app, or someone asks for a
"verify skill", "driver skill" or `/verify` for this project. The output is a project-local skill
at `.claude/skills/verify/` named `verify`. At the repo root, a project skill with that name
replaces Claude Code's built-in user-only `/verify`, so any skill, agent or person can call it. In
a monorepo, write it in the touched package and pass that package as the repo argument. Write it
for an agent that reads it cold, in the middle of a task.

The generated skill says how to reach and watch the app. VERIFY.md decides pass or fail, and
verify-loop returns the answer. The generated skill never decides a verdict on its own.

## 1. Interview the repo, not the user

Answer from the codebase, and ask the user only what you cannot observe:

- **Surface:** what a user touches (web UI, CLI/TUI, API, desktop, library). Pick the primary one
  and note the rest.
- **Run:** the repo's own dev command, ports, env, seed data and auth.
- **Drive:** existing harnesses first (Playwright/Cypress specs, PTY/expect, curl-able routes).
  Only then a generic one.
- **Observe:** screenshots, transcripts, response bodies, logs, exit codes, stored state.
- **Isolate:** can two instances run side by side (ports, data dirs, profiles)? If not, the skill
  refuses to drive a shared instance.

If the checkout does not start, fix it or report the blocker precisely before generating.
Launch, doctor, drive and evidence follow the [project recipe](project-recipe.md). Read it, and do
not repeat it in the generated skill beyond what this repo needs.

## 2. Map the checks first

Pick the top 3-5 user-facing features from routes, commands, menus or docs. Give each one a
VERIFY.md section ([format](../VERIFY_FORMAT.md)) with a real-run check, an `oracle:` from the
spec, and a literal `fail-signal:`. Put launch in `## Run` (`setup`, `start`, `ready`, `doctor`,
`stop`). For a build-sensitive service, the doctor checks the
[running artifact identity](../VERIFY_FORMAT.md#run). Helpers that the checks call live in the
skill's `scripts/` folder. They must be executable, and the skill shows how to invoke each one.

## 3. Generate the skill

`verify.py scaffold-skill <repo>` detects the stack (package.json, pyproject, go.mod, Cargo.toml,
Dockerfile, compose, Makefile) and writes a draft:

- `SKILL.md`: frontmatter `name: verify` and a description that names the app, the surface and
  when to use it. It has no `disable-model-invocation`. Its sections are **Launch** (from an empty
  data dir to usable, with isolation stated), **Doctor** (read-only: the right, healthy
  instance), **Drive** (real selectors, routes and commands from this repo), **Evidence** (the real
  user path; the action, resulting state and side effects; mocks only at production boundaries;
  proof in a named place that survives cleanup), **Cleanup** (kill only what you started),
  **Helpers**, and **Verdict** (route back through verify.py).
- `features/README.md` plus one file per VERIFY.md feature. Each file has an H1, one paragraph, a
  `verify-section: <VERIFY.md feature>` line, and exactly these H2s: `Sub-features`,
  `How to get to it (user POV)`, `Driving it with <harness>`, `Gotchas`.

Every guess carries `TODO(verify-create)`. Replace each one from the repo, and delete the
"Detected" block. If the seed data cannot satisfy a journey's precondition, the journey fails and
its `Gotchas` entry says why. Never weaken a journey to make it pass.

## 4. Prove it once, then freeze

1. Follow the generated skill as written: launch, doctor, drive one mapped feature, capture
   evidence, clean up. Then confirm the evidence still exists. Run cleanup after a failed attempt
   too.
2. For a build-sensitive service, change the source without committing it while the old process
   keeps running. The doctor must reject that instance.
3. For each mapped feature, put the product in its `fail-proof:` state in a scratch copy, or
   restore it from a saved copy afterwards. `verify.py run` must show the `fail-signal:`. Restore,
   and confirm the restore.
4. `verify.py skill-check <repo>` must report no problems. Then run `baseline`, `run --strict` and
   `report`. Once the skill is committed, add `last-maintained: <sha>` to `features/README.md` so
   that [maintain mode](maintain.md) counts churn from that commit.

If you proved it in a stand-in (a container instead of the real VM, a local stack instead of a
remote one), list each setup step the stand-in did and the target will not. Those steps stay
unverified.

## Report

Return the `verify.py report` answer ([format](handoff.md#what-comes-back)). Also list the files
generated, the feature you drove end to end, where its evidence is, and the features or surfaces
left unmapped. The plugin repo's `examples/verify-create/` is a finished run.
