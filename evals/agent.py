#!/usr/bin/env python3
"""
agent.py — runs one real agent, headless, and reads back what it did.

run.py and route.py both need the same three things: start Claude Code on a
prompt in a throwaway folder, with or without this plugin loaded; keep the
full transcript; and pull out of it what the agent actually DID (tools it
called, commands it ran, skills it loaded) apart from what it SAID. This file
is those three things and nothing else.

Why "did" matters: a report can say "I ran the tests" without running them.
The transcript cannot. Graders that only read the report grade the writing;
graders that read the transcript grade the work.

Stdlib only. Needs the `claude` CLI on PATH.
"""
import hashlib, json, os, re, shutil, subprocess, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# What a plugin install actually ships. The evals, their answer keys and the
# test suite stay behind, so an agent that wanders around the plugin folder
# cannot read the expected answer.
PLUGIN = os.path.join(ROOT, "plugin")

# Environment the child agent is allowed to see. Everything else — in
# particular the parent session's own CLAUDE_CODE_* wiring — is dropped, so the
# child is a clean, ordinary Claude Code run and cannot talk to this session.
ENV_KEEP = (
    "PATH", "HOME", "LANG", "LC_ALL", "TERM", "TMPDIR",
    "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy", "http_proxy", "no_proxy",
    "NODE_EXTRA_CA_CERTS", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE",
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_OAUTH_TOKEN", "IS_SANDBOX",
    # Windows: without SystemRoot the child dies in 0.1s ("Bun needs this set"); the rest is where
    # it finds its login and temp folder.
    "SystemRoot", "SYSTEMROOT", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "HOMEDRIVE", "HOMEPATH",
    "COMSPEC", "PATHEXT", "TEMP", "TMP",
)

IGNORED_DIRS = {"__pycache__", ".pytest_cache", ".git", ".mypy_cache", ".ruff_cache"}
SHELL_TOOLS = {"Bash", "PowerShell"}
# A shell command that prints a file's text. Naming the path (ls, rm, grep -l) is not reading it.
SHELL_READERS = re.compile(r"(?<![\w.-])(cat|sed|head|tail|less|more|nl|bat|type|get-content|gc)(?![\w.-])", re.I)

# Strings that mean the agent reached the answer key instead of doing the task.
LEAK_MARKERS = ("evals/cases", "reference/good", "reference/bad", "expect.json",
                "top-tier-engineer-skill/evals")


def clean_env():
    env = {k: v for k, v in os.environ.items() if k in ENV_KEEP}
    # Root can't use bypassPermissions unless it says it is in a sandbox; a
    # throwaway temp folder is exactly that.
    # throwaway temp folder is exactly that. Only "1" counts, so it is forced.
    env["IS_SANDBOX"] = "1"
    # The child keeps USERPROFILE/APPDATA for its own login, which is also where `gh` keeps the
    # person's GitHub token. An eval agent asked to "file these as issues" must not reach a real
    # tracker, so gh gets an empty config of its own and no token.
    env["GH_CONFIG_DIR"] = GH_EMPTY
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


GH_EMPTY = os.path.join(tempfile.gettempdir(), "tte-eval-no-gh")


def stage_plugin(dest, hooks_profile=None):
    """Copy only what an installed plugin contains into `dest`; return it.

    `hooks_profile` ("optional", "autonomous") installs hooks/<profile>.json as the staged
    plugin's hooks.json, the same copy a person makes by hand. The checkout is not touched.
    """
    shutil.copytree(PLUGIN, dest, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(*IGNORED_DIRS))
    if hooks_profile:
        shutil.copy2(os.path.join(PLUGIN, "hooks", hooks_profile + ".json"),
                     os.path.join(dest, "hooks", "hooks.json"))
    return dest


def claude_bin():
    """The `claude` executable. On Windows an npm install puts only a claude.cmd shim on PATH,
    which subprocess can't start by bare name and cmd.exe would mangle a multi-line prompt
    through, so resolve the shim to the claude.exe it wraps."""
    found = shutil.which("claude")
    if found and found.lower().endswith(".cmd"):
        exe = os.path.join(os.path.dirname(found), "node_modules", "@anthropic-ai",
                           "claude-code", "bin", "claude.exe")
        if os.path.isfile(exe):
            return exe
    return found or "claude"


def build_command(prompt, plugin_dir=None, model=None, budget_usd=None, max_turns=None):
    # User settings are where a person's installed plugins are enabled, and their user memory
    # (~/.claude/CLAUDE.md) rides along with them. Without this, an installed copy of this very
    # plugin loads in the "without" arm and beside the staged one in the "with" arm, and the
    # comparison measures nothing. Project and local settings of the scratch folder still apply.
    cmd = [claude_bin(), "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--permission-mode", "bypassPermissions", "--no-session-persistence",
           "--setting-sources", "project,local"]
    if plugin_dir:
        cmd += ["--plugin-dir", plugin_dir]
    if model:
        cmd += ["--model", model]
    if budget_usd:
        cmd += ["--max-budget-usd", str(budget_usd)]
    if max_turns:
        cmd += ["--max-turns", str(max_turns)]
    return cmd


def run_agent(prompt, workdir, plugin_dir=None, model=None, timeout=1200,
              budget_usd=None, max_turns=None):
    """Run one agent in `workdir`. Returns the raw stream lines plus timing."""
    cmd = build_command(prompt, plugin_dir, model, budget_usd, max_turns)
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=workdir, env=clean_env(), capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout)
        out, err, timed_out = proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as exc:
        def text(b):
            return b.decode("utf-8", "replace") if isinstance(b, bytes) else (b or "")
        out, err, timed_out = text(exc.stdout), text(exc.stderr), True
    return {"lines": out.splitlines(), "stderr": err, "timed_out": timed_out,
            "seconds": round(time.time() - t0, 1)}


def parse_stream(lines, plugin_dir=None):
    """Turn stream-json lines into what the agent did and what it said.

    Tool calls made inside subagents count too: work delegated is still work
    the run did.
    """
    tools, init, result, texts, hooks = [], {}, {}, [], []
    for line in lines:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        kind = ev.get("type")
        if kind == "system" and ev.get("subtype") == "init":
            init = ev
        elif kind == "system" and ev.get("subtype") == "hook_response":
            hooks.append({"event": ev.get("hook_event", ""), "output": ev.get("output") or ""})
        elif kind == "assistant":
            message = ev.get("message") or {}
            for block in message.get("content") or []:
                if block.get("type") == "tool_use":
                    # `model` is the model that actually produced this call, read from the
                    # message itself; `parent` ties a subagent's call to the dispatch behind it.
                    tools.append({"name": block.get("name", ""), "input": block.get("input") or {},
                                  "sub": bool(ev.get("parent_tool_use_id")),
                                  "id": block.get("id", ""), "parent": ev.get("parent_tool_use_id") or "",
                                  "model": message.get("model", "")})
                elif block.get("type") == "text" and not ev.get("parent_tool_use_id"):
                    texts.append(block.get("text", ""))
        elif kind == "result":
            result = ev

    commands = [t["input"].get("command", "") for t in tools if t["name"] in SHELL_TOOLS]
    skills = [t["input"].get("skill", "") for t in tools if t["name"] == "Skill"]
    # Match actual staged files, never a filename suffix in an unrelated checkout.
    staged = {}
    if plugin_dir:
        folder = os.path.join(plugin_dir, "skills")
        if os.path.isdir(folder):
            for name in os.listdir(folder):
                path = os.path.join(folder, name, "SKILL.md")
                if os.path.isfile(path):
                    staged[os.path.normcase(os.path.abspath(path))] = name
    reads = []
    for t in tools:
        path = t["input"].get("file_path", "")
        if t["name"] == "Read" and path:
            name = staged.get(os.path.normcase(os.path.abspath(path)))
            if name:
                reads.append({"skill": name, "path": path, "sub": t["sub"]})
    # An agent that prints a staged SKILL.md with `cat`/`sed`/`Get-Content` has loaded it as surely
    # as one that calls Read; ignoring that made runs that followed the skill score "not opened".
    for t in tools:
        cmd = t["input"].get("command", "") if t["name"] in SHELL_TOOLS else ""
        if not cmd or not staged or not SHELL_READERS.search(cmd):
            continue
        text = os.path.normcase(cmd.replace("\\", "/"))
        for path, name in staged.items():
            if os.path.normcase(path.replace("\\", "/")) in text:
                reads.append({"skill": name, "path": path, "sub": t["sub"], "via": "shell"})
    usage = result.get("modelUsage") or {}
    final = result.get("result")
    if not isinstance(final, str) or not final.strip():
        final = texts[-1] if texts else ""
    return {
        "tools": tools,
        "commands": commands,
        "skills": skills,
        "skill_reads": reads,
        "skills_loaded": sorted({s.split(":")[-1] for s in skills} | {r["skill"] for r in reads}),
        "skill_read_candidates": [t["input"]["file_path"] for t in tools
                                  if t["name"] == "Read" and t["input"].get("file_path", "").replace("\\", "/").endswith("/SKILL.md")],
        "model_usage": usage,
        "hooks": hooks,
        "final_text": final,
        "model": init.get("model") or (next(iter(usage), None)),
        "models_used": sorted(usage),
        "cost_usd": result.get("total_cost_usd"),
        "turns": result.get("num_turns"),
        "is_error": bool(result.get("is_error")) or not result,
        "stop": result.get("subtype") or result.get("terminal_reason"),
    }


def touched_answer_key(parsed):
    """True when any tool call reached for the evals or their answer keys."""
    blob = json.dumps([t["input"] for t in parsed["tools"]]).replace("\\\\", "/")
    return any(marker in blob for marker in LEAK_MARKERS)


def skill_matches(invoked, wanted):
    """`top-tier-engineer:debug-protocol` and `debug-protocol` are the same skill."""
    return invoked == wanted or invoked.split(":")[-1] == wanted


def action_log(parsed, width=160):
    """One line per tool call, short enough to read — the evidence, kept small."""
    lines = []
    for i, t in enumerate(parsed["tools"], 1):
        inp = t["input"]
        detail = (inp.get("command") or inp.get("file_path") or inp.get("pattern")
                  or inp.get("skill") or inp.get("description") or inp.get("path")
                  or json.dumps(inp)[:width])
        detail = " ".join(str(detail).split())
        if len(detail) > width:
            detail = detail[:width - 1] + "…"
        sub = f"  (subagent{' ' + t['model'] if t.get('model') else ''}) " if t["sub"] else ""
        lines.append(f"{i:3}. {sub}{t['name']}: {detail}")
    return "\n".join(lines)


def snapshot(folder):
    """{relative path: sha256} for every file, skipping caches."""
    out = {}
    for base, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for name in files:
            path = os.path.join(base, name)
            rel = os.path.relpath(path, folder).replace(os.sep, "/")
            with open(path, "rb") as fh:
                out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def diff_snapshots(before, after):
    return {
        "changed": sorted(p for p in before if p in after and before[p] != after[p]),
        "added": sorted(p for p in after if p not in before),
        "deleted": sorted(p for p in before if p not in after),
    }


EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
GIT_NAME = re.compile(r"(user\.name[= ]+['\"]?)[^'\"\s]+")


def redact(text):
    """Email addresses and git user names out: a run's agent may pick up the account's
    identity (e.g. for a git commit in its scratch folder), and the saved evidence is
    committed to the repo."""
    return GIT_NAME.sub(r"\1<name>", EMAIL.sub("<email>", text))


def scratch_dir(prefix):
    return tempfile.mkdtemp(prefix=prefix)
