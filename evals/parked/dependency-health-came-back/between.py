"""A teammate's merge between the two sessions, the same in both arms: an old branch's
requirements.txt wins the conflict on two lines, so urllib3 goes back to 1.24.1 and PyYAML back to
5.3.1, both with known holes. requirements.in is untouched; urllib3 is only pulled in by requests,
so nothing there names it. Nothing else changes; the tests still pass."""
import os, re, sys

path = os.path.join(sys.argv[1], "requirements.txt")
with open(path, encoding="utf-8") as fh:
    text = fh.read()
for name, old in (("urllib3", "1.24.1"), ("pyyaml", "5.3.1")):
    # The pinned line, plus any `--hash` continuation lines (their hashes would no longer match).
    pat = re.compile(r"(?im)^" + name + r"==\S+(?:[ \t]*\\\n[ \t]+--hash=\S+)*")
    if pat.search(text):
        text = pat.sub(f"{name}=={old}", text, count=1)
    else:
        via = "requests" if name == "urllib3" else "-r requirements.in"
        text += f"{name}=={old}\n    # via {via}\n"
with open(path, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
