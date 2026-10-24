"""Create mode: draft and lint a project-local `verify` skill whose verdicts come from VERIFY.md.

scaffold-skill  Detect the stack (package.json, pyproject.toml, go.mod, Cargo.toml, Dockerfile,
                compose, Makefile) and write .claude/skills/verify/SKILL.md plus a feature map
                stub per VERIFY.md feature. Every guess is marked TODO(verify-create): a draft
                is not a skill until an agent replaces them from the repo and proves it once.
                --adopt keeps a SKILL.md already there (Claude Code's bundled /verify records
                one at the same path) and adds only what is missing.
skill-check     Lint the generated skill: callable frontmatter, the required sections, no
                placeholder left, executable helpers, and every feature file tied to a VERIFY.md
                section that has a literal fail-signal and a fail-proof. Claude Code runs a
                model-invocable project `verify` skill before each commit, so the skill must
                also have a cheap `## Before a commit` path.
"""
import json
import os
import re

SKILL_DIR = os.path.join(".claude", "skills", "verify")
TODO = "TODO(verify-create)"
COMMIT = "Before a commit"
SECTIONS = ("Launch", "Doctor", "Drive", "Evidence", "Cleanup", "Helpers", "Verdict", COMMIT)
FEATURE_H2 = ("Sub-features", "How to get to it (user POV)", "Driving it with ", "Gotchas")
WEB_DEPS = ("next", "vite", "react", "vue", "svelte", "@angular/core", "nuxt", "astro", "electron")
API_DEPS = ("express", "fastify", "koa", "@nestjs/core", "hono", "fastapi", "flask", "django",
            "starlette", "aiohttp", "axum", "actix-web", "rocket", "warp", "gin-gonic", "echo", "fiber")


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _has(repo, *names):
    return [n for n in names if os.path.exists(os.path.join(repo, n))]


def detect_stack(repo):
    """What the repo says about how it runs. Facts only; the agent decides what they mean."""
    found = {"name": os.path.basename(os.path.abspath(repo)), "stacks": [], "surfaces": [],
             "run": [], "test": [], "harness": [], "ports": [], "evidence": []}

    def add(key, *vals):
        for val in vals:
            if val and val not in found[key]:
                found[key].append(val)

    pkg = _read(os.path.join(repo, "package.json"))
    if pkg:
        add("stacks", "node")
        try:
            data = json.loads(pkg)
        except ValueError:
            data = {}
        found["name"] = data.get("name") or found["name"]
        scripts = data.get("scripts") or {}
        deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
        for s in ("dev", "start", "serve", "preview"):
            if s in scripts:
                add("run", f"npm run {s}")
        for s in ("test", "e2e", "test:e2e"):
            if s in scripts:
                add("test", f"npm run {s}")
        if any(d in deps for d in ("@playwright/test", "playwright")) or _has(repo, "playwright.config.ts",
                                                                              "playwright.config.js"):
            add("harness", "Playwright")
        if "cypress" in deps or _has(repo, "cypress.config.ts", "cypress.config.js"):
            add("harness", "Cypress")
        if any(d in deps for d in WEB_DEPS):
            add("surfaces", "web")
        if any(d in deps for d in API_DEPS):
            add("surfaces", "api")
        if data.get("bin"):
            add("surfaces", "cli")
    py = _read(os.path.join(repo, "pyproject.toml"))
    if py or _has(repo, "setup.py", "requirements.txt"):
        add("stacks", "python")
        m = re.search(r'(?m)^name\s*=\s*"([^"]+)"', py)
        if m:
            found["name"] = m.group(1)
        if re.search(r"(?m)^\[project\.scripts\]|^\[tool\.poetry\.scripts\]", py):
            add("surfaces", "cli")
        low = (py + _read(os.path.join(repo, "requirements.txt"))).lower()
        if any(re.search(rf"\b{re.escape(d)}\b", low) for d in ("fastapi", "flask", "django", "starlette", "aiohttp")):
            add("surfaces", "api")
        if "pytest" in low:
            add("test", "python -m pytest -q")
        if "playwright" in low:
            add("harness", "Playwright")
        if _has(repo, "manage.py"):
            add("run", "python manage.py runserver")
    for entry in ("app.py", "main.py", "server.py"):
        if _has(repo, entry):
            add("stacks", "python")
            add("run", f"python {entry}")
            if re.search(r"http\.server|HTTPServer|uvicorn|\.run\(|FastAPI\(|Flask\(", _read(os.path.join(repo, entry))):
                add("surfaces", "api")
    gomod = _read(os.path.join(repo, "go.mod"))
    if gomod:
        add("stacks", "go")
        m = re.search(r"(?m)^module\s+(\S+)", gomod)
        if m:
            found["name"] = m.group(1).rsplit("/", 1)[-1]
        add("run", "go run ./cmd/..." if os.path.isdir(os.path.join(repo, "cmd")) else "go run .")
        add("test", "go test ./...")
        if any(d in gomod for d in ("gin-gonic", "labstack/echo", "gofiber", "go-chi", "gorilla/mux")):
            add("surfaces", "api")
        if "spf13/cobra" in gomod or "urfave/cli" in gomod:
            add("surfaces", "cli")
    cargo = _read(os.path.join(repo, "Cargo.toml"))
    if cargo:
        add("stacks", "rust")
        m = re.search(r'(?m)^name\s*=\s*"([^"]+)"', cargo)
        if m:
            found["name"] = m.group(1)
        add("run", "cargo run")
        add("test", "cargo test")
        if any(d in cargo for d in ("axum", "actix-web", "rocket", "warp")):
            add("surfaces", "api")
        if "clap" in cargo or "[[bin]]" in cargo:
            add("surfaces", "cli")
    docker = _read(os.path.join(repo, "Dockerfile"))
    if docker:
        add("stacks", "docker")
        add("ports", *re.findall(r"(?mi)^EXPOSE\s+(\d+)", docker))
    for compose in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        text = _read(os.path.join(repo, compose))
        if text:
            add("stacks", "compose")
            add("run", f"docker compose -f {compose} up --wait")
            add("ports", *re.findall(r"[\"']?(\d{2,5}):\d{2,5}", text))
    make = _read(os.path.join(repo, "Makefile"))
    for target in ("dev", "run", "serve", "start", "test", "e2e"):
        if re.search(rf"(?m)^{target}\s*:", make):
            add("test" if target in ("test", "e2e") else "run", f"make {target}")
    if os.path.isdir(os.path.join(repo, "tests")) or os.path.isdir(os.path.join(repo, "test")):
        add("evidence", "test output")
    if not found["surfaces"]:
        found["surfaces"].append("cli" if found["stacks"] else "unknown")
    if not found["harness"]:
        surface = found["surfaces"][0]
        add("harness", {"web": "Playwright", "api": "curl", "cli": "subprocess"}.get(surface, "subprocess"))
    add("evidence", {"web": "screenshot + ARIA snapshot", "api": "response body + status",
                     "cli": "command, stdout, stderr, exit code"}.get(found["surfaces"][0], "transcript"))
    return found


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "feature"


def _bullets(items, empty):
    return "\n".join(f"  - `{i}`" for i in items) if items else f"  - {empty}"


def _intro():
    return """Written for an agent reading it cold. Pass/fail is never decided here: each mapped feature has a
check in [VERIFY.md](../../../VERIFY.md) with a literal `fail-signal:` and a `fail-proof:`, and
verify-loop's `verify.py` runs it. This file says how to reach and watch the real app."""


def section_bodies(facts):
    """The required sections in order, as (heading, body). Adopt appends the missing ones."""
    harness = facts["harness"][0]
    return [
        ("Launch", f"""{TODO}: the repo's own dev command, from an empty disposable data dir (migrations, seed), on owned
ports/profiles. Ready means usable, not just that a process answers. Mirror it in VERIFY.md
`## Run` (`setup`, `start`, `ready`, `stop`) so `verify.py run` launches the same way. Teardown is
under Cleanup. For a short-lived CLI: build once, then run each drive in its own process/PTY.
Isolation: {TODO}: can two instances run side by side? If not, refuse to drive a shared one."""),
        ("Doctor", f"""{TODO}: one read-only command answering "is this the right, healthy instance?" (owned port/PID,
expected build, auth). It is VERIFY.md's `## Run` `doctor:`; for a build-sensitive service it
checks the running artifact identity, not just health. Run it first, and again after any surprise."""),
        ("Drive", f"""Harness: {harness}. Existing harnesses first; real selectors, routes and commands from this repo
(ARIA names, data attributes, prompts, paths), never coordinates. One file per feature in
[features/](features/README.md).
{TODO}: the shared recipe (how to invoke the harness against the launched instance)."""),
        ("Evidence", f"""Drive the real user path, not internal setters or test-only routes. Capture the action, the
resulting state and side effects (files, rows, messages) through a second read; mocks only at
production boundaries. Evidence for this surface: {facts['evidence'][-1]}.
Proof goes to `.verify-evidence/<feature>/` and survives cleanup; output tails and rejection
receipts also stay in `.verify-state.json`. Keep secrets out.
{TODO}: confirm the evidence location is git-ignored."""),
        ("Cleanup", f"""Stop only what this run started (PID/port you own); never kill by process name. Remove scratch
data, never evidence. Afterwards, confirm the evidence files still exist.
{TODO}: exact teardown commands (VERIFY.md `stop:`)."""),
        ("Helpers", f"""{TODO}: each helper script lives in `scripts/` here, is executable, and is shown with its exact
invocation. Delete this section's TODO if there are none."""),
        ("Verdict", """`<verify-loop>` is the installed verify-loop skill's directory. Every caller gets its answer:

1. Prove a feature can fail: in a scratch copy, put the product in its `fail-proof:` state and run
   `python <verify-loop>/scripts/verify.py run .` until its `fail-signal:` shows; restore.
2. Freeze: `verify.py baseline .`. A check that seems wrong is a finding for a person, not an edit.
3. Done: `verify.py run . --strict`, then `verify.py report .` (or `status --json`). Return that
   output unchanged: verdict, `VERIFY:` line, observed rejection, passes and gaps.

Never weaken a journey or expectation to make it pass. If verify-loop is absent, run the checks
directly before and after, keep both outputs, and report the verdict as `unverified`. When the app
changes, use verify-loop's maintain mode (`verify.py maintain .`) to keep this skill honest."""),
        (COMMIT, """Claude Code runs this skill right before each commit (not for docs- or test-only changes). Here,
run only the mapped checks the change touches; do not launch or drive the app by hand:

    python <verify-loop>/scripts/verify.py run . --affected

`nothing to run` or green: commit. Red: do not commit; fix it, or report it blocked. This gate is
not done: `--affected` can miss a check, so done is still the whole strict run under Verdict."""),
    ]


def skill_text(facts):
    surface = facts["surfaces"][0]
    body = "\n\n".join(f"## {h}\n\n{b}" for h, b in section_bodies(facts))
    return f"""---
name: verify
description: >-
  Launch, drive and prove {facts['name']} ({surface}) the way a user does, with evidence. Use to
  verify a change here, check a feature in the running app, or prove a task done. Verdicts come
  from VERIFY.md through verify-loop.
---

# Verify {facts['name']}

{_intro()}

Detected (verify each against the repo, then delete this list):
- stacks: {", ".join(facts['stacks']) or "none"}; surfaces: {", ".join(facts['surfaces'])}
- run candidates:
{_bullets(facts['run'], "none found")}
- test candidates:
{_bullets(facts['test'], "none found")}
- harnesses: {", ".join(facts['harness'])}; ports: {", ".join(facts['ports']) or "none declared"}
{TODO}: confirm these, pick the primary surface, note the others, then remove this block.

{body}
"""


def readme_text(facts, names):
    rows = "\n".join(f"- [{n}](./{slug(n)}.md)" for n in names)
    return f"""# {facts['name']} verification map

The maintained source for verifying what users touch. Read this index before driving the app, then
use the matching feature file. Each file names its VERIFY.md section (`verify-section:`), which
holds the check, its literal `fail-signal:` and its `fail-proof:`.

## Baseline preconditions

- {TODO}: launched per ../SKILL.md Launch, doctor passing, seed data named here.
- Never drive an instance this run did not start.

## Driving conventions

- Start each recipe from the baseline state. Prefer stable handles over position.
- Restore seeded data after a mutation. Do not remove proof artifacts during cleanup.

## Feature entry contract

H1 title, one paragraph of user-visible behavior, a `verify-section:` line, then exactly four H2s:
`Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, `Gotchas`. A journey
the seed data cannot complete fails and says why in `Gotchas`; never weaken it to pass. A proof
through one entry point does not verify the others this map lists.

## Features

{rows}
"""


def feature_text(name, harness):
    return f"""# {name}

{TODO}: one paragraph describing the user-visible behavior.

verify-section: {name}

## Sub-features

- {TODO}: `short-id` one line per behavior.

## How to get to it (user POV)

- {TODO}: every user entry point (button, route, command, endpoint).

## Driving it with {harness}

Preconditions:

- {TODO}: required state, beyond the baseline.

- **{TODO}.** User action, exact command, observable result.
- **Proof.** Save to `.verify-evidence/{slug(name)}/`; read the stored effect back a second way.

## Gotchas

- {TODO}: traps that waste or invalidate a run.
"""


def adopt_text(text, facts):
    """Keep an existing SKILL.md as written; add frontmatter, the VERIFY.md link and missing sections.

    Returns (new text, what was added)."""
    added = []
    text = text.replace("\r\n", "\n")
    front = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not front:
        head = skill_text(facts).split("\n---\n", 1)[0] + "\n---\n\n"
        text, added = head + text, ["frontmatter"]
    if "VERIFY.md" not in text:
        end = re.match(r"^---\n.*?\n---\n", text, re.S).end()
        text = text[:end] + "\n" + _intro() + "\n" + text[end:]
        added.append("VERIFY.md link")
    heads = _sections(text)
    missing = [(h, b) for h, b in section_bodies(facts) if h not in heads]
    if missing:
        text = text.rstrip("\n") + "\n\n" + "\n\n".join(f"## {h}\n\n{b}" for h, b in missing) + "\n"
        added += [f"## {h}" for h, _ in missing]
    return text, added


def cmd_scaffold_skill(v, repo, adopt=False):
    target = os.path.join(repo, SKILL_DIR)
    skill_path = os.path.join(target, "SKILL.md")
    existing = _read(skill_path) if os.path.exists(skill_path) else None
    if existing is not None and not adopt:
        print(f"{os.path.join(SKILL_DIR, 'SKILL.md')} already exists; not overwriting. If Claude Code's "
              "/verify recorded it, `scaffold-skill --adopt` keeps it and adds what is missing. "
              "Otherwise use skill-check.")
        return 1
    facts = detect_stack(repo)
    features = []
    if os.path.isfile(os.path.join(repo, v.RECIPE)):
        features, _ = v.parse(v.read(repo, v.RECIPE), repo=repo)
    names = [f["name"] for f in features if not f["journey"]][:5] or ["Primary feature"]
    os.makedirs(os.path.join(target, "features"), exist_ok=True)
    if existing is None:
        files, added = {"SKILL.md": skill_text(facts)}, None
    else:
        text, added = adopt_text(existing, facts)
        files = {"SKILL.md": text} if added else {}
    files[os.path.join("features", "README.md")] = readme_text(facts, names)
    for n in names:
        files[os.path.join("features", slug(n) + ".md")] = feature_text(n, facts["harness"][0])
    if existing is not None:
        files = {rel: t for rel, t in files.items()
                 if rel == "SKILL.md" or not os.path.exists(os.path.join(target, rel))}
    for rel, text in files.items():
        with open(os.path.join(target, rel), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    if existing is not None:
        print(f"adopted {os.path.join(SKILL_DIR, 'SKILL.md')}: kept its text; added "
              f"{', '.join(added) or 'nothing'}; wrote {len(files) - (1 if added else 0)} missing feature file(s). "
              "Move its recorded launch and drive steps into Launch and Drive.")
    else:
        print(f"wrote {SKILL_DIR}: SKILL.md + {len(names)} feature file(s) "
              f"({', '.join(names)}). Stack: {', '.join(facts['stacks']) or 'unknown'}; "
              f"surface: {facts['surfaces'][0]}; harness: {facts['harness'][0]}.")
    if not features:
        print(f"no {v.RECIPE} features: map the top 3-5 user-facing features in {v.RECIPE} and the map.")
    print(f"DRAFT: replace every {TODO} from the repo, prove it once, then run `verify.py skill-check`.")
    return 0


def _sections(text):
    return re.findall(r"(?m)^##\s+(.+?)\s*$", text)


def skill_problems(v, repo):
    """Every reason the generated skill is not yet a deliverable, as text lines."""
    base = os.path.join(repo, SKILL_DIR)
    skill = _read(os.path.join(base, "SKILL.md"))
    if not skill:
        return [f"no {os.path.join(SKILL_DIR, 'SKILL.md')}: run `verify.py scaffold-skill` first"]
    problems = []
    front = re.match(r"^---\n(.*?)\n---\n", skill, re.S)
    if not front:
        problems.append("SKILL.md has no YAML frontmatter: the skill never registers")
    else:
        fm = front.group(1)
        if not re.search(r"(?m)^name:\s*verify\s*$", fm):
            problems.append("frontmatter name must be `verify` to replace the built-in user-only /verify")
        if not re.search(r"(?m)^description:\s*\S", fm):
            problems.append("frontmatter has no description")
        if "disable-model-invocation" in fm:
            problems.append("frontmatter sets disable-model-invocation: other skills cannot call it")
    heads = _sections(skill)
    for s in SECTIONS:
        if s not in heads:
            problems.append(f"SKILL.md is missing `## {s}`")
    if "VERIFY.md" not in skill:
        problems.append("SKILL.md does not link VERIFY.md: verdicts must come from its checks")
    commit = re.search(rf"(?ms)^##\s+{COMMIT}\s*$(.*?)(?=^##\s|\Z)", skill)
    if commit and not re.search(r"verify\.py\s+run\s+\S+\s+--affected", commit.group(1)):
        problems.append(f"`## {COMMIT}` must run `verify.py run . --affected`: Claude Code runs this "
                        "skill before every commit, and a full launch and drive there is slow")
    for root, _, files in os.walk(base):
        for f in sorted(files):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, repo)
            if TODO in _read(p):
                problems.append(f"{rel} still has {TODO} placeholders")
            if os.path.basename(root) == "scripts":
                if not os.access(p, os.X_OK):
                    problems.append(f"helper {rel} is not executable")
                if os.path.relpath(p, base).replace(os.sep, "/") not in skill:
                    problems.append(f"helper {rel} has no invocation shown in SKILL.md")
    fdir = os.path.join(base, "features")
    readme = _read(os.path.join(fdir, "README.md"))
    if not readme:
        problems.append("no features/README.md index")
    sections = {}
    if os.path.isfile(os.path.join(repo, v.RECIPE)):
        sections = {f["name"]: f for f in v.parse(v.read(repo, v.RECIPE), repo=repo)[0] if not f["journey"]}
    else:
        problems.append(f"no {v.RECIPE}: each mapped feature needs a check there")
    files = sorted(f for f in (os.listdir(fdir) if os.path.isdir(fdir) else [])
                   if f.endswith(".md") and f != "README.md")
    if not files:
        problems.append("the feature map has no feature files")
    for f in files:
        text, rel = _read(os.path.join(fdir, f)), f"features/{f}"
        if f"({f})" not in readme and f"(./{f})" not in readme:
            problems.append(f"{rel} is not listed in features/README.md")
        got = _sections(text)
        if len(got) != 4 or any(not g.startswith(want) if want.endswith(" ") else g != want
                                for g, want in zip(got, FEATURE_H2)):
            problems.append(f"{rel} must have exactly these H2s in order: Sub-features, "
                            "How to get to it (user POV), Driving it with <harness>, Gotchas")
        m = re.search(r"(?m)^verify-section:\s*(.+?)\s*$", text)
        sec = sections.get(m.group(1)) if m else None
        if not m:
            problems.append(f"{rel} has no `verify-section:` line naming its VERIFY.md section")
        elif sections and sec is None:
            problems.append(f"{rel} names `{m.group(1)}`, which is not a {v.RECIPE} feature section")
        elif sec is not None:
            if not sec["checks"]:
                problems.append(f"{v.RECIPE} `{sec['name']}` has no check")
            if not sec["signals"]:
                problems.append(f"{v.RECIPE} `{sec['name']}` has no literal fail-signal:")
            if not sec["proofs"]:
                problems.append(f"{v.RECIPE} `{sec['name']}` has no fail-proof:")
    return problems


def cmd_skill_check(v, repo, as_json=False):
    problems = skill_problems(v, repo)
    if as_json:
        print(json.dumps({"ok": not problems, "problems": problems, "exit": 1 if problems else 0}, indent=2))
    else:
        for p in problems:
            print(f"SKILL  {p}")
        print("SKILL-CHECK: " + ("ok; the shape is right. Done still needs one end-to-end proof and "
                                 "`verify.py run --strict` + `status` green" if not problems
                                 else f"{len(problems)} problem(s)"))
    return 1 if problems else 0
