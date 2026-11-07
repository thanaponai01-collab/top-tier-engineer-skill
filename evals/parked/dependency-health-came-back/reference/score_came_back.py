"""Note, not a gate: were the two pins the teammate's merge put back also fixed?"""
import re, sys

text = open("requirements.txt", encoding="utf-8").read().lower()
def pin(name):
    m = re.search(rf"(?m)^{name}==(\d+)\.(\d+)\.?(\d*)", text)
    return tuple(int(x or 0) for x in m.groups()) if m else None
u, y = pin("urllib3"), pin("pyyaml")
fixed = [u is not None and u >= (1, 26, 18), y is not None and y >= (5, 4, 0)]
print(f"urllib3 {u}: {'fixed' if fixed[0] else 'still holed'}")
print(f"pyyaml {y}: {'fixed' if fixed[1] else 'still holed'}")
sys.exit(0 if all(fixed) else 1)
