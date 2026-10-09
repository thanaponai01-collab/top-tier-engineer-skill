#!/usr/bin/env python3
"""features.py — the feature map behind feature-map.

FEATURES.md at the repo root says what the system has and how each feature is reached: route,
click target, shortcut, CLI command. Two commands:

  init   Draft FEATURES.md from the entry points found in the code, one feature per group.
         A draft: the agent names each feature, writes what it does, and labels it. Never
         overwrites an existing FEATURES.md.
  impact Which features a change touches, and the VERIFY.md sections to rerun. Files come from
         `--files a b`, else `git diff` against HEAD (`--base REF`) plus untracked files.
  check  Test the map against the code. STALE: a mapped entry point the code no longer has.
         Then what the map does NOT cover: entry points in the code the map lacks (unmapped),
         features with no VERIFY.md link, no status label, or no description.

An entry point is `kind: `anchor` @ file :: needle`. The check looks for the needle in the file (or
anywhere in the repo when no file is given). The needle defaults from the anchor by kind; write
`:: needle` when the default does not fit. A big map is an index: `include: features/<area>.md`
lines, each read in place (paths from the repo root; VERIFY.md includes are followed the same way).
Stdlib only.

FEATURES.md format:

  ## Checkout
  - what: Pay for the cart and get an order id.
  - route: `/checkout` @ src/app.py
  - click: `[data-testid=pay-btn]` @ src/cart.html
  - shortcut: `Ctrl+Enter` @ src/keys.js :: submitOrder
  - cli: `shop checkout` @ cli.py
  - code: src/checkout/
  - trace: `checkout` @ src/app.py > `place_order` @ src/svc.py > `orders` @ src/schema.sql
  - verify: Checkout
  - status: proven @ 3f2a1bc: drove /checkout in a browser, order id shown

`@ commit` on the status pins what the claim was true of; `check` reports it as drifted once a
file of that feature has changed since (unknown commits count as drifted).

kinds: route (or api), click, shortcut, cli, menu. status: proven | traced | suspected, then how.

Usage:
  python scripts/features.py init  [repo]
  python scripts/features.py check [repo] [--strict]

Exit: check 0 = nothing stale or broken; 1 = something stale or broken (or --strict and something is untraced, unmapped,
unlinked, unlabeled or undescribed); 2 = no FEATURES.md. Summary line:
  FEATURES: <f> features | <e> entry points, <s> stale | <b> broken | <t> untraced | <u> unmapped | <v> unlinked | <l> unlabeled | <d> undescribed
"""
import argparse, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams

MAP, VERIFY = "FEATURES.md", "VERIFY.md"
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "target",
             "vendor", ".tox", ".next", "fixture", "fixtures", "tests", "test", "__tests__"}
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".html",
            ".go", ".rs", ".rb", ".php", ".java", ".kt", ".cs"}
MAX_BYTES = 1_000_000
ENTRY_KINDS = {"route", "api", "click", "shortcut", "cli", "menu"}
LABELS = ("proven", "traced", "suspected")
MODS = {"ctrl": "mod", "control": "mod", "cmd": "mod", "command": "mod", "meta": "mod",
        "cmdorctrl": "mod", "commandorcontrol": "mod", "mod": "mod", "super": "mod",
        "option": "alt", "alt": "alt", "shift": "shift"}

# (kind, regex, what group 1 holds). Every hit is one entry point found in code.
DETECT = [
    ("route", r"@\w+\.(?:route|get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]"),
    ("route", r"\b(?:app|router|server|api)\.(?:get|post|put|delete|patch)\(\s*['\"`](/[^'\"`]*)"),
    ("route", r"\bpath\s*[=:]\s*\{?['\"](/[^'\"]*)['\"]"),
    ("click", r"data-(?:testid|test|cy|qa)\s*=\s*\{?['\"]([\w-]+)['\"]"),
    ("click", r"<button[^>]*\bid\s*=\s*['\"]([\w-]+)['\"]"),
    ("shortcut", r"\baccelerator\s*:\s*['\"]([^'\"]+)['\"]"),
    ("shortcut", r"\b(?:useHotkeys|hotkeys|Mousetrap\.bind|bindKey)\(\s*['\"]([^'\"]+)['\"]"),
    ("cli", r"\badd_parser\(\s*['\"]([\w-]+)['\"]"),
    ("cli", r"@\w+\.command\(\s*['\"]([\w-]+)['\"]"),
    ("cli", r"\.command\(\s*['\"]([\w-]+)[\s'\"<\[]"),
    ("cli", r"\bUse:\s*\"([\w-]+)"),
]
PAGE_FILE = re.compile(r"(?:^|/)(?:app|pages)/(.*?)/?(?:page|index)\.(?:tsx|jsx|js|ts)$")


# ---- needles ------------------------------------------------------------------------------

def norm_combo(text):
    """'CmdOrCtrl+Shift+O' -> 'mod+shift+o': same shortcut however the code spells the modifier."""
    parts = [p.strip().lower() for p in re.split(r"\+|(?<=\w)-(?=\w)", text) if p.strip()]
    mods = sorted({MODS[p] for p in parts[:-1] if p in MODS})
    return "+".join(mods + parts[-1:])


def default_needle(kind, anchor):
    a = anchor.strip()
    if kind in ("route", "api"):
        a = re.sub(r"^(?:GET|POST|PUT|PATCH|DELETE)\s+", "", a)
        a = re.split(r"[:{<\[*]", a)[0].rstrip("/") or "/"
        return a
    if kind == "click":
        m = re.search(r"[=~^$*|]?=\s*['\"]?([^'\"\]]+)", a) if a.startswith("[") else None
        if m:
            return m.group(1)
        return a.lstrip("#.")
    if kind == "cli":
        return a.split()[-1]
    if kind == "shortcut":
        return re.split(r"\+", a)[-1].strip().lower()
    return a


def identity(kind, anchor, needle):
    """What makes two entries the same entry point, so the map can be diffed against the code."""
    if kind in ("route", "api"):
        return ("route", default_needle("route", anchor))
    if kind == "shortcut":
        return ("shortcut", norm_combo(anchor))
    return (kind, needle)


# ---- reading the map ----------------------------------------------------------------------

def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


INCLUDE = re.compile(r"^(?:[-*]\s+)?include:\s*`?([^`\s]+)`?", re.I)


def load(repo, rel, seen=None):
    """A map file's text with every `include: <path>` line replaced by that file's text, so an
    index can list one area file per line. Paths are from the repo root, as in VERIFY.md."""
    seen = set() if seen is None else seen
    full = os.path.normpath(os.path.join(repo, rel))
    if full in seen:
        return ""
    seen.add(full)
    out = []
    for line in read(full).splitlines():
        m = INCLUDE.match(line.strip())
        out.append(load(repo, m.group(1).strip("'\""), seen) if m else line)
    return "\n".join(out)


def parse(text):
    """[{name, what, entries: [(kind, anchor, file, needle)], verify, status}]"""
    features, cur = [], None
    for line in text.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            cur = {"name": h.group(1), "what": "", "entries": [], "verify": "", "status": "", "trace": ""}
            features.append(cur)
            continue
        b = re.match(r"^\s*[-*]\s+([A-Za-z][\w-]*):\s*(.*?)\s*$", line)
        if not (b and cur):
            continue
        key, val = b.group(1).lower(), b.group(2)
        if key in ENTRY_KINDS:
            m = re.match(r"^`([^`]+)`(?:\s*@\s*(\S+))?(?:\s*::\s*(\S+))?", val)
            if m:
                cur["entries"].append((key, m.group(1), m.group(2) or "", m.group(3) or ""))
        elif key in ("what", "verify", "status", "trace"):
            cur[key] = val if key == "trace" else val.strip("`")
    return features


def is_todo(s):
    return not s or s.upper().startswith("TODO")


# ---- finding entry points in code ---------------------------------------------------------

def code_files(repo):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if os.path.splitext(f)[1] in CODE_EXT:
                p = os.path.join(root, f)
                if os.path.getsize(p) <= MAX_BYTES:
                    yield os.path.relpath(p, repo).replace("\\", "/"), p


def discover(repo):
    """[(kind, anchor, file)] for every entry point the code declares."""
    found, seen = [], set()

    def add(kind, anchor, rel):
        key = (kind, anchor, rel)
        if key not in seen:
            seen.add(key)
            found.append(key)

    for rel, path in code_files(repo):
        m = PAGE_FILE.search(rel)
        if m:
            add("route", "/" + re.sub(r"\([^)]*\)/?", "", m.group(1)).strip("/"), rel)
        text = read(path)
        for kind, rx in DETECT:
            for hit in re.finditer(rx, text):
                anchor = hit.group(1)
                if kind == "click" and "data-" not in hit.group(0):
                    anchor = "#" + anchor
                elif kind == "click":
                    anchor = f"[data-testid={anchor}]"
                add(kind, anchor, rel)
    return found


# ---- init ---------------------------------------------------------------------------------

def group_of(kind, anchor, rel):
    if kind == "route":
        seg = [s for s in anchor.strip("/").split("/") if s and s != "api" and not re.match(r"[:{<\[]", s)]
        return seg[0].replace("-", " ").title() if seg else "Home"
    if kind == "cli":
        return anchor.replace("-", " ").title()
    return re.sub(r"\.\w+$", "", rel.rsplit("/", 1)[-1]).replace("_", " ").replace("-", " ").title()


def cmd_init(repo):
    path = os.path.join(repo, MAP)
    if os.path.exists(path):
        print(f"{MAP} already exists at {path}; not overwriting. Edit it, or delete it first.")
        return 2
    groups = {}
    for kind, anchor, rel in discover(repo):
        groups.setdefault(group_of(kind, anchor, rel), []).append((kind, anchor, rel))
    out = [
        "# FEATURES", "",
        "What the system has and how each feature is reached. `features.py check` tests every entry",
        "point against the code. This is a draft found from the code: regroup by real feature, write",
        "what each does, add the entry points a scan cannot see, link each to VERIFY.md, label it,",
        "and replace every TODO.", "",
    ]
    for name in sorted(groups):
        out.append(f"## {name}")
        out.append("- what: TODO one sentence: what this feature does for its user")
        for kind, anchor, rel in groups[name]:
            out.append(f"- {kind}: `{anchor}` @ {rel}")
        out.append("- trace: TODO `handler` @ file > `what it calls` @ file > `effect` @ file")
        out.append("- verify: TODO name of the VERIFY.md section that proves it")
        out.append("- status: TODO proven | traced | suspected, then how you know")
        out.append("")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    n = sum(len(v) for v in groups.values())
    print(f"wrote {path}: {len(groups)} group(s), {n} entry point(s) found in code." +
          ("" if n else " None found; add a '## <feature>' section per feature by hand."))
    return 0


# ---- git: what changed, what a feature owns ------------------------------------------------

def git_lines(repo, *args):
    """Output lines of a git command run in repo, or None when git or the repo is unavailable."""
    try:
        r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8")
    except OSError:
        return None
    return r.stdout.splitlines() if r.returncode == 0 else None


def changed_files(repo, ref):
    """Files changed against ref (working tree included) plus untracked ones; None if git fails."""
    diff = git_lines(repo, "diff", "--name-only", "--relative", ref)
    if diff is None:
        return None
    return set(diff) | set(git_lines(repo, "ls-files", "--others", "--exclude-standard") or [])


def feature_files(f):
    """Every file a feature's map names: entry-point files and trace steps."""
    files = {rel for _k, _a, rel, _n in f["entries"] if rel}
    for raw in f["trace"].split(" > "):
        m = STEP.match(raw.strip())
        if m and m.group(2):
            files.add(m.group(2))
    return files


STATUS_COMMIT = re.compile(r"^\w+\s*@\s*([0-9a-fA-F]{4,40})")


def cmd_impact(repo, files, base):
    features = parse(load(repo, MAP))
    if not features:
        print(f"no {MAP} with features in {repo}; run `features.py init`.")
        return 2
    changed = set(f.replace("\\", "/") for f in files) if files else changed_files(repo, base)
    if changed is None:
        print(f"cannot read the change from git in {repo}; pass --files a b.")
        return 2
    claimed = set()
    hit = 0
    for f in features:
        own = feature_files(f)
        touched = sorted(own & changed)
        claimed |= own
        if touched:
            hit += 1
            print(f["name"])
            print("  changed: " + ", ".join(touched))
            print(f"  verify: {f['verify'] if not is_todo(f['verify']) else 'none linked, no check to rerun'}")
    loose = sorted(c for c in changed if os.path.splitext(c)[1] in CODE_EXT and c not in claimed)
    if loose:
        print("Changed code claimed by no feature (map gap, or shared code to check by hand):")
        for c in loose:
            print(f"  {c}")
    print(f"IMPACT: {len(changed)} changed file(s) | {hit} feature(s) affected | {len(loose)} claimed by no feature")
    return 0


# ---- check --------------------------------------------------------------------------------

def stale_reason(repo, kind, anchor, rel, needle, cache):
    """None when the entry point still exists, else why not."""
    needle = needle or default_needle(kind, anchor)
    fold = kind == "shortcut"
    if rel:
        p = os.path.join(repo, rel)
        if not os.path.isfile(p):
            return f"{rel} does not exist"
        if kind in ("route", "api") and needle.strip("/") and needle.strip("/") in rel:
            return None
        if needle == "/":
            return None
        text = read(p)
        hit = needle.lower() in text.lower() if fold else needle in text
        return None if hit else f"'{needle}' not found in {rel}"
    for r, p in code_files(repo):
        text = cache.setdefault(r, read(p))
        if (needle.lower() in text.lower()) if fold else (needle in text):
            return None
    return f"'{needle}' not found anywhere in the code"


STEP = re.compile(r"^`([^`]+)`(?:\s*@\s*(\S+))?(?:\s*::\s*(\S+))?")


def trace_problems(repo, trace):
    """[(tag, message)]: STALE when a step is not in its file, BROKEN when a step is not
    referenced from the step before it (the path is no longer a real call chain)."""
    out, prev_rel, prev_text = [], None, ""
    for raw in trace.split(" > "):
        m = STEP.match(raw.strip())
        if not m:
            out.append(("STALE", f"unreadable step: {raw.strip()[:40]}"))
            continue
        sym, rel, needle = m.group(1), m.group(2) or "", m.group(3) or m.group(1)
        text = read(os.path.join(repo, rel)) if rel else ""
        if not rel or not os.path.isfile(os.path.join(repo, rel)):
            out.append(("STALE", f"{sym}: {rel or 'no file given'} does not exist"))
            prev_rel, prev_text = None, ""
            continue
        if needle not in text:
            out.append(("STALE", f"{sym}: '{needle}' not found in {rel}"))
            prev_rel, prev_text = None, ""
            continue
        if prev_rel is not None:
            defined = re.search(rf"\b(?:def|function|func|fn|class|const|let|var)\s+{re.escape(needle)}\b", text)
            need = 2 if rel == prev_rel and defined else 1
            if prev_text.count(needle) < need:
                out.append(("BROKEN", f"{sym} is not called from {prev_rel}"))
        prev_rel, prev_text = rel, text
    return out


def cmd_check(repo, strict):
    path = os.path.join(repo, MAP)
    if not os.path.isfile(path):
        print(f"no {MAP} in {repo}. Run `features.py init` to draft one.")
        return 2
    features = parse(load(repo, MAP))
    if not features:
        print(f"{MAP} has no '## <feature>' sections; nothing to check.")
        return 2
    vtext = load(repo, VERIFY)
    vnames = {m.lower(): m for m in re.findall(r"(?m)^##\s+(.+?)\s*$", vtext) if m.lower() not in ("blind spots", "run") and not m.lower().startswith("journey:")}

    cache, mapped = {}, set()
    entries = stale = broken = untraced = unlinked = unlabeled = undescribed = drifted = 0
    head_changed = {}
    for f in features:
        print(f["name"])
        for kind, anchor, rel, needle in f["entries"]:
            entries += 1
            mapped.add(identity(kind, anchor, needle or default_needle(kind, anchor)))
            why = stale_reason(repo, kind, anchor, rel, needle, cache)
            stale += bool(why)
            where = f" @ {rel}" if rel else ""
            print(f"  {'STALE' if why else 'ok   '}  {kind}  {anchor}{where}" + (f"  ({why})" if why else ""))
        if not f["entries"]:
            print("  note  no entry points: how does a user reach this?")
        if is_todo(f["trace"]):
            untraced += 1
            print("  note  untraced: no 'trace:' path from entry point to effect")
        else:
            for tag, msg in trace_problems(repo, f["trace"]):
                stale += tag == "STALE"
                broken += tag == "BROKEN"
                print(f"  {tag:<5}  trace  {msg}")
        if is_todo(f["what"]):
            undescribed += 1
            print("  note  undescribed: no 'what:' line")
        if is_todo(f["verify"]):
            unlinked += 1
            print("  note  no verify link to a VERIFY.md section")
        elif vtext and f["verify"].lower() not in vnames:
            unlinked += 1
            print(f"  note  verify: '{f['verify']}' is not a section of {VERIFY}")
        if not f["status"].lower().startswith(LABELS):
            unlabeled += 1
            print("  note  no status label (proven | traced | suspected)")
        cm = STATUS_COMMIT.match(f["status"])
        if cm:
            ref = cm.group(1)
            if ref not in head_changed:
                head_changed[ref] = changed_files(repo, ref)
            moved = head_changed[ref]
            if moved is None:
                drifted += 1
                print(f"  note  drifted: status pinned to {ref}, which git cannot resolve")
            elif feature_files(f) & moved:
                drifted += 1
                print(f"  note  drifted: {', '.join(sorted(feature_files(f) & moved))} changed since {ref}")

    unmapped = []
    for kind, anchor, rel in discover(repo):
        if identity(kind, anchor, default_needle(kind, anchor)) not in mapped:
            unmapped.append((kind, anchor, rel))
    if unmapped:
        print("Unmapped entry points (in the code, not in the map):")
        for kind, anchor, rel in unmapped:
            print(f"  {kind}  {anchor}  @ {rel}")
    linked = {f["verify"].lower() for f in features}
    orphans = [n for k, n in vnames.items() if k not in linked]
    if orphans:
        print(f"In {VERIFY} but linked from no feature here: " + ", ".join(orphans))
        unlinked += len(orphans)

    print(f"FEATURES: {len(features)} features | {entries} entry points, {stale} stale | "
          f"{broken} broken | {untraced} untraced | {len(unmapped)} unmapped | {unlinked} unlinked | {unlabeled} unlabeled | {undescribed} undescribed | {drifted} drifted")
    if stale or broken or (strict and (untraced or unmapped or unlinked or unlabeled or undescribed or drifted)):
        return 1
    return 0


def main():
    utf8_streams()
    ap = argparse.ArgumentParser(description="Feature map: draft FEATURES.md, check it against the code.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init", help="draft FEATURES.md from the entry points found in code")
    i.add_argument("repo", nargs="?", default=".")
    c = sub.add_parser("check", help="test every mapped entry point against the code")
    c.add_argument("repo", nargs="?", default=".")
    c.add_argument("--strict", action="store_true",
                   help="also exit 1 on unmapped entry points, unlinked, unlabeled or undescribed features, and drifted status pins")
    m = sub.add_parser("impact", help="which features a change touches and which VERIFY.md sections to rerun")
    m.add_argument("repo", nargs="?", default=".")
    m.add_argument("--files", nargs="+", help="changed files (default: git diff against --base, plus untracked)")
    m.add_argument("--base", default="HEAD", help="git ref to diff against (default HEAD)")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    if a.cmd == "init":
        sys.exit(cmd_init(repo))
    if a.cmd == "impact":
        sys.exit(cmd_impact(repo, a.files, a.base))
    sys.exit(cmd_check(repo, a.strict))


if __name__ == "__main__":
    main()
