"""One explicit mutation, two fresh copies, unchanged verification commands."""
import contextlib
import io
import json
import os
import shutil
import tempfile
from pathlib import Path


def cmd_challenge(v, repo, feature, mutation_file, timeout, record=True):
    """record=False: survey only. No state write, no receipts, one-line output (used by --auto)."""
    try:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        mutation = json.loads(Path(mutation_file).read_text(encoding="utf-8"))
        if not isinstance(mutation, dict) or any(
                not isinstance(mutation.get(k), str) or not mutation[k].strip()
                for k in ("file", "before", "after", "claim")):
            raise ValueError("mutation needs nonempty file, before, after and claim strings")
        target = Path(repo, mutation["file"]).resolve()
        target.relative_to(Path(repo).resolve())
        if not target.is_file() or mutation["before"] == mutation["after"]:
            raise ValueError("target must exist and replacement must change it")
        frozen = v.check_hashes(repo)
        if target in {Path(repo, name).resolve() for name in frozen} or target.name in (v.RECIPE, v.STATE):
            raise ValueError("mutate product code, never the recipe, state, tests or frozen oracles")
        source = target.read_text(encoding="utf-8")
        if source.count(mutation["before"]) != 1:
            raise ValueError("before must match exactly once; choose a more specific replacement")
        features, _ = v.parse(v.read(repo, v.RECIPE))
        selected = [f for f in features if f["name"] == feature]
        if len(selected) != 1 or not selected[0]["checks"] or not selected[0]["signals"]:
            raise ValueError("name one exact feature with checks and a declared fail-signal")
        recipe = v.parse_run(v.read(repo, v.RECIPE))
        if any(k == "run" for f in features for k, _ in f["checks"]) and not (recipe or {}).get("start"):
            raise ValueError("live run checks need a scratch-local Run start recipe")
        # A copied link could let a check or mutation write back into the source tree.
        for here, dirs, files in os.walk(repo):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            for name in dirs + files:
                path = Path(here, name)
                if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                    raise ValueError(f"scratch copy cannot contain links: {path.relative_to(repo)}")
    except (OSError, ValueError) as exc:
        print(f"CHALLENGE: invalid ({exc})")
        return 2

    original_tree = v.tree_sig(repo)
    original_state = v.load_state(repo)
    report = {"feature": feature, "mutation": mutation, "tree": original_tree,
              "check_signature": v.sha(json.dumps(frozen, sort_keys=True))}
    caught_checks = {}

    def trial(scratch):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = v.cmd_run(str(scratch), None, timeout, False)
        checks = v.load_state(str(scratch)).get("checks", {})
        return {"exit": code, "output": output.getvalue()[-8000:], "checks": checks,
                "checks_unchanged": v.check_hashes(str(scratch)) == frozen}

    try:
        with tempfile.TemporaryDirectory(prefix="verify-challenge-") as tmp:
            copies = [Path(tmp, "original"), Path(tmp, "mutated")]
            for scratch in copies:
                shutil.copytree(repo, scratch,
                                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", v.STATE))
            report["original"] = trial(copies[0])
            original = report["original"]
            relative = target.relative_to(Path(repo).resolve())
            original["product_unchanged"] = (copies[0] / relative).read_text(encoding="utf-8") == source
            verdict, reason = "inconclusive", "original recipe must pass with stable checks first"
            if original["exit"] == 0 and original["checks_unchanged"] and original["product_unchanged"]:
                changed = copies[1] / relative
                wrong_source = source.replace(mutation["before"], mutation["after"], 1)
                changed.write_text(wrong_source, encoding="utf-8")
                report["mutated"] = trial(copies[1])
                mutated = report["mutated"]
                mutated["mutation_unchanged"] = changed.read_text(encoding="utf-8") == wrong_source
                rows = [(kind, cmd, mutated["checks"].get(f"{feature}|{cmd}"))
                        for kind, cmd in selected[0]["checks"]]
                caught_checks = {f"{feature}|{cmd}": row for kind, cmd, row in rows
                                 if row and not row["ok"] and row["exit"] is not None
                                 and kind not in ("lint", "type", "types")
                                 and any(signal in row["output"] for signal in selected[0]["signals"])
                                 and not v.HARNESS_FAILURE.search(row["output"])}
                if not mutated["checks_unchanged"] or not mutated["mutation_unchanged"]:
                    reason = "check, oracle or mutated product changed during the run"
                elif rows and all(row and row["ok"] for _, _, row in rows):
                    verdict, reason = "survived", "selected feature checks still pass on the wrong implementation"
                elif caught_checks:
                    verdict, reason = "caught", "selected behavioral check rejected the mutation with its declared signal"
                else:
                    reason = "no expected behavioral rejection; inspect harness, timeout or signal mismatch"
            report.update(verdict=verdict, reason=reason)
    except (OSError, ValueError) as exc:
        report.update(verdict="inconclusive", reason=str(exc))

    if v.tree_sig(repo) != original_tree or v.load_state(repo) != original_state:
        print("CHALLENGE: inconclusive (source files or verification state changed during challenge; evidence not saved)")
        return 2
    if not record:
        print(f"CHALLENGE: {report['verdict']} ({report['reason']})")
        return {"caught": 0, "survived": 1, "inconclusive": 2}[report["verdict"]]
    original_state["challenge"] = report
    if report["verdict"] == "caught":
        receipts = original_state.setdefault("failures", {})
        for key, row in caught_checks.items():
            receipts[key] = {"signature": report["check_signature"], "exit": row["exit"],
                             "output": row["output"], "mutation": mutation, "tree": original_tree}
    v.save_state(repo, original_state)
    print(f"CHALLENGE: {report['verdict']} ({report['reason']})")
    print(f"Claim: {mutation['claim']}; mutation: {mutation['file']}")
    print(f"Evidence: {v.STATE} challenge; source tree {original_tree}")
    for label in ("original", "mutated"):
        if label in report:
            print(f"--- {label} ---\n{report[label]['output']}")
    return {"caught": 0, "survived": 1, "inconclusive": 2}[report["verdict"]]
