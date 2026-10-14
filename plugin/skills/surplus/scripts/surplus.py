#!/usr/bin/env python3
"""surplus.py — two probes that turn spare budget into evidence.

  repeat  Run a check many times and count the failures. A suite that is green once and red one run
          in five has a defect somewhere: in the code, in the test, or in what the test depends on.
            surplus.py repeat --times 30 -- python -m unittest
  mutate  Plant one small bug at a time in the named files (>= to >, == to !=, and to or, True to
          False, + 1 to - 1 ...), run the check after each, and list the bugs the check did not
          notice. Each survivor is a behaviour no test pins.
            surplus.py mutate shipping.py orders.py -- python -m unittest

The check must pass three times on the untouched code before `mutate` starts: a red check kills
every mutant, and a flaky one kills some at random, so run `repeat` first. A mutant counts as
killed only when the check fails on it twice; one that fails once and then passes is reported as
a flaky kill, because a test that went red by chance pinned nothing. Every file is restored byte for byte after each mutant. A copy is kept beside
it as <file>.surplus-orig while it runs; if one is left behind by a crash, `mutate` refuses to start
until you restore it (`--restore`). Stdlib only.

Exit codes: 0 nothing found (all runs passed / every mutant killed), 1 something found
(a failing run / a surviving mutant), 2 could not probe (bad usage, check red on untouched code).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

from _encoding import utf8_streams

# (name, pattern, replacement). Patterns avoid the neighbours that make a different operator:
# `->`, `=>`, `>>`, `<<`, `<-`.
OPERATORS = [
    (">= to >", r">=", ">"),
    ("<= to <", r"<=", "<"),
    ("> to >=", r"(?<![-=>])>(?![=>])", ">="),
    ("< to <=", r"(?<![<])<(?![=<-])", "<="),
    ("== to !=", r"(?<![=!])==(?!=)", "!="),
    ("!= to ==", r"!=(?!=)", "=="),
    ("and to or", r"\band\b", "or"),
    ("or to and", r"\bor\b", "and"),
    ("&& to ||", r"&&", "||"),
    ("|| to &&", r"\|\|", "&&"),
    ("True to False", r"\bTrue\b", "False"),
    ("False to True", r"\bFalse\b", "True"),
    ("true to false", r"\btrue\b", "false"),
    ("false to true", r"\bfalse\b", "true"),
    ("+ 1 to - 1", r"\+ 1\b", "- 1"),
    ("- 1 to + 1", r"(?<![-=(,\[])- 1\b", "+ 1"),
    ("not removed", r"\bnot ", ""),
]
COMMENT = re.compile(r"^\s*(#|//|\*|/\*|--)")


def run(cmd, cwd, timeout):
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return None, f"timed out after {timeout}s"


def in_string(line, pos):
    """Rough: an odd number of quotes before pos means pos sits inside a string literal."""
    head = line[:pos]
    return head.count('"') % 2 == 1 or head.count("'") % 2 == 1


def sites(text):
    """Every (line number, column, operator name, mutated line) for one file."""
    out = []
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        if COMMENT.match(line):
            continue
        code = line.split(" #", 1)[0] if " #" in line else line
        for name, pattern, repl in OPERATORS:
            for m in re.finditer(pattern, code):
                if in_string(line, m.start()):
                    continue
                out.append((number, m.start(), name, line[:m.start()] + repl + line[m.end():]))
    return out


def cmd_repeat(args):
    passed, failed, first_fail = 0, 0, None
    for i in range(1, args.times + 1):
        code, output = run(args.cmd, args.cwd, args.timeout)
        if code == 0:
            passed += 1
        else:
            failed += 1
            if first_fail is None:
                first_fail = (i, code, output)
    print(f"{passed}/{args.times} passed, {failed} failed  ({' '.join(args.cmd)})")
    if first_fail:
        i, code, output = first_fail
        tail = "\n".join(output.strip().splitlines()[-15:])
        print(f"first failure: run {i}, exit {code}\n{tail}")
        print("FLAKY: the same code passed and failed. Find what differs between runs "
              "(randomness, clock, order, shared state) before trusting any green." if passed else
              "RED on every run: this is a failing check, not a flaky one.")
        return 1
    return 0


def restore(path):
    backup = path + ".surplus-orig"
    if os.path.exists(backup):
        shutil.copyfile(backup, path)
        os.remove(backup)
        return True
    return False


def cmd_mutate(args):
    files = [os.path.join(args.cwd, f) if not os.path.isabs(f) else f for f in args.files]
    if args.restore:
        for path in files:
            print(("restored " if restore(path) else "nothing to restore for ") + path)
        return 0
    for path in files:
        if not os.path.isfile(path):
            print(f"no such file: {path}")
            return 2
        if os.path.exists(path + ".surplus-orig"):
            print(f"{path}.surplus-orig exists: an earlier run was interrupted. "
                  f"Run with --restore first, then check the file is what you expect.")
            return 2
    for attempt in range(1, 4):
        code, output = run(args.cmd, args.cwd, args.timeout)
        if code != 0:
            print(f"the check failed on the untouched code (run {attempt} of 3), so mutants would "
                  f"'die' for reasons of their own. Run `repeat` and fix or report that first.\n"
                  + "\n".join(output.strip().splitlines()[-10:]))
            return 2
    killed, survived, flaky, timeouts, tried = 0, [], [], 0, 0
    for path in files:
        with open(path, "rb") as fh:
            original = fh.read()
        text = original.decode("utf-8")
        lines = text.splitlines(keepends=True)
        shutil.copyfile(path, path + ".surplus-orig")
        try:
            for number, _col, name, mutated in sites(text):
                if tried >= args.max:
                    break
                tried += 1
                body = "".join(lines[:number - 1] + [mutated] + lines[number:])
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(body)
                code, _ = run(args.cmd, args.cwd, args.timeout)
                if code is None:
                    timeouts += 1
                elif code == 0:
                    survived.append((os.path.relpath(path, args.cwd), number, name,
                                     lines[number - 1].strip(), mutated.strip()))
                elif run(args.cmd, args.cwd, args.timeout)[0] == 0:
                    flaky.append((os.path.relpath(path, args.cwd), number, name))
                else:
                    killed += 1
        finally:
            with open(path, "wb") as fh:
                fh.write(original)
            os.remove(path + ".surplus-orig")
    print(f"{tried} mutants: {killed} killed, {len(survived)} survived, {len(flaky)} flaky kills, "
          f"{timeouts} timed out")
    if tried >= args.max:
        print(f"stopped at --max {args.max}; later sites were not tried")
    for rel, number, name, before, after in survived:
        print(f"SURVIVED {rel}:{number}  {name}\n    was: {before}\n    now: {after}")
    for rel, number, name in flaky:
        print(f"FLAKY KILL {rel}:{number}  {name}: failed once, then passed. The check is unstable here.")
    if survived or flaky:
        print("Each survivor is a change the check cannot see. Either a test should pin it, or the "
              "code there does not matter (say which, per survivor).")
        return 1
    return 0


def main(argv=None):
    utf8_streams()
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = []
    if "--" in argv:
        cut = argv.index("--")
        argv, cmd = argv[:cut], argv[cut + 1:]
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="Put the check command after `--`.")
    sub = parser.add_subparsers(dest="command", required=True)
    rep = sub.add_parser("repeat", help="run the check N times and count failures")
    rep.add_argument("--times", type=int, default=20)
    mut = sub.add_parser("mutate", help="plant one bug at a time and list the ones the check missed")
    mut.add_argument("files", nargs="+")
    mut.add_argument("--max", type=int, default=80, help="most mutants to try (default 80)")
    mut.add_argument("--restore", action="store_true",
                     help="put back <file>.surplus-orig left by an interrupted run")
    for p in (rep, mut):
        p.add_argument("--cwd", default=".", help="where to run the check (default .)")
        p.add_argument("--timeout", type=int, default=300, help="seconds per check run")
    args = parser.parse_args(argv)
    args.cmd = cmd
    args.cwd = os.path.abspath(args.cwd)
    if not cmd and not getattr(args, "restore", False):
        parser.error("give the check command after `--`")
    return cmd_repeat(args) if args.command == "repeat" else cmd_mutate(args)


if __name__ == "__main__":
    sys.exit(main())
