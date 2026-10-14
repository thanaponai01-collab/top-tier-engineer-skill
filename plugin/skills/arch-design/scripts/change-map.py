#!/usr/bin/env python3
"""change-map.py — what the git history says about a codebase's boundaries.

The code shows what is connected. Only the history shows what actually changes
together. Three readings, all from `git log --name-only`:

  1. SPREAD          — how many modules each commit touched. A boundary drawn
                       well keeps one change inside one module.
  2. HIDDEN COUPLING — file pairs in DIFFERENT modules that keep changing in the
                       same commit: one concept with two owners, or a shared
                       assumption nobody named.
  3. HOTSPOTS        — files changed most often, weighted by size: where every
                       feature lands.

A module is a file's first --depth path components (app/reports/models.py at
depth 2 is app/reports). Only files that still exist are counted. Commits that
touch more than --max-files files (reformats, renames, vendoring) are skipped.

Stdlib only.

Usage:
  python scripts/change-map.py <repo> [--commits 300] [--depth 2]
        [--min-shared 3] [--max-files 30] [--exclude GLOB ...] [--json]

Summary line:
  CHANGE: <n> commits read | spread median <m>, p90 <p> modules | <k> coupled pairs
"""
import argparse, fnmatch, json, os, subprocess, sys
from collections import Counter
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams


def commits(repo, n):
    out = subprocess.run(
        ["git", "-C", repo, "log", "-n", str(n), "--no-merges", "--name-only", "--format=%x00%h %s"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    ).stdout
    for chunk in out.split("\0")[1:]:
        head, _, rest = chunk.partition("\n")
        yield head, [f for f in rest.splitlines() if f.strip()]


def module(path, depth):
    parts = path.split("/")
    return "/".join(parts[:-1][:depth]) or "."


def percentile(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * p))] if xs else 0


def analyze(repo, n, depth, min_shared, max_files, exclude):
    def keep(f):
        return os.path.isfile(os.path.join(repo, f)) and not any(fnmatch.fnmatch(f, g) for g in exclude)

    touched, pairs, spreads, worst = Counter(), Counter(), [], []
    read = skipped = 0
    for head, files in commits(repo, n):
        files = sorted({f for f in files if keep(f)})
        if not files:
            continue
        if len(files) > max_files:
            skipped += 1
            continue
        read += 1
        touched.update(files)
        mods = {module(f, depth) for f in files}
        spreads.append(len(mods))
        worst.append((len(mods), head))
        for a, b in combinations(files, 2):
            if module(a, depth) != module(b, depth):
                pairs[(a, b)] += 1

    coupled = []
    for (a, b), shared in pairs.items():
        if shared >= min_shared:
            # share of the rarer file's changes that dragged the other one along
            coupled.append({"a": a, "b": b, "shared": shared,
                            "confidence": round(shared / min(touched[a], touched[b]), 2)})
    coupled.sort(key=lambda c: (-c["shared"], -c["confidence"]))

    def lines(f):
        with open(os.path.join(repo, f), "rb") as fh:
            return fh.read().count(b"\n")

    hotspots = sorted(({"file": f, "changes": c, "lines": lines(f)} for f, c in touched.items()),
                      key=lambda h: -h["changes"] * max(h["lines"], 1))
    return {
        "commits_read": read, "commits_skipped_bulk": skipped, "depth": depth,
        "spread_median": percentile(spreads, 0.5), "spread_p90": percentile(spreads, 0.9),
        "widest_commits": [{"modules": m, "commit": h} for m, h in sorted(worst, key=lambda w: -w[0])[:5]],
        "coupled": coupled[:20], "hotspots": hotspots[:10],
    }


def main():
    utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo")
    ap.add_argument("--commits", type=int, default=300)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--min-shared", type=int, default=3)
    ap.add_argument("--max-files", type=int, default=30)
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        r = analyze(a.repo, a.commits, a.depth, a.min_shared, a.max_files, a.exclude)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"CHANGE: blocked (no readable git history at {a.repo}: {e})")
        return 2
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        print(f"SPREAD (modules touched per commit, module = first {r['depth']} path parts)")
        print(f"  median {r['spread_median']}, p90 {r['spread_p90']}; bulk commits skipped: {r['commits_skipped_bulk']}")
        for w in r["widest_commits"]:
            print(f"  {w['modules']:>3}  {w['commit']}")
        print("HIDDEN COUPLING (different modules, changed together)")
        for c in r["coupled"] or []:
            print(f"  {c['shared']:>3}x  conf {c['confidence']:.2f}  {c['a']}  <->  {c['b']}")
        if not r["coupled"]:
            print("  none at this threshold")
        print("HOTSPOTS (changes x lines)")
        for h in r["hotspots"]:
            print(f"  {h['changes']:>3} changes  {h['lines']:>5} lines  {h['file']}")
    print(f"CHANGE: {r['commits_read']} commits read | spread median {r['spread_median']}, "
          f"p90 {r['spread_p90']} modules | {len(r['coupled'])} coupled pairs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
