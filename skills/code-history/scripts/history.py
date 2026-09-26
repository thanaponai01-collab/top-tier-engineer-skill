#!/usr/bin/env python3
"""history.py — what git recorded about why a file, symbol or line is the way it is.

Git is one evidence source of several (issue tracker, docs, chat, error tracking).
This reads only that one, and says so. Three ways in:

  --file PATH          every commit that touched the file, following renames
  --symbol NAME        every commit with a changed line that mentions NAME
                       (git log -G, so a value edited in place shows up),
                       optionally limited with --in PATH
  --lines PATH:A,B     every commit that changed those lines (git log -L)

Per commit: short sha, date, subject, the body (where a reason usually lives), and
the references found in it (#123, PROJ-45). Reverts are counted; the oldest commit
is reported as the introduction. A commit body is a claim by its author, not a
fact about today's code, so read it against the code.

Stdlib only.

Usage:
  python scripts/history.py <repo> (--file PATH | --symbol NAME [--in PATH] | --lines PATH:A,B)
        [--max 40] [--json]

Summary line:
  HISTORY: <n> commits | introduced <sha> <date> | <r> reverts, <f> fixes | refs: <list> | sources: git only

Exit: 0 history found, 1 none found, 2 not a git repo or bad arguments.
"""
import argparse, json, re, subprocess, sys

SEP, END = "\x1f", "\x1e"
FMT = SEP.join(["%h", "%as", "%s", "%b"]) + END
REF = re.compile(r"(?<![\w/])#\d+\b|\b[A-Z][A-Z0-9]+-\d+\b")
FIX = re.compile(r"\b(fix(es|ed)?|hotfix|regression|bug)\b", re.I)
REVERT = re.compile(r"^revert\b", re.I)


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr


def parse(out):
    commits = []
    for rec in out.split(END):
        rec = rec.strip("\n")
        if SEP not in rec:
            continue
        sha, date, subject, body = (rec.split(SEP, 3) + [""])[:4]
        body = body.strip()
        text = subject + "\n" + body
        commits.append({
            "sha": sha.strip(), "date": date, "subject": subject, "body": body,
            "refs": REF.findall(text),
            "revert": bool(REVERT.match(subject)),
            "fix": bool(FIX.search(subject)),
        })
    return commits


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--file")
    g.add_argument("--symbol")
    g.add_argument("--lines", help="PATH:START,END")
    ap.add_argument("--in", dest="within", help="limit --symbol to this path")
    ap.add_argument("--max", type=int, default=40)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if git(a.repo, "rev-parse", "--git-dir")[0] != 0:
        print("not a git repo: " + a.repo, file=sys.stderr)
        return 2

    base = ["log", "--format=" + FMT, "-n", str(a.max)]
    if a.file:
        cmd = base + ["--follow", "--", a.file]
    elif a.symbol:
        pattern = re.sub(r"(\W)", lambda m: "\\" + m.group(1), a.symbol)
        cmd = base + ["-G" + pattern] + (["--", a.within] if a.within else [])
    else:
        m = re.match(r"^(.+):(\d+),(\d+)$", a.lines)
        if not m:
            print("--lines needs PATH:START,END", file=sys.stderr)
            return 2
        cmd = base + ["-s", "-L%s,%s:%s" % (m.group(2), m.group(3), m.group(1))]
    code, out, err = git(a.repo, *cmd)
    commits = parse(out) if code == 0 else []

    refs = []
    for c in commits:
        for r in c["refs"]:
            if r not in refs:
                refs.append(r)
    data = {
        "commits": commits,
        "introduced": commits[-1] if commits else None,
        "reverts": sum(c["revert"] for c in commits),
        "fixes": sum(c["fix"] for c in commits),
        "refs": refs,
        "sources": "git only",
    }
    if a.json:
        print(json.dumps(data, indent=2))
        return 0 if commits else 1
    if not commits:
        print("no history found for that target" + (" (" + err.strip() + ")" if err.strip() else ""))
        return 1
    for c in commits:
        tag = " [revert]" if c["revert"] else ""
        print("%s %s %s%s" % (c["sha"], c["date"], c["subject"], tag))
        for line in c["body"].splitlines()[:4]:
            print("    " + line)
    i = data["introduced"]
    print("HISTORY: %d commits | introduced %s %s | %d reverts, %d fixes | refs: %s | sources: git only"
          % (len(commits), i["sha"], i["date"], data["reverts"], data["fixes"],
             ", ".join(refs) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
