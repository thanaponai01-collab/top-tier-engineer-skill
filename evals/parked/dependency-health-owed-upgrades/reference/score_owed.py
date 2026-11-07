"""Note, not a gate: how much of what was owed beyond the gate got done.

simplejson (imported by nothing) removed; the Docker base off end-of-life Python (>= 3.10);
Jinja2 off 2.11.3 (known holes) with the code migrated. Prints the count; passes at 2 of 3.
"""
import re, sys

def read(p):
    try:
        return open(p, encoding="utf-8").read().lower()
    except OSError:
        return ""

done = []
reqs = read("requirements.in") + read("requirements.txt")
done.append(("simplejson removed", "simplejson" not in reqs))
m = re.search(r"from\s+python:(\d+)\.(\d+)", read("Dockerfile"))
done.append(("docker base >= 3.10", bool(m) and (int(m.group(1)), int(m.group(2))) >= (3, 10)))
m = re.search(r"jinja2==(\d+)", read("requirements.txt"))
code = "".join(read(f"tripbook/{f}.py") for f in ("render",))
done.append(("jinja2 3.x, code migrated", bool(m) and int(m.group(1)) >= 3 and "contextfilter" not in code))
for what, yes in done:
    print(("done " if yes else "left ") + what)
n = sum(y for _, y in done)
print(f"{n}/3")
sys.exit(0 if n >= 2 else 1)
