"""Replay the structural handoff checks; agent understanding is reviewed separately."""
from pathlib import Path
import importlib.util
import re
import sys

root = Path(__file__).resolve().parents[2]
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "workspace"
spec = importlib.util.spec_from_file_location("budget", root / "skills/recall/scripts/context_budget.py")
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)
brief = (workspace / "BRIEF.md").read_text(encoding="utf-8")
areas = [workspace / rel for rel in budget.includes(brief)]
current = brief + "\n" + "\n".join(p.read_text(encoding="utf-8") for p in areas)
assert set(map(int, re.findall(r"Area (\d+):", current))) == set(range(35)), "active decisions lost"
assert "JSON" in brief and "invoice_id" in brief and "amount" in brief, "intent missing"
assert "CSV only" in (workspace / "BRIEF.archive.md").read_text(encoding="utf-8"), "retired intent lost"
archive = (workspace / "BUILD.archive.md").read_text(encoding="utf-8")
assert set(map(int, re.findall(r"Controlled baseline receipt (\d+):", archive))) == set(range(200)), "history lost"
assert not any(row["over"] for row in budget.measure(str(workspace))), "startup notes over budget"
assert "credentials missing" in (workspace / "BUILD.md").read_text(encoding="utf-8"), "blocker lost"
print("PASS: 35 active decisions, 200 history receipts, current intent and blocker retained; budgets pass")
