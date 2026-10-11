#!/usr/bin/env python3
"""history.py — give a fixture copy the git history a case needs, ending on fixture/ itself.

Some skills are about the past: why a line is the way it is, what was in flight, what a branch
changes. A folder of files cannot hold that, and git refuses a nested .git in this repo, so a case
describes its history in setup.py and run.py builds it in the scratch copy before the agent starts.

    from history import build
    build(repo, [
        {"message": "Add cache", "date": "2026-03-02T10:00:00", "files": {"cache.py": "TTL = 5\\n"}},
        {"message": "Raise TTL", "date": "2026-04-14T10:00:00", "files": {"cache.py": FINAL}},
    ])

Each commit lists the files it writes (FINAL = the fixture's own bytes, None = delete). After the
listed commits, every file still differing from fixture/ is committed as it is in fixture/ by a
last "final" commit, except the `uncommitted` paths: those stay at their last committed content in
HEAD and are fixture/ only in the working tree, which is how a case plants work in flight. A commit
may say "branch": "name" to create and switch to that branch first.

The working tree always ends identical to fixture/, so the workdir rules see no setup edits.
Stdlib only; needs git on PATH.
"""
import os, subprocess

FINAL = object()
NAME, EMAIL = "Eval Fixture", "fixture@example.invalid"


def git(repo, *args, date=None):
    env = dict(os.environ, GIT_AUTHOR_NAME=NAME, GIT_AUTHOR_EMAIL=EMAIL,
               GIT_COMMITTER_NAME=NAME, GIT_COMMITTER_EMAIL=EMAIL)
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    return subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false", *args],
                          cwd=repo, env=env, check=True, capture_output=True, text=True).stdout


def read_tree(repo):
    out = {}
    for base, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            path = os.path.join(base, name)
            with open(path, "rb") as fh:
                out[os.path.relpath(path, repo).replace(os.sep, "/")] = fh.read()
    return out


def write(repo, rel, data):
    path = os.path.join(repo, *rel.split("/"))
    if data is None:
        if os.path.exists(path):
            os.remove(path)
        return
    os.makedirs(os.path.dirname(path) or repo, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))


def build(repo, commits, uncommitted=(), final_message="Tidy up", final_date="2026-10-01T09:00:00"):
    final = read_tree(repo)
    for rel in final:
        write(repo, rel, None)
    git(repo, "init", "-q", "-b", "main")
    state = {}
    for c in commits:
        if c.get("branch"):
            git(repo, "checkout", "-q", "-b", c["branch"])
        for rel, data in c["files"].items():
            data = final[rel] if data is FINAL else data
            write(repo, rel, data)
            if data is None:
                state.pop(rel, None)
            else:
                state[rel] = data if isinstance(data, bytes) else data.encode("utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "--allow-empty", "-m", c["message"], date=c["date"])
    rest = {rel: data for rel, data in final.items()
            if rel not in uncommitted and state.get(rel) != data}
    gone = [rel for rel in state if rel not in final and rel not in uncommitted]
    if rest or gone:
        for rel, data in rest.items():
            write(repo, rel, data)
        for rel in gone:
            write(repo, rel, None)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", final_message, date=final_date)
    for rel in uncommitted:
        write(repo, rel, final.get(rel))
