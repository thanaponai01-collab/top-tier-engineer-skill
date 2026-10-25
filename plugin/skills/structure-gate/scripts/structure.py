#!/usr/bin/env python3
"""structure.py - the mechanical side of the structure-gate skill.

A model that reads a small codebase finds its tangles well: the long function, the cycle, the
copied block. What it does not say is how much of the code any tool or test can reach. It reads
JavaScript held in a Python string and judges it like the rest, so the reader never learns that
no linter, complexity check or test will ever see that code. This keeps that denominator, makes
every region no parser entered get a reading or an UNKNOWN, and drafts an answer that opens with
the measured share.

  S PATHS ...             measure and list what needs a note
  S --gate [PATHS ...]    check the stages (paths default to the ones recorded in the notes):
    1 measure  the paths hold code and were measured; the share a parser entered is known
    2 account  every region no parser entered, and every finding over threshold, has a note
               in .structure/notes.md (the gate appends the slots it needs)
    3 answer   the notes give a verdict the measurement allows

`S` is `python structure.py`, run from the repo root. Stdlib only.
"""
import argparse, importlib.util, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _encoding import utf8_streams  # noqa: E402

_spec = importlib.util.spec_from_file_location("structure_report", os.path.join(HERE, "structure-report.py"))
report = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(report)

NOTES = os.path.join(".structure", "notes.md")
FILL = "[[fill"
VERDICTS = ("yes", "in places", "no")
UNENTERED_TAGS = ("read", "unknown")
FUNCTION_KINDS = {"function_lines": "lines", "cyclomatic": "complexity", "nesting_depth": "nesting"}
NOTE = re.compile(r"^\s*-\s*(.+?)\s*\|\s*(\w+)\s*:\s*(.*?)\s*$")
META = re.compile(r"^\s*-\s*(paths|verdict)\s*:\s*(.*?)\s*$", re.IGNORECASE)


def rel(path):
    try:
        path = os.path.relpath(path)
    except ValueError:
        pass
    return path.replace(os.sep, "/")


# ---------------- stage 1: measure ---------------------------------------------------
def measure(paths):
    """(analysis, {id: item}). An item is a region no parser entered or a finding over threshold."""
    r = report.analyze(paths, report.DEFAULT_THRESHOLDS)
    items = {}
    syntax = {rel(f.path) for f in r["findings"] if f.kind == "syntax"}
    for f in r["findings"]:
        p = rel(f.path)
        if f.kind == "opaque_code":
            hint = re.search(r"looks like ([\w/]+)", f.detail)
            items[f"{p}:{f.line}"] = {"kind": "unentered", "path": p, "lines": f.value, "sealed": True,
                                      "what": f"{f.value} lines inside a string literal"
                                              + (f", shaped like {hint.group(1)}" if hint else "")}
        elif f.kind == "syntax":
            items[p] = {"kind": "unentered", "path": p, "lines": None, "sealed": True,
                        "what": "does not parse, so nothing in it was measured"}
        elif f.kind in FUNCTION_KINDS:
            it = items.setdefault(f"{p}::{f.symbol}", {"kind": "finding", "path": p, "signal": "tangled function",
                                                       "signals": {}})
            it["signals"][FUNCTION_KINDS[f.kind]] = f.value
        elif f.kind == "file_lines":
            items.setdefault(p, {"kind": "finding", "path": p, "signal": "long file",
                                 "signals": {}})["signals"]["lines"] = f.value
        elif f.kind == "import_cycle":
            members = sorted(set(f.detail.split(": ", 1)[1].split(" -> ")))
            items["cycle: " + ", ".join(members)] = {"kind": "finding", "path": None, "signal": "import cycle",
                                                    "signals": {"modules": len(members)}}
        elif f.kind == "duplication":
            sites = f.detail.split("sites: ", 1)[1]
            group = tuple(sorted(s.rsplit(":", 1)[0] for s in sites.split(", ")))
            if not any(it.get("group") == group for it in items.values()):
                items[f"copy: {sites}"] = {"kind": "finding", "path": p, "group": group, "signal": "copied block",
                                           "signals": {"copies": len(sites.split(", "))}}
    for path in r["non_py"]:
        p = rel(path)
        n = len((report.read_text(path) or "").splitlines())
        if p not in syntax:
            items[p] = {"kind": "unentered", "path": p, "lines": n,
                        "what": f"{n} lines with no parser here (length and copies only)"}
    return r, items


# ---------------- stage 2: account ---------------------------------------------------
def read_notes(path=NOTES):
    out = {"paths": None, "verdict": None, "notes": {}, "text": ""}
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            out["text"] = fh.read()
    except OSError:
        return out
    for line in out["text"].splitlines():
        m = META.match(line)
        if m and "|" not in line:
            key, val = m.group(1).lower(), m.group(2)
            out[key] = [p.strip() for p in val.split(",") if p.strip()] if key == "paths" else val.strip().lower()
            continue
        m = NOTE.match(line)
        if m:
            out["notes"][m.group(1).replace("\\", "/").strip("`")] = (m.group(2).lower(), m.group(3))
    return out


def note_for(item_id, item, notes):
    """The note covering ITEM: its own, or (for code no parser entered) one on a folder above it."""
    if item_id in notes:
        return notes[item_id]
    if item["kind"] == "unentered":
        for nid, note in notes.items():
            if nid.endswith("/") and (item["path"] or "").startswith(nid):
                return note
    return None


def slot(item_id, item):
    if item["kind"] == "unentered":
        return (f"- {item_id} | read: [[fill: {item['what']}: what they hold, counted by reading "
                "(or `unknown: <why>` if you did not read them)]]")
    return f"- {item_id} | cost: [[fill: what this costs the next person who changes it, or `none: <why>`]]"


def append_slots(paths, items, notes):
    lines = []
    if notes["paths"] is None:
        lines.append(f"- paths: {', '.join(paths)}")
    lines += [slot(i, it) for i, it in items.items() if note_for(i, it, notes["notes"]) is None]
    if notes["verdict"] is None:
        lines.append("- verdict: [[fill: yes | in places | no]]")
    if not lines:
        return 0
    os.makedirs(os.path.dirname(NOTES), exist_ok=True)
    head = "" if notes["text"] else ("# Structure notes\n\nOne line per region no parser entered and per finding. "
                                     "`python structure.py --gate` checks them.\n\n")
    sep = "" if not notes["text"] or notes["text"].endswith("\n") else "\n"
    with open(NOTES, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(head + sep + "\n".join(lines) + "\n")
    return len(lines)


def account(items, notes):
    problems = []
    for i, it in items.items():
        tag, text = note_for(i, it, notes) or ("", "")   # the gate appended a slot for every item
        if FILL in text or not text.strip():
            problems.append(f"{i}: the slot is still empty. Fill it in {NOTES}")
        elif it["kind"] == "unentered":
            if tag not in UNENTERED_TAGS:
                problems.append(f"{i}: no parser entered this code, so it takes `read:` or `unknown:`, not `{tag}:`")
            elif tag == "read" and not re.search(r"\d", text):
                problems.append(f"{i}: `read:` says what you counted (blocks, branches, lines). "
                                "Count it, or mark it `unknown: <why>`")
        elif tag not in ("cost", "none"):
            problems.append(f"{i}: a finding takes `cost: <what it costs the next person>` or `none: <why>`")
    for nid in notes:
        if nid not in items and not (nid.endswith("/") and any(
                it["kind"] == "unentered" and (it["path"] or "").startswith(nid) for it in items.values())):
            problems.append(f"{nid}: noted, but not measured now. Remove the line, or fix the name")
    return problems


# ---------------- stage 3: answer ----------------------------------------------------
def accepted(note):
    tag, text = note
    return tag == "none" or (tag == "cost" and re.match(r"^\s*none\b", text, re.IGNORECASE))


def check_verdict(verdict, items, notes):
    if verdict is None or FILL in verdict:
        return [f"no verdict. Set `- verdict: yes | in places | no` in {NOTES}"]
    if verdict not in VERDICTS:
        return [f"verdict `{verdict}` is not one of: {' | '.join(VERDICTS)}"]
    found = {i: note_for(i, it, notes) for i, it in items.items()}
    unknown = [i for i, n in found.items() if n and n[0] == "unknown"]
    standing = [i for i, n in found.items() if items[i]["kind"] == "finding" and not (n and accepted(n))]
    # Code in a string (or a file that does not parse) is out of reach of every linter and test,
    # wherever it runs: reading it does not make it clean. A .js file only lacks a parser here.
    sealed = [i for i, it in items.items() if it.get("sealed")]
    if verdict == "no" and unknown:
        return [f"`no` over code nobody read ({', '.join(unknown[:3])}): unknown is not clean. "
                "Say `in places`, or read it and note what it holds"]
    if verdict == "no" and sealed:
        return [f"`no` while {', '.join(sealed[:3])} sits where no linter or test can reach it, here or "
                "anywhere: that is a finding, not clean. Say `in places` or `yes`"]
    if verdict == "no" and standing:
        return [f"`no` while findings stand ({', '.join(standing[:3])}). Say `in places`, or note each "
                "`cost: none: <why>` if the shape is the right call"]
    if verdict == "yes" and not standing and not unknown and not sealed:
        return ["`yes` but nothing measured or noted says so. Name what is tangled in a note, or say `no`"]
    return []


def measured(item):
    return ", ".join(f"{v} {k}" if k in ("lines", "modules", "copies") else f"{k} {v}"
                     for k, v in item["signals"].items())


def coverage_line(r, items):
    c = r["coverage"]
    unentered = [(i, it) for i, it in items.items() if it["kind"] == "unentered"]
    text = (f"Measured first: {c['code_lines']} code lines, {c['pct_entered']}% entered by a parser "
            f"({c['entered']} lines; deep on Python, length and copies only elsewhere).")
    if unentered:
        n = c["opaque"] + c["shallow"]
        where = ", ".join(f"`{i}` ({it['what']})" for i, it in unentered[:6])
        text += (f" {n} lines no parser entered: {where}. No complexity check, linter or test here reaches "
                 "them; what was not entered is unknown, not clean, and a reading below is a reading, "
                 "not a measurement.")
    else:
        text += " Nothing was left unentered."
    return text


def answer(r, items, notes, verdict, paths):
    print("\nANSWER (drafted from the measurement and the notes; give it, adding only context):\n")
    print(f"Is it spaghetti? {verdict.capitalize()}. [[fill: one sentence: where the tangle is, or why it is not]]")
    print(coverage_line(r, items))
    print("\n| signal | where | measured | what it costs the next person who changes it |\n|---|---|---|---|")
    for i, it in items.items():
        tag, text = note_for(i, it, notes)
        if it["kind"] == "unentered":
            print(f"| code no parser entered | `{i}` | {it['what']} | {'read by hand: ' if tag == 'read' else 'UNKNOWN: '}{text} |")
        else:
            print(f"| {it['signal']} | `{i}` | {measured(it)} | {text} |")
    flagged = {i.split("::", 1)[1] for i in items if "::" in i}
    print(f"\nUnder every threshold: {max(r['fn_count'] - len(flagged), 0)} of {r['fn_count']} functions. "
          f"Raw numbers: `python structure-report.py {' '.join(paths)}`.")
    print("Not covered: [[fill: what this run could not measure or did not read]]")
    unentered = [n for i, it in items.items() if it["kind"] == "unentered" for n in [note_for(i, it, notes)]]
    findings = sum(it["kind"] == "finding" for it in items.values())
    print(f"\nSTRUCTURE-GATE: done({r['coverage']['pct_entered']}% entered, {findings} findings, "
          f"{len(unentered)} unentered: {sum(n[0] == 'read' for n in unentered)} read, "
          f"{sum(n[0] == 'unknown' for n in unentered)} unknown; verdict {verdict})")


def gate(paths):
    notes = read_notes()
    paths = paths or notes["paths"]
    print("S = python \"" + os.path.abspath(__file__) + "\"")
    problems = {1: [], 2: [], 3: []}
    if not paths:
        problems[1].append("no paths. Run S --gate <paths the question is about>")
    elif [p for p in paths if not os.path.exists(p)]:
        problems[1].append(f"{', '.join(p for p in paths if not os.path.exists(p))}: not found from here. "
                           "Run from the repo root with paths relative to it")
    r = items = None
    if not problems[1]:
        r, items = measure(paths)
        if r["exit_code"] == 2:
            problems[1].append(f"no code files under {', '.join(paths)}: blocked, not clean")
    if not problems[1]:
        added = append_slots(paths, items, notes)
        if added:
            print(f"appended {added} slot(s) to {NOTES}")
            notes = read_notes()
        problems[2] = account(items, notes["notes"])
        if not problems[2]:
            problems[3] = check_verdict(notes["verdict"], items, notes["notes"])
        print(coverage_line(r, items))
    names = {1: "measure: the share a parser entered is known", 2: "account: every unentered region and finding noted",
             3: "answer: a verdict the measurement allows"}
    for g in (1, 2, 3):
        if problems[g]:
            state = f"open, {len(problems[g])} to fix"
        elif any(problems[e] for e in range(1, g)):
            state = "waits on the stage above"
        else:
            state = "holds"
        print(f"STAGE {g} {names[g]}: {state}")
        for line in problems[g]:
            print(f"  - {line}")
    open_stages = [g for g in (1, 2, 3) if problems[g]]
    if open_stages:
        print(f"STRUCTURE-GATE: open({', '.join(map(str, open_stages))}): fix the lines above, then S --gate")
        return 1
    answer(r, items, notes["notes"], notes["verdict"], paths)
    return 0


def overview(paths):
    r, items = measure(paths)
    print(coverage_line(r, items))
    for i, it in items.items():
        what = it["what"] if it["kind"] == "unentered" else f"{it['signal']}, {measured(it)}"
        print(f"  {'unentered' if it['kind'] == 'unentered' else 'finding  '}  {i}: {what}")
    print("next: S --gate " + " ".join(paths))
    return 0


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="Measure shape, account for what no parser entered, answer.")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--gate", action="store_true", help="check the three stages")
    a = ap.parse_args(argv)
    if a.gate:
        return gate(a.paths)
    return overview(a.paths or ["."])


if __name__ == "__main__":
    sys.exit(main())
