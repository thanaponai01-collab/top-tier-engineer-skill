#!/usr/bin/env python3
"""arch-design.py — the check behind docs/arch-design.md, the file an agent builds moves from.

The file is a work order with a shelf life. `check` says whether it can still be built from:

  BROKEN  a field a builder needs is missing, a named file or line is not in the repo, a one-way
          door has no recorded confirmation (or rests on a suspected fact), a strong finding has
          no number, or `after:` names a move that does not exist.
  STALE   a file the moves and findings name has changed since the commit the file is pinned to
          (`at:`). Not checked once `status: landed`.

Format (`key: value` bullets, so an agent reads it without prose):

  # ARCH-DESIGN
  - at: 3f2a1bc                    commit the analysis was true of
  - question: <one line>
  - yardstick: <change>; <change>; <change>
  - status: open | landed
  - verdict: clean | messy in places | tangled

  ## Finding 1: <title>            where, cost, badge (strong|worth exploring|speculative), evidence
  ## Decision 1: <title>           options, door, evidence  (one-way: `confirmed: <what the user said>`)
  ## Move 1: <title>              cost, pays, files, owner, callers, door, proof, effort, after

File references are `path` or `path:line`, relative to the repo root, comma-separated. Stdlib only.

Usage:
  python scripts/arch-design.py check [docs/arch-design.md | repo]

Exit: 0 = buildable; 1 = broken or stale; 2 = no file. Summary line:
  ARCH: <m> moves, <f> findings, <d> decisions | <b> broken | <s> stale
"""
import argparse, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams

DEFAULT = os.path.join("docs", "arch-design.md")
HEAD_KEYS = ("at", "question", "yardstick", "status", "verdict")
KEYS = {
    "finding": ("where", "cost", "badge", "evidence"),
    "decision": ("options", "door", "evidence"),
    "move": ("cost", "pays", "files", "owner", "callers", "door", "proof", "effort", "after"),
}
STATUS = ("open", "landed")
BADGES = ("strong", "worth exploring", "speculative")
LABELS = ("proven", "traced", "suspected")
SECTION = re.compile(r"^##\s+(Finding|Decision|Move)\s+(\d+)\s*:?\s*(.*)$", re.I)
BULLET = re.compile(r"^-\s+([\w-]+)\s*:\s*(.*)$")
REF = re.compile(r"^([^\s:]+?)(?::(\d+))?(?:\s.*)?$")


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout


def parse(text):
    head, sections, cur = {}, [], None
    for line in text.splitlines():
        m = SECTION.match(line)
        if m:
            cur = {"kind": m.group(1).lower(), "n": int(m.group(2)), "title": m.group(3).strip(), "f": {}}
            sections.append(cur)
            continue
        if line.startswith("## "):
            cur = None
            continue
        b = BULLET.match(line.strip())
        if b:
            (cur["f"] if cur else head)[b.group(1).lower()] = b.group(2).strip()
    return head, sections


def refs(value):
    out = []
    for tok in value.split(","):
        m = REF.match(tok.strip())
        if m and m.group(1).lower() != "nothing":
            out.append((m.group(1), int(m.group(2)) if m.group(2) else None))
    return out


def ref_problem(repo, path, line):
    full = os.path.join(repo, *path.split("/"))
    if not os.path.isfile(full):
        return f"{path}{':' + str(line) if line else ''} is not a file in the repo"
    if line:
        with open(full, encoding="utf-8", errors="replace") as fh:
            n = sum(1 for _ in fh)
        if line > n:
            return f"{path}:{line} is past the end of the file ({n} lines)"
    return None


def label(value):
    return value.split()[0].strip(",.:").lower() if value.split() else ""


def problems(repo, head, sections):
    out = []
    for k in HEAD_KEYS:
        if not head.get(k):
            out.append(f"header: missing `{k}`")
    if head.get("status") and head["status"].lower() not in STATUS:
        out.append(f"header: status `{head['status']}` is not one of {', '.join(STATUS)}")
    moves = {s["n"] for s in sections if s["kind"] == "move"}
    for s in sections:
        tag, f = f"{s['kind'].title()} {s['n']}", s["f"]
        for k in KEYS[s["kind"]]:
            if not f.get(k):
                out.append(f"{tag}: missing `{k}`")
        for k in ("where", "files"):
            for path, line in refs(f.get(k, "")):
                p = ref_problem(repo, path, line)
                if p:
                    out.append(f"{tag}: {p}")
        door = f.get("door", "").lower()
        if door and not door.startswith(("two-way", "one-way")):
            out.append(f"{tag}: door must start with two-way or one-way")
        if door.startswith("one-way"):
            said = re.search(r"confirmed\s*:\s*\S", f.get("door", ""), re.I) or f.get("confirmed")
            if not said:
                out.append(f"{tag}: one-way door has no recorded `confirmed:` (what the user said)")
            if s["kind"] == "decision" and label(f.get("evidence", "")) == "suspected":
                out.append(f"{tag}: a one-way door cannot rest on a suspected fact")
        if s["kind"] == "finding":
            if f.get("badge") and f["badge"].lower() not in BADGES:
                out.append(f"{tag}: badge `{f['badge']}` is not one of {', '.join(BADGES)}")
            if f.get("badge", "").lower() == "strong" and not re.search(r"\d", f.get("cost", "")):
                out.append(f"{tag}: a strong finding needs a number in `cost`")
        if s["kind"] in ("finding", "decision") and f.get("evidence") and label(f["evidence"]) not in LABELS:
            out.append(f"{tag}: evidence must start with proven, traced or suspected")
        if s["kind"] == "move":
            if f.get("effort") and f["effort"].strip().upper() not in ("S", "M", "L"):
                out.append(f"{tag}: effort must be S, M or L")
            after = f.get("after", "")
            if after and after.lower() != "nothing":
                for n in re.findall(r"\d+", after) or [None]:
                    if n is None or int(n) not in moves or int(n) == s["n"]:
                        out.append(f"{tag}: after `{after}` does not name another move")
                        break
    return out


def stale(repo, head, sections):
    sha = head.get("at", "")
    rc, _ = git(repo, "cat-file", "-e", f"{sha}^{{commit}}") if sha else (1, "")
    if rc != 0:
        return [f"`at: {sha}` is not a commit in this repo"]
    rc, out = git(repo, "diff", "--name-only", sha, "HEAD")
    changed = set(out.split()) if rc == 0 else set()
    named = []
    for s in sections:
        for k in ("where", "files"):
            for path, _ in refs(s["f"].get(k, "")):
                if path in changed and path not in named:
                    named.append(path)
    return [f"{p} changed after {sha}" for p in named]


def cmd_check(target):
    path = os.path.join(target, DEFAULT) if os.path.isdir(target) else target
    if not os.path.isfile(path):
        print(f"ARCH: no file at {path}")
        return 2
    with open(path, encoding="utf-8") as fh:
        head, sections = parse(fh.read())
    rc, top = git(os.path.dirname(os.path.abspath(path)), "rev-parse", "--show-toplevel")
    repo = top.strip() if rc == 0 else os.path.dirname(os.path.abspath(path))
    broken = problems(repo, head, sections)
    old = [] if head.get("status", "").lower() == "landed" else stale(repo, head, sections)
    for p in broken:
        print(f"BROKEN: {p}")
    for p in old:
        print(f"STALE: {p}")
    count = lambda k: sum(1 for s in sections if s["kind"] == k)
    print(f"ARCH: {count('move')} moves, {count('finding')} findings, {count('decision')} decisions"
          f" | {len(broken)} broken | {len(old)} stale")
    return 1 if broken or old else 0


def main():
    utf8_streams()
    ap = argparse.ArgumentParser(description="Check docs/arch-design.md is still buildable from.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="test the file's fields, references and pinned commit")
    c.add_argument("target", nargs="?", default=".")
    args = ap.parse_args()
    sys.exit(cmd_check(args.target))


if __name__ == "__main__":
    main()
