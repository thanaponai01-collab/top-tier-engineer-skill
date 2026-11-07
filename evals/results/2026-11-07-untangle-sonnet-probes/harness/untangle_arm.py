"""Make a fresh untangled tree with the plugin as it is in this checkout (Opus), for sp.py to probe.

python untangle_arm.py <id>      e.g. N1 -> <SP_WORK>/untangle/N1/{repo, result.json, notes.md}
Then: SP_ARMS="N1=<SP_WORK>/untangle/N1/repo" python sp.py batch N1 D1,D3,D4,P5,P6,P7 2
Same prompt as the compare run's skill arms (../../2026-11-07-untangle-compare/data/prompt-O1.txt).
"""
import json
import os
import shutil
import sys

import sp

PROMPT = """This codebase has gotten tangled. Untangle it.

The point is the next change: whoever touches this code next, most likely an AI agent, should spend \
less effort finding what to change, break less without noticing, and find the root cause of a bug \
faster. Keep what the program does exactly the same: same commands, same output.

When you are done, tell me what you changed and why, what you chose to leave alone, and how you know \
nothing broke."""


def main(rid):
    out = os.path.join(sp.WORK, "untangle", rid)
    if os.path.isfile(os.path.join(out, "result.json")):
        sys.exit(f"{rid} already done")
    sp.rmtree(out)
    os.makedirs(out)
    plug = sp.agent.stage_plugin(os.path.join(out, "plugin"))
    entry = os.path.join(plug, "skills", "untangle", "SKILL.md")
    prompt = (PROMPT + f"\n\nUse the untangle skill. The explicitly requested untangle skill is at {entry}. "
              "Read and follow that SKILL.md before starting. You are running unattended: nobody will "
              "answer questions, so make any choice the skill leaves to the user yourself.")
    repo = os.path.join(out, "repo")
    sp.copy_repo(sp.ARMS["orig"], repo)
    r = sp.agent.run_agent(prompt, repo, plugin_dir=plug, model="claude-opus-5-5", timeout=3600,
                           budget_usd=float(os.environ.get("BUDGET", "6")))
    open(os.path.join(out, "stream.jsonl"), "w", encoding="utf-8").write("\n".join(r["lines"]))
    _, st = sp.git(repo, "status", "--porcelain")
    if st.strip():
        sp.git(repo, "add", "-A")
        sp.sh(["git", "-c", "user.name=dev", "-c", "user.email=dev@example.com", "commit", "-qm",
               "untangle (uncommitted by agent)"], repo)
    report = next((json.loads(l).get("result") for l in reversed(r["lines"])
                   if l.startswith("{") and '"type":"result"' in l.replace(" ", "")), None)
    eff = sp.effort(r["lines"], [])
    files = sp.git(repo, "diff", "--name-status", sp.CUT, "HEAD")[1]
    notes = os.path.join(repo, ".untangle", "notes.md")
    if os.path.isfile(notes):
        shutil.copy(notes, os.path.join(out, "notes.md"))
    res = {"id": rid, "seconds": r["seconds"], "timed_out": r["timed_out"], **eff,
           "diff_files": files, "gate_done": "UNTANGLE-GATE: done" in "\n".join(r["lines"]),
           "report": report}
    json.dump(res, open(os.path.join(out, "result.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps({k: res[k] for k in ("id", "cost", "calls", "seconds", "gate_done")}))
    print(files)


if __name__ == "__main__":
    main(sys.argv[1])
