"""Generate fresh proof from committed inputs using the existing runner."""
import contextlib
import hashlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path


def cmd_ci(v, repo, plan_file, output, timeout):
    root, output = Path(repo).resolve(), Path(output).resolve()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True,
                                       stderr=subprocess.PIPE).strip()

    try:
        checkout = Path(git("rev-parse", "--show-toplevel")).resolve()
        if output == checkout or checkout in output.parents:
            raise ValueError("evidence output must be outside the checkout")
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"CI: invalid ({exc})")
        return 1
    output.mkdir(parents=True, exist_ok=True)
    report = {"verdict": "red", "stages": [], "challenges": []}
    log = io.StringIO()
    work = None
    state = {}

    def stage(name, action):
        with contextlib.redirect_stdout(log):
            code = action()
        report["stages"].append({"name": name, "exit": code})
        if code:
            raise ValueError(f"{name} failed (exit {code})")

    try:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        report["commit"] = git("rev-parse", "HEAD")
        if git("status", "--porcelain", "--untracked-files=all"):
            raise ValueError("CI requires a clean checkout of committed inputs")
        relative = root.relative_to(checkout).as_posix()
        archive_ref = report["commit"] + (":" + relative if relative != "." else "")
        tools = Path(__file__).parent
        report["verifier_hash"] = hashlib.sha256(b"".join(
            (tools / name).read_bytes() for name in ("verify.py", "challenge.py", "ci.py"))).hexdigest()
        report["project_path"] = relative
        with tempfile.TemporaryDirectory(prefix="verify-ci-") as tmp:
            archive = Path(tmp, "input.tar")
            with archive.open("wb") as fh:
                subprocess.run(["git", "-C", str(root), "archive", archive_ref], stdout=fh,
                               stderr=subprocess.PIPE, check=True)
            work = Path(tmp, "project")
            work.mkdir()
            with tarfile.open(archive) as tar:
                members = [m for m in tar.getmembers() if Path(m.name).name != v.STATE]
                if any(not (m.isfile() or m.isdir()) for m in members):
                    raise ValueError("CI inputs must not contain symlinks or special files")
                tar.extractall(work, members=members, filter="data")
            plan_path = (work / plan_file).resolve()
            plan_path.relative_to(work)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            if not isinstance(plan, list) or not plan:
                raise ValueError("CI plan must contain at least one feature mutation")
            for item in plan:
                if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip()
                                                     for k in ("feature", "mutation")):
                    raise ValueError("each plan item needs feature and mutation strings")
                (work / item["mutation"]).resolve().relative_to(work)
            report["input_tree"] = v.tree_sig(str(work))
            report["check_hashes"] = v.check_hashes(str(work))
            try:
                stage("baseline", lambda: v.cmd_baseline(str(work)))
                from challenge import cmd_challenge
                for item in plan:
                    try:
                        stage("challenge " + item["feature"], lambda: cmd_challenge(
                            v, str(work), item["feature"], str(work / item["mutation"]), timeout))
                    finally:
                        evidence = v.load_state(str(work)).get("challenge")
                        if evidence:
                            report["challenges"].append(evidence)
                stage("strict run", lambda: v.cmd_run(str(work), None, timeout, True))
                stage("status", lambda: v.cmd_status(str(work)))
                if v.check_hashes(str(work)) != report["check_hashes"]:
                    raise ValueError("frozen checks changed during CI")
                if git("rev-parse", "HEAD") != report["commit"] or git("status", "--porcelain", "--untracked-files=all"):
                    raise ValueError("source checkout changed during CI")
                report["verdict"] = "green"
            finally:
                state = v.load_state(str(work))
    except (OSError, ValueError, tarfile.TarError, subprocess.CalledProcessError) as exc:
        report["error"] = str(exc)
        log.write(f"CI failure: {exc}\n")
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    (output / "run.log").write_text(log.getvalue(), encoding="utf-8")
    print(log.getvalue())
    print(f"CI: {report['verdict']} | commit {report.get('commit', 'unknown')} | evidence {output}")
    return 0 if report["verdict"] == "green" else 1
