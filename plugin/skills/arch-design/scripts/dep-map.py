#!/usr/bin/env python3
"""dep-map.py — what the import graph says about a codebase's shape.

Reads the graph that latent-audit's graph-audit.py writes with `--edges FILE`, so nothing here
re-parses imports. It reports leads for arch-design's Judge step, never verdicts: each still has
to pass the deletion test and the same-reason test.

  1. CYCLES        — modules that (transitively) import each other.
  2. HUBS          — most-imported modules, with instability (out / in+out). A hub that also
                     imports a lot is where a change ripples; a hub that imports nothing is stable.
  3. PASS-THROUGH  — modules whose every function only forwards its own arguments to another
                     in-tree module, with how many modules import them.
  4. SEAMS         — Protocol / ABC classes and how many classes implement each: one implementer is
                     a hypothetical seam, two or more a real one.
  5. I/O           — modules that import a network, database or process library, with how many
                     modules import them.
  6. CO-CHANGE     — with `--cochange FILE` (change-map.py --json), which co-changing file pairs
                     have no import edge between them: shared knowledge nobody named.

Python only, stdlib only.

Usage:
  python scripts/dep-map.py <edges.json> [--cochange change.json] [--io LIB ...] [--json]

Summary line:
  DEP: <n> modules, <e> edges | cycles <c> | risky hubs <h> | pass-through <p> | seams <s> (<k> hypothetical) | io <i>
"""
import argparse, ast, json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams

IO_LIBS = {"urllib.request", "http.client", "requests", "httpx", "aiohttp", "socket", "smtplib",
           "sqlite3", "psycopg2", "sqlalchemy", "pymongo", "redis", "boto3", "subprocess"}
PROTOCOL_BASES = {"Protocol", "ABC"}
RISKY_FAN_IN = 5
RISKY_INSTABILITY = 0.5


def load(path):
    with open(path, encoding="utf-8") as f:
        g = json.load(f)
    return g["modules"], g["edges"]


def parse(path):
    try:
        with open(path, encoding="utf-8") as f:
            return ast.parse(f.read())
    except (OSError, SyntaxError, ValueError):
        return None


def cycles(mods, out):
    """Strongly connected components of two or more modules (Tarjan)."""
    sys.setrecursionlimit(max(10000, sys.getrecursionlimit()))
    index, low, on, stack, found, n = {}, {}, set(), [], [], [0]

    def visit(v):
        index[v] = low[v] = n[0]
        n[0] += 1
        stack.append(v)
        on.add(v)
        for w in out.get(v, ()):
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                found.append(sorted(comp))

    for m in sorted(mods):
        if m not in index:
            visit(m)
    return sorted(found)


def cycle_evidence(comp, edges):
    inside = set(comp)
    return [f"{e['from']}:{e['line']} -> {e['to']}" for e in edges
            if e["from"] in inside and e["to"] in inside]


def hubs(mods, edges):
    fin, fout = defaultdict(set), defaultdict(set)
    for e in edges:
        fin[e["to"]].add(e["from"])
        fout[e["from"]].add(e["to"])
    rows = []
    for m in mods:
        i, o = len(fin[m]), len(fout[m])
        if i:
            rows.append({"module": m, "fan_in": i, "fan_out": o,
                         "instability": round(o / (i + o), 2),
                         "risky": i >= RISKY_FAN_IN and o / (i + o) >= RISKY_INSTABILITY})
    rows.sort(key=lambda r: (-r["fan_in"], r["module"]))
    return rows


def imported_names(tree):
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            names |= {(a.asname or a.name).split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            names |= {a.asname or a.name for a in n.names}
    return names


def root_name(node):
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def forwards(fn, imported):
    """True when fn's whole body is one call to an imported name, passing only its own parameters."""
    body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Constant))]
    if len(body) != 1 or not isinstance(body[0], (ast.Return, ast.Expr)):
        return False
    call = body[0].value
    if not isinstance(call, ast.Call) or root_name(call.func) not in imported:
        return False
    params = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
    args = call.args + [k.value for k in call.keywords]
    return all(isinstance(a, ast.Starred) or (isinstance(a, ast.Name) and a.id in params) for a in args)


def pass_through(mods, trees, fan_in):
    rows = []
    for m, t in trees.items():
        if m.endswith("__init__"):
            continue
        body = [n for n in t.body if not isinstance(n, (ast.Import, ast.ImportFrom, ast.Expr, ast.Assign, ast.AnnAssign))]
        fns = [n for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if fns and len(fns) == len(body):
            imp = imported_names(t)
            if all(forwards(f, imp) for f in fns):
                rows.append({"module": m, "functions": len(fns), "imported_by": fan_in.get(m, 0)})
    return sorted(rows, key=lambda r: r["module"])


def seams(trees):
    classes = []  # (module, ClassDef)
    for m, t in trees.items():
        classes += [(m, n) for n in ast.walk(t) if isinstance(n, ast.ClassDef)]

    def base_names(c):
        return {b.id if isinstance(b, ast.Name) else b.attr for b in c.bases if isinstance(b, (ast.Name, ast.Attribute))}

    def methods(c):
        return {n.name for n in c.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("__")}

    rows = []
    for m, c in classes:
        if not base_names(c) & PROTOCOL_BASES:
            continue
        want = methods(c)
        impl = []
        for m2, c2 in classes:
            if c2 is c:
                continue
            explicit = c.name in base_names(c2)
            structural = "Protocol" in base_names(c) and want and want <= methods(c2)
            if explicit or structural:
                impl.append(f"{c2.name} ({m2})")
        rows.append({"seam": c.name, "module": m, "implementers": sorted(impl),
                     "verdict": "real" if len(impl) >= 2 else "hypothetical"})
    return sorted(rows, key=lambda r: (r["module"], r["seam"]))


def io_modules(mods, trees, fan_in, libs):
    rows = []
    for m, t in trees.items():
        hit = set()
        for n in ast.walk(t):
            names = []
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.module:
                names = [n.module]
            hit |= {x for x in names for lib in libs if x == lib or x.startswith(lib + ".")}
        if hit:
            rows.append({"module": m, "libs": sorted(hit), "imported_by": fan_in.get(m, 0)})
    return sorted(rows, key=lambda r: r["module"])


def cochange(mods, edges, change):
    linked = {frozenset((e["from"], e["to"])) for e in edges}

    def module_of(f):
        f = f.replace("\\", "/")
        hits = [m for m, p in mods.items() if p.replace("\\", "/").endswith("/" + f) or p.replace("\\", "/") == f]
        return hits[0] if len(hits) == 1 else None

    rows = []
    for c in change.get("coupled", []):
        a, b = module_of(c["a"]), module_of(c["b"])
        if a and b:
            rows.append({"a": c["a"], "b": c["b"], "shared": c["shared"],
                         "import_edge": frozenset((a, b)) in linked})
    return rows


def analyze(mods, edges, libs, change=None):
    out = defaultdict(set)
    fin = defaultdict(set)
    for e in edges:
        out[e["from"]].add(e["to"])
        fin[e["to"]].add(e["from"])
    trees, unparsed = {}, []
    for m, p in mods.items():
        t = parse(p)
        if t is None:
            unparsed.append(m)
        else:
            trees[m] = t
    fan_in = {m: len(v) for m, v in fin.items()}
    cyc = [{"modules": c, "edges": cycle_evidence(c, edges)} for c in cycles(mods, out)]
    linked = set(out) | set(fan_in)
    counted = [m for m in mods if not (m.endswith("__init__") and m not in linked)]
    r = {"modules": len(counted), "edges": len(edges), "cycles": cyc, "hubs": hubs(mods, edges)[:8],
         "pass_through": pass_through(mods, trees, fan_in), "seams": seams(trees),
         "io": io_modules(mods, trees, fan_in, libs), "unparsed": sorted(unparsed)}
    if change is not None:
        r["cochange"] = cochange(mods, edges, change)
    return r


def summary(r):
    hyp = sum(1 for s in r["seams"] if s["verdict"] == "hypothetical")
    risky = sum(1 for h in r["hubs"] if h["risky"])
    return (f"DEP: {r['modules']} modules, {r['edges']} edges | cycles {len(r['cycles'])} | risky hubs {risky} "
            f"| pass-through {len(r['pass_through'])} | seams {len(r['seams'])} ({hyp} hypothetical) | io {len(r['io'])}")


def main():
    utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("edges", help="JSON written by graph-audit.py --edges")
    ap.add_argument("--cochange", help="JSON from change-map.py --json")
    ap.add_argument("--io", action="append", default=[], help="extra I/O library prefix (repeatable)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        mods, edges = load(a.edges)
        change = None
        if a.cochange:
            with open(a.cochange, encoding="utf-8") as cf:
                change = json.load(cf)
    except (OSError, ValueError, KeyError) as e:
        print(f"DEP: blocked (cannot read the graph: {e})")
        return 2
    r = analyze(mods, edges, IO_LIBS | set(a.io), change)
    if a.json:
        r["summary"] = summary(r)
        print(json.dumps(r, indent=2))
        return 0
    else:
        print("CYCLES (modules that import each other, directly or through others)")
        for c in r["cycles"] or []:
            print("  " + " <-> ".join(c["modules"]))
            for e in c["edges"]:
                print("      " + e)
        if not r["cycles"]:
            print("  none")
        print("HUBS (most imported; instability = out / (in + out); risky = imported by 5+ and imports a lot)")
        for h in r["hubs"][:5]:
            print(f"  in {h['fan_in']:>3}  out {h['fan_out']:>3}  instability {h['instability']:.2f}"
                  f"{'  RISKY' if h['risky'] else ''}  {h['module']}")
        print("PASS-THROUGH (every function only forwards its own arguments)")
        for p in r["pass_through"] or []:
            print(f"  {p['module']}: {p['functions']} function(s), imported by {p['imported_by']} module(s)")
        if not r["pass_through"]:
            print("  none")
        print("SEAMS (Protocol / ABC; one implementer = hypothetical, two or more = real)")
        for s in r["seams"] or []:
            print(f"  {s['seam']} ({s['module']}): {len(s['implementers'])} implementer(s) -> {s['verdict']}"
                  + (": " + ", ".join(s["implementers"]) if s["implementers"] else ""))
        if not r["seams"]:
            print("  none")
        print("I/O (modules that import a network, database or process library)")
        for i in r["io"] or []:
            print(f"  {i['module']}: {', '.join(i['libs'])}; imported by {i['imported_by']} module(s)")
        if not r["io"]:
            print("  none")
        if "cochange" in r:
            print("CO-CHANGE (pairs that change together; import_edge says whether a dependency explains it)")
            for c in r["cochange"] or []:
                tag = "linked by an import" if c["import_edge"] else "NO IMPORT EDGE"
                print(f"  {c['shared']:>3}x  {c['a']}  <->  {c['b']}  [{tag}]")
        if r["unparsed"]:
            print("NOT READ (could not parse): " + ", ".join(r["unparsed"]))
    print(summary(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
