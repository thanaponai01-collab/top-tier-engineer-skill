from pathlib import Path


root = Path(__file__).resolve().parents[2]
def read(name):
    return " ".join((root / name).read_text(encoding="utf-8").split())


guide = read("skills/drive/references/program-delivery.md")
drive = read("skills/drive/SKILL.md")
handoff = read("work/pstack-handoff.md")
build = read("BUILD.md")
comparison = read("docs/pstack/comparison.md")
adoption = read("docs/pstack/adoption-plan.md")
evidence = read("work/p09/evidence.md")

required_guide = [
    "Large agent programs",
    "graph before dispatch",
    "write ownership",
    "one executor",
    "integration check",
    "Stack delivery",
    "base SHA",
    "head SHA",
    "patch-id",
    "contiguous verified prefix",
    "bottom",
    "one PR at a time",
    "user authority",
    "queue",
]
missing = [phrase for phrase in required_guide if phrase.lower() not in guide.lower()]
assert not missing, "program-delivery guide misses: " + ", ".join(missing)
assert "program-delivery.md" in drive, "Drive entry point does not link the guide"
assert "P09 | Stack delivery and large agent programs" in handoff, "handoff has no P09 row"
assert "[Evidence](p09/evidence.md)" in handoff, "handoff does not link P09 evidence"
assert "Implemented; one bounded behavior trial passed" in handoff and "no forge mutation" in handoff, "handoff status or authority is missing"
assert "P09 adopts optional portable steps" in comparison, "comparison does not record the P09 scope"
assert "separate authorized implementation pass" in adoption, "adoption plan does not link the P09 pass"
assert "Before-edit behavior baseline" in evidence and "no Drive advantage" in evidence, "baseline evidence or limitation is missing"
assert "Drive found 8/8" in evidence and "does not establish reliability" in evidence, "post-change result or limits are missing"
assert "P09 slice" in build and "program-delivery.md" in build, "BUILD.md does not record the slice"
print("P09 content: Drive links bounded program and stack guidance; handoff, BUILD and baseline evidence are present.")
