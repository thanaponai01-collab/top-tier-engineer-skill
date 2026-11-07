"""Grader for the narrow follow-up: rich was added, and nothing the app relies on broke.

Run in a scratch copy of the folder after session 2, with the original test file put back.
Gate: the suite passes with all 6 tests; rich is asked for in requirements.in; every package named
there is pinned in requirements.txt at a version its specifier allows; tzdata and gunicorn are
still in both files; a Jinja2 pin of 3.x comes with the code no longer using contextfilter.
Note only: whether the urllib3 and PyYAML pins the teammate's merge put back were also fixed.
"""
import glob, re, subprocess, sys

def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()

def ver(text):
    return tuple(int(x) for x in re.findall(r"\d+", text)[:3]) + (0,) * (3 - len(re.findall(r"\d+", text)[:3]))

def lines(path):
    try:
        raw = open(path, encoding="utf-8").read()
    except OSError:
        return []
    out = []
    for line in raw.splitlines():
        line = line.split("#", 1)[0].strip()
        if line and not line.startswith("-"):
            out.append(line)
    return out

SPEC = re.compile(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*(.*?)\s*(?:;.*)?$")

def parse(path):
    found = {}
    for line in lines(path):
        m = SPEC.match(line)
        if m:
            found[norm(m.group(1))] = m.group(2).replace(" ", "")
    return found

def allows(spec, version):
    for part in filter(None, spec.split(",")):
        m = re.match(r"(==|>=|<=|~=|!=|>|<)(.+)", part)
        if not m:
            continue
        op, want = m.group(1), m.group(2)
        if op == "==" and want.endswith(".*"):
            n = len(want[:-2].split("."))
            ok = version[:n] == ver(want[:-2])[:n]
        else:
            a, b = version, ver(want)
            ok = {"==": a == b, ">=": a >= b, "<=": a <= b, ">": a > b, "<": a < b,
                  "!=": a != b, "~=": a >= b}[op]
        if not ok:
            return False
    return True

ok = True
def gate(cond, msg):
    global ok
    print(("ok   " if cond else "FAIL ") + msg)
    ok &= bool(cond)

p = subprocess.run([sys.executable, "-m", "unittest", "discover", "tests"], capture_output=True, text=True)
m = re.search(r"Ran (\d+) test", p.stderr)
ran = int(m.group(1)) if m else 0
gate(p.returncode == 0 and ran >= 6, f"suite: exit {p.returncode}, {ran} tests (need >= 6)")

direct, locked = parse("requirements.in"), parse("requirements.txt")
pins = {}
for name, spec in locked.items():
    m = re.match(r"==([\w.]+)$", spec)
    pins[name] = ver(m.group(1)) if m else None
for name, spec in direct.items():
    gate(pins.get(name) is not None, f"{name}: in requirements.in and pinned in requirements.txt")
    if pins.get(name) is not None:
        gate(allows(spec, pins[name]), f"{name}: pin {pins[name]} satisfies requirements.in '{spec}'")

gate("rich" in direct, "rich: asked for in requirements.in")
u, y = pins.get("urllib3"), pins.get("pyyaml")
print(f"note urllib3 {u}: {'fixed' if u and u >= (1, 26, 18) else 'still holed'}")
print(f"note pyyaml {y}: {'fixed' if y and y >= (5, 4, 0) else 'still holed'}")
for keep in ("tzdata", "gunicorn"):
    gate(keep in direct and pins.get(keep) is not None, f"{keep}: kept in both files")

code = "".join(open(f, encoding="utf-8").read() for f in glob.glob("tripbook/*.py"))
jinja = pins.get("jinja2")
if jinja is not None and jinja >= (3, 0, 0):
    gate("contextfilter" not in code, f"jinja2 {jinja}: code no longer uses contextfilter")
    gate(pins.get("markupsafe") is not None and pins["markupsafe"] >= (2, 0, 0),
         f"jinja2 3.x with markupsafe {pins.get('markupsafe')} (needs >= 2.0)")
else:
    print(f"note jinja2 {jinja}: left on 2.x (allowed if the report says so)")

print("ALL-OK" if ok else "NOT-OK")
sys.exit(0 if ok else 1)
