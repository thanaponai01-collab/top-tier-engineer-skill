"""One explicit mutation, fresh scratch execution, unchanged verification commands.

prepare, mutable_target, judge and copy_repo are shared with `challenge --auto` (mutate.py)."""
import ast
import contextlib
import io
import json
import os
import shutil
import tempfile
from pathlib import Path


COPY_IGNORE = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".verify-state*")


def copy_repo(v, repo, dest):
    shutil.copytree(repo, dest, ignore=COPY_IGNORE)
    v.keep_state_in(dest)


def prepare(v, repo, feature, need_signal=True):
    """What every mutation of one feature shares, checked once: (frozen hashes, feature, Run recipe).
    Raises ValueError when the feature or the tree cannot be challenged. need_signal=False is for a
    survey that records no receipt (`challenge --auto`): any behavioral failure then counts as caught."""
    frozen = v.check_hashes(repo)
    features, _ = v.parse(v.read(repo, v.RECIPE), repo=repo)
    selected = [f for f in features if f["name"] == feature]
    if len(selected) != 1 or not selected[0]["checks"]:
        raise ValueError("name one exact feature with checks")
    if need_signal and not selected[0]["signals"]:
        raise ValueError("a challenge that records a receipt needs a declared fail-signal; "
                         "`--auto` surveys without one")
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
    return frozen, selected[0], recipe


def mutable_target(v, repo, frozen, rel):
    """The product file a mutation may change; raises ValueError for the recipe, state, tests or oracles."""
    target = Path(repo, rel).resolve()
    target.relative_to(Path(repo).resolve())
    if not target.is_file():
        raise ValueError("target must exist")
    if target in {Path(repo, name).resolve() for name in frozen} or target.name == v.RECIPE or v.is_state_file(target.name):
        raise ValueError("mutate product code, never the recipe, state, tests or frozen oracles")
    return target


def judge(v, feat, rows, intact, passing=None):
    """rows: [(kind, cmd, {ok, exit, output} or None)] for the feature's checks on the mutated tree.
    (verdict, reason, {check key: row} that rejected it with the declared signal)."""
    caught = {f"{feat['name']}|{cmd}": row for kind, cmd, row in rows
              if row and not row["ok"] and row["exit"] is not None
              and kind not in ("lint", "type", "types")
              and (not feat["signals"] or any(
                  signal in row["output"] and signal not in ((passing or {}).get(f"{feat['name']}|{cmd}") or "")
                  for signal in feat["signals"]))
              and not v.HARNESS_FAILURE.search(row["output"])}
    if not intact:
        return "inconclusive", "check, oracle or mutated product changed during the run", {}
    if rows and all(row and row["ok"] for _, _, row in rows):
        return "survived", "selected feature checks still pass on the wrong implementation", {}
    if caught:
        return "caught", ("selected behavioral check rejected the mutation with its declared signal"
                          if feat["signals"] else "a behavioral check failed (no fail-signal declared)"), caught
    if any(row and not row["ok"] and row["exit"] is not None
           and any(s in row["output"] and s in ((passing or {}).get(f"{feat['name']}|{cmd}") or "")
                   for s in feat["signals"])
           for _, cmd, row in rows):
        return "inconclusive", "original check also printed fail-signal on pass (SIGNAL IN PASS)", {}
    return "inconclusive", "no expected behavioral rejection; inspect harness, timeout or signal mismatch", {}


def cmd_challenge(v, repo, feature, mutation_file, timeout, record=True):
    """record=False: survey only. No state write, no receipts, one-line output."""
    try:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        mutation = (mutation_file if isinstance(mutation_file, dict)
                    else json.loads(Path(mutation_file).read_text(encoding="utf-8")))
        if not isinstance(mutation, dict) or any(
                not isinstance(mutation.get(k), str) or not mutation[k].strip()
                for k in ("file", "before", "after", "claim")):
            raise ValueError("mutation needs nonempty file, before, after and claim strings")
        if mutation["before"] == mutation["after"]:
            raise ValueError("target must exist and replacement must change it")
        frozen, feat, recipe = prepare(v, repo, feature)
        target = mutable_target(v, repo, frozen, mutation["file"])
        source = target.read_text(encoding="utf-8")
        if source.count(mutation["before"]) != 1:
            raise ValueError("before must match exactly once; choose a more specific replacement")
        wrong_source = source.replace(mutation["before"], mutation["after"], 1)
        if target.suffix.lower() == ".py":
            try:
                src_ast = ast.dump(ast.parse(source))
                mut_ast = ast.dump(ast.parse(wrong_source))
            except SyntaxError as exc:
                raise ValueError(f"mutation introduces a Python syntax error: {exc.msg}") from exc
            if src_ast == mut_ast:
                raise ValueError("mutation changes only comments or formatting; mutate executable code")
    except (OSError, ValueError) as exc:
        print(f"CHALLENGE: invalid ({exc})")
        return 2

    original_tree = v.tree_sig(repo)
    original_state = v.load_state(repo)
    report = {"feature": feature, "mutation": mutation, "tree": original_tree,
              "check_signature": v.sha(json.dumps(frozen, sort_keys=True))}
    caught_checks = {}

    def trial(scratch, only_feat=False):
        if only_feat and not recipe:
            checks, out_lines, any_fail = {}, [feature], False
            for kind, cmd in feat["checks"]:
                ok, code, out, secs, _ = v.attempt(cmd, str(scratch), timeout, 1)
                checks[f"{feature}|{cmd}"] = {"ok": ok, "exit": code, "output": out[-4000:]}
                tag = "PASS" if ok else "FAIL"
                extra = "" if ok else (" (timeout)" if code is None else f" (exit {code})")
                out_lines.append(f"  {tag}  {kind}  {cmd}  [{secs:.1f}s]{extra}")
                if not ok:
                    any_fail = True
                    out_lines.extend(f"        {ln}" for ln in out.rstrip().splitlines()[-v.TAIL_LINES:])
            return {"exit": 1 if any_fail else 0, "output": ("\n".join(out_lines) + "\n")[-8000:],
                    "checks": checks, "checks_unchanged": v.check_hashes(str(scratch)) == frozen}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = v.cmd_run(str(scratch), None, timeout, False, use_cache=False, judge_reach=False)
        checks = v.load_state(str(scratch)).get("checks", {})
        return {"exit": code, "output": output.getvalue()[-8000:], "checks": checks,
                "checks_unchanged": v.check_hashes(str(scratch)) == frozen}

    try:
        with tempfile.TemporaryDirectory(prefix="verify-challenge-") as tmp:
            scratch = Path(tmp, "original")
            copy_repo(v, repo, scratch)
            report["original"] = trial(scratch, only_feat=False)
            original = report["original"]
            relative = target.relative_to(Path(repo).resolve())
            original["product_unchanged"] = (scratch / relative).read_text(encoding="utf-8") == source
            verdict, reason = "inconclusive", "original recipe must pass with stable checks first"
            if original["exit"] == 0 and original["checks_unchanged"] and original["product_unchanged"]:
                if v.tree_sig(str(scratch)) != original_tree:
                    scratch = Path(tmp, "mutated")
                    copy_repo(v, repo, scratch)
                changed = scratch / relative
                changed.write_text(wrong_source, encoding="utf-8")
                report["mutated"] = trial(scratch, only_feat=True)
                mutated = report["mutated"]
                mutated["mutation_unchanged"] = changed.read_text(encoding="utf-8") == wrong_source
                rows = [(kind, cmd, mutated["checks"].get(f"{feature}|{cmd}")) for kind, cmd in feat["checks"]]
                passing = {k: r.get("output", "") for k, r in (original.get("checks") or {}).items()
                           if isinstance(r, dict) and r.get("ok")}
                verdict, reason, caught_checks = judge(
                    v, feat, rows, mutated["checks_unchanged"] and mutated["mutation_unchanged"], passing)
            report.update(verdict=verdict, reason=reason)
    except (OSError, ValueError) as exc:
        report.update(verdict="inconclusive", reason=str(exc))

    # Receipts other agents add meanwhile are additive evidence; anything else changing is not.
    def settled(state):
        return {k: val for k, val in state.items() if k != "failures"}

    if v.tree_sig(repo) != original_tree or settled(v.load_state(repo)) != settled(original_state):
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
                             "output": row["output"], "mutation": mutation, "tree": original_tree,
                             "agent": v.agent_name()}
    v.save_state(repo, original_state)
    print(f"CHALLENGE: {report['verdict']} ({report['reason']})")
    print(f"Claim: {mutation['claim']}; mutation: {mutation['file']}")
    print(f"Evidence: {v.STATE} challenge; source tree {original_tree}")
    for label in ("original", "mutated"):
        if label in report:
            print(f"--- {label} ---\n{report[label]['output']}")
    return {"caught": 0, "survived": 1, "inconclusive": 2}[report["verdict"]]
