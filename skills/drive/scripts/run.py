#!/usr/bin/env python3
"""Durable evidence gate for drive. Checks run; deploy commands never run here.

Stdlib only. Local hashes detect accidental edits, not a malicious writer.
Use protected CI checks and host permissions for an independent trust boundary.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

STATE = "RUN.json"
SKIP = {".git", "__pycache__", ".pytest_cache"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(root, state):
    # A killed writer leaves the previous complete record, never half a JSON file.
    tmp = root / (STATE + ".tmp")
    with tmp.open("w", encoding="utf-8") as stream:
        json.dump(state, stream, indent=2, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, root / STATE)


def files_hash(root, names):
    files = {}
    for name in names:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or path == root / STATE:
            raise ValueError("input must be inside the repo and cannot be RUN.json")
        if not path.exists():
            raise ValueError("missing input: " + name)
        candidates = path.rglob("*") if path.is_dir() else [path]
        for file in candidates:
            if not file.is_file() or any(p in SKIP for p in file.relative_to(root).parts):
                continue
            if not file.resolve().is_relative_to(root):
                raise ValueError("input symlink leaves repo: " + str(file))
            rel = file.relative_to(root).as_posix()
            if rel in {STATE, STATE + ".tmp"}:
                continue
            files[rel] = hashlib.sha256(file.read_bytes()).hexdigest()
    if not files:
        raise ValueError("inputs contain no files")
    return digest(files)


def strings(value):
    return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value)


def validate(contract):
    if not isinstance(contract, dict):
        raise ValueError("contract must be an object")
    if not isinstance(contract.get("goal"), str) or not contract["goal"].strip():
        raise ValueError("goal is required")
    if contract.get("target") not in {"local", "staging", "production"}:
        raise ValueError("target must be local, staging or production")
    for key in ("max_attempts", "timeout_seconds", "max_seconds"):
        if type(contract.get(key)) is not int or contract[key] < 1:
            raise ValueError(key + " must be a positive integer")
    stages = contract.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ValueError("stages are required")
    ids = []
    for stage in stages:
        if not isinstance(stage, dict) or not isinstance(stage.get("id"), str) or not stage["id"]:
            raise ValueError("each stage needs an id")
        if not isinstance(stage.get("skill"), str) or not stage["skill"].strip():
            raise ValueError("each stage needs a skill or direct")
        for key in ("command", "inputs"):
            if not strings(stage.get(key)):
                raise ValueError("each stage needs nonempty " + key)
        ids.append(stage["id"])
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate stage id")
    criteria = contract.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise ValueError("acceptance criteria are required")
    for criterion in criteria:
        if (not isinstance(criterion, dict) or criterion.get("stage") not in ids
                or not isinstance(criterion.get("statement"), str) or not criterion["statement"].strip()):
            raise ValueError("each criterion needs a statement and a matching stage")
    if not strings(contract.get("oracle_files")):
        raise ValueError("oracle_files must name the frozen checks/spec")
    if contract["target"] != "local" and (len(ids) < 2 or ids[-2:] != ["ship", "watch"]):
        raise ValueError("release targets must end with ship and watch checks")
    actions = contract.get("actions", [])
    if not isinstance(actions, list):
        raise ValueError("actions must be a list")
    action_ids = []
    for action in actions:
        if not isinstance(action, dict) or not isinstance(action.get("id"), str) or not action["id"]:
            raise ValueError("each action needs an id")
        if action.get("stage") not in ids or not strings(action.get("probe")):
            raise ValueError("each action needs a stage and a replay-safe probe")
        if action.get("environment") not in {"local", "staging", "production"}:
            raise ValueError("each action needs its exact environment")
        if not isinstance(action.get("authorization", ""), str):
            raise ValueError("authorization must quote the user or be empty")
        if type(action.get("required", False)) is not bool:
            raise ValueError("required must be boolean")
        action_ids.append(action["id"])
    if len(set(action_ids)) != len(action_ids):
        raise ValueError("duplicate action id")


def load(root):
    state = read(root / STATE)
    validate(state["contract"])
    if digest(state["contract"]) != state["contract_hash"]:
        raise ValueError("contract changed; preserve the run and obtain a revised contract")
    if files_hash(root, state["contract"]["oracle_files"]) != state["oracle_hash"]:
        raise ValueError("oracle changed; do not rebaseline to make the work pass")
    return state


def budget(state):
    if time.time() - state["started_at"] >= state["contract"]["max_seconds"]:
        raise ValueError("run time budget exhausted; stop with a reason and next action")


def execute(root, state, command):
    budget(state)
    timeout = min(state["contract"]["timeout_seconds"],
                  state["contract"]["max_seconds"] - (time.time() - state["started_at"]))
    argv = [sys.executable if part == "python" else part for part in command]
    start = time.time()
    try:
        proc = subprocess.run(argv, cwd=root, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=max(0.01, timeout),
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        code, output = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        code, output = 124, "check timed out; external state may be unknown"
    except OSError as exc:
        code, output = 127, str(exc)
    return {"command": command, "exit": code, "output": output[-12000:],
            "at": start, "seconds": round(time.time() - start, 3)}


def pending(state):
    return [name for name, record in state["journal"].items() if record["result"] == "unknown"]


def required_actions(state):
    for action in state["contract"].get("actions", []):
        if action.get("required") and state["journal"].get(action["id"], {}).get("result") != "applied":
            raise ValueError("required action not applied: " + action["id"])


def next_stage(state):
    return next((s for s in state["contract"]["stages"] if s["id"] not in state["proofs"]), None)


def gate(root, state):
    if state["status"] != "complete":
        raise ValueError(state["status"] + ": " + state.get("reason", "next stage or finish required"))
    if pending(state):
        raise ValueError("unresolved actions: " + ", ".join(pending(state)))
    required_actions(state)
    for stage in state["contract"]["stages"]:
        proof = state["proofs"].get(stage["id"])
        if not proof or proof["exit"] != 0:
            raise ValueError("missing passing evidence: " + stage["id"])
        if proof["inputs_hash"] != files_hash(root, stage["inputs"]):
            raise ValueError("stale evidence: " + stage["id"])


def check_stage(root, state, stage):
    name = stage["id"]
    attempts = state["attempts"].get(name, 0)
    if attempts >= state["contract"]["max_attempts"]:
        raise ValueError("attempt budget exhausted: " + name)
    before = files_hash(root, stage["inputs"])
    state["attempts"][name] = attempts + 1
    state["status"] = "active"
    state["proofs"].pop(name, None)
    save(root, state)  # Reserve attempt before a crash or tool call.
    proof = execute(root, state, stage["command"])
    if before != files_hash(root, stage["inputs"]):
        proof["exit"] = 1
        proof["output"] += "\ninputs changed during check"
    proof["inputs_hash"] = before
    state["history"].append({"stage": name, **proof})
    if proof["exit"] == 0:
        state["proofs"][name] = proof
    save(root, state)
    print(proof["output"])
    if proof["exit"]:
        raise ValueError("check failed: " + name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    subs = parser.add_subparsers(dest="operation", required=True)
    subs.add_parser("init").add_argument("contract")
    subs.add_parser("status")
    subs.add_parser("next")
    subs.add_parser("check").add_argument("stage")
    subs.add_parser("finish")
    for name in ("begin", "reconcile"):
        subs.add_parser(name).add_argument("action")
    stop = subs.add_parser("stop")
    stop.add_argument("status", choices=["blocked", "failed"])
    stop.add_argument("--reason", required=True)
    stop.add_argument("--next", required=True)
    subs.add_parser("resume")
    args = parser.parse_args(argv)
    root = Path(args.repo).resolve()
    try:
        if args.operation == "init":
            if (root / STATE).exists():
                raise ValueError("RUN.json already exists; resume or archive explicitly")
            contract = read(Path(args.contract))
            validate(contract)
            for stage in contract["stages"]:
                files_hash(root, stage["inputs"])
            state = {"version": 1, "contract": contract, "contract_hash": digest(contract),
                     "oracle_hash": files_hash(root, contract["oracle_files"]),
                     "started_at": time.time(), "status": "active", "proofs": {},
                     "attempts": {}, "journal": {}, "history": []}
            save(root, state)
        else:
            # An honest failure must remain recordable even with a changed oracle.
            if args.operation == "stop":
                raw = (root / STATE).read_bytes()
                try:
                    state = json.loads(raw.decode("utf-8-sig"))
                    if not isinstance(state, dict):
                        raise ValueError("run record must be an object")
                except (ValueError, UnicodeError):
                    # Preserve damaged evidence before allowing an honest terminal handoff.
                    backup = "RUN.invalid." + hashlib.sha256(raw).hexdigest()[:16] + ".json"
                    (root / backup).write_bytes(raw)
                    state = {"invalid_record": backup}
            else:
                state = load(root)
            if args.operation == "status":
                gate(root, state)
            elif args.operation == "next":
                stage = next_stage(state)
                print(json.dumps({"status": state["status"], "next": stage,
                                  "unresolved": pending(state)}, ensure_ascii=False))
                return 0
            elif args.operation == "stop":
                if not args.reason.strip() or not args.next.strip():
                    raise ValueError("stop needs a reason and next action")
                state.update(status=args.status, reason=args.reason, next_action=args.next)
                save(root, state)
                print("RUN: " + args.status + "; " + args.reason)
                return 0  # Recorded stop, not successful completion; status still exits 1.
            elif args.operation == "resume":
                budget(state)
                state["status"] = "active"
                state.pop("reason", None)
                state.pop("next_action", None)
                save(root, state)
            else:
                budget(state)
                if state["status"] in {"blocked", "failed"}:
                    raise ValueError("explicit resume required")
                if args.operation in {"begin", "reconcile"}:
                    action = next((a for a in state["contract"].get("actions", [])
                                   if a["id"] == args.action), None)
                    if action is None:
                        raise ValueError("action outside contract")
                    record = state["journal"].get(args.action)
                    if args.operation == "begin":
                        if not action.get("authorization", "").strip():
                            raise ValueError("action has no user authorization")
                        stage = next_stage(state)
                        if stage is None or stage["id"] != action["stage"]:
                            raise ValueError("action is not in the current stage")
                        if pending(state) or (record and record["result"] == "applied"):
                            raise ValueError("reconcile first; never repeat an applied action")
                        tries = (record or {}).get("attempts", 0) + 1
                        if tries > state["contract"]["max_attempts"]:
                            raise ValueError("action attempt budget exhausted")
                        state["status"] = "active"
                        state["journal"][args.action] = {"result": "unknown", "attempts": tries,
                                                         "began_at": time.time()}
                    else:
                        if not record:
                            raise ValueError("action was never begun")
                        proof = execute(root, state, action["probe"])
                        record["probe"] = proof
                        record["result"] = {0: "applied", 3: "absent"}.get(proof["exit"], "unknown")
                    save(root, state)
                    if pending(state):
                        print("RUN: external action unknown; reconcile before checks or retries")
                        return 0 if args.operation == "begin" else 1
                else:
                    if pending(state):
                        raise ValueError("unresolved actions: " + ", ".join(pending(state)))
                    if args.operation == "check":
                        stage = next_stage(state)
                        if stage is None or stage["id"] != args.stage:
                            raise ValueError("check must be the next stage")
                        check_stage(root, state, stage)
                    elif args.operation == "finish":
                        if next_stage(state):
                            raise ValueError("required stages remain")
                        required_actions(state)
                        # Replay checks, never external mutations. Catches changed remote health.
                        for stage in state["contract"]["stages"]:
                            check_stage(root, state, stage)
                        state = load(root)  # Check oracles after the commands, too.
                        state["status"] = "complete"
                        save(root, state)
                        gate(root, state)
        print("RUN: " + state["status"])
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print("RUN: rejected; " + str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
