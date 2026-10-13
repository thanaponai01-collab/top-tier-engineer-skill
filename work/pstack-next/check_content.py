from pathlib import Path

root = Path(__file__).resolve().parents[2]
handoff = (root / "work/pstack-handoff.md").read_text(encoding="utf-8")
build = (root / "BUILD.md").read_text(encoding="utf-8")
evidence = root / "work/pstack-next/evidence.md"
assert evidence.is_file(), "PStack Next evidence record missing"
assert "[Evidence](pstack-next/evidence.md)" in handoff, "P01 handoff status does not link the expanded trial"
assert "P01 expanded-trial" in build and "pstack-next/evidence.md" in build, "BUILD does not point to the new proof"
assert "Next" in handoff and "reliability" in handoff.lower(), "handoff loses the broader evidence limit"
assert "No release" in evidence.read_text(encoding="utf-8"), "evidence omits scope limit"
print("PStack Next content: status, evidence, next-step limits, and BUILD links are present.")
