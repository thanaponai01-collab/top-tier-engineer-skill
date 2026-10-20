"""swarm.py — coordinate many agents verifying one repository, or survey every feature at once.

Two jobs:

  1. Work-stealing queue (`verify.py swarm [repo] [--claim | --release | --done]`):
     Inspects VERIFY.md and .verify-state.json to classify every feature into its next required
     verification step (`map` -> `fix` -> `prove` -> `freeze` -> `challenge` -> `independent` ->
     `run` -> `done`). Agents with `VERIFY_AGENT=<name>` claim one feature at a time under the
     state lock with an expiring lease (`--lease`, default 600s). A step advances automatically as
     soon as the real receipt, baseline or pass lands in .verify-state.json, so an agent cannot
     mark a step done without producing the evidence. `independent` and `--role judge` tasks are
     never handed to the agent that froze the check (`frozen_by`).

  2. Repo-wide mutation survey (`verify.py swarm [repo] --auto [--diff [REF]] [--jobs N]`):
     Runs `challenge --auto` across every mapped feature (sharing scratch lanes when there is no
     `## Run` recipe) and reports per-feature and repo-wide mutation scores in one pass.
"""
import json
import tempfile
import time
from pathlib import Path


ACTIONS = ("map", "fix", "prove", "freeze", "challenge", "independent", "run", "done")
WORKER_ACTIONS = {"map", "fix", "prove", "freeze", "run", "challenge"}
JUDGE_ACTIONS = {"independent", "challenge", "prove", "freeze"}


def _independently_verified(state, feat, signature, tree):
    """True when every check of `feat` has a freezer and a different agent that verified it on (signature, tree)."""
    frozen = state.get("frozen_by") or {}
    verified = state.get("verified_by") or {}
    for kind, cmd in feat["checks"]:
        ckey = f"{feat['name']}|{kind}|{cmd}"
        who = frozen.get(ckey)
        v = verified.get(ckey) or {}
        if not who or v.get("agent") in (None, who) or v.get("signature") != signature or v.get("tree") != tree:
            return False
    return True


def _next_command(repo, feat, action, freezers):
    name = feat["name"]
    q = f'"{name}"' if " " in name else name
    if action == "map":
        return f"edit {repo}/VERIFY.md: add `- test: ...` and `- fail-signal: ...` under `## {name}`"
    if action == "fix":
        paths = " ".join(feat.get("paths") or ["<files>"])
        return f"python verify.py scope {paths} --repo {repo} && python verify.py run {repo} --only {q}"
    if action == "prove":
        target = (feat.get("paths") or ["<file>"])[0]
        return (f"python verify.py challenge {repo} --feature {q} --file {target} "
                f"--before \"<good>\" --after \"<wrong>\"")
    if action == "freeze":
        return f"python verify.py baseline {repo}"
    if action == "challenge":
        target = (feat.get("paths") or ["<file>"])[0]
        return (f"python verify.py challenge {repo} --feature {q} --file {target} "
                f"--before \"<good>\" --after \"<wrong>\"")
    if action == "independent":
        avoid = f" (not {', '.join(freezers)})" if freezers else ""
        return f"VERIFY_AGENT=<other{avoid}> python verify.py run {repo} --strict"
    if action == "run":
        return f"python verify.py run {repo} --strict"
    return ""


def swarm_items(v, repo, state=None, now=None):
    """Compute the current verification state and active lease for every feature in VERIFY.md."""
    now = time.time() if now is None else now
    text = v.read(repo, v.RECIPE)
    features, _ = v.parse(text, repo=repo)
    reqs = set(v.requirements(text))
    state = v.load_state(repo) if state is None else state
    try:
        hashes = v.check_hashes(repo)
        signature = v.sha(json.dumps(hashes, sort_keys=True))
    except (OSError, ValueError):
        hashes, signature = {}, None
    cur_tree = v.tree_sig(repo, fast=False) if features else None
    receipts = v.current_receipts(state, signature) if signature else {}
    checks = state.get("checks", {}) or {}
    passing_out = {k: r.get("output", "") for k, r in checks.items() if isinstance(r, dict) and r.get("ok")}
    frozen_lines = set((state.get("baseline_lines") or {}).get("checks", []))
    frozen_by = state.get("frozen_by") or {}
    leases = state.get("swarm") or {}
    any_challenged = any(r.get("mutation") and r.get("signature") == signature for r in receipts.values())
    tree_matches_last_strict = bool(state.get("strict") and state.get("result") == "green"
                                    and state.get("tree") == cur_tree)

    items = []
    for f in features:
        ckeys = [f"{f['name']}|{k}|{c}" for k, c in f["checks"]]
        freezers = sorted({frozen_by[k] for k in ckeys if frozen_by.get(k)})
        failing = [c for _, c in f["checks"]
                   if isinstance(checks.get(f"{f['name']}|{c}"), dict) and not checks[f"{f['name']}|{c}"].get("ok")]
        all_passed = bool(f["checks"]) and all(
            isinstance(checks.get(f"{f['name']}|{c}"), dict) and checks[f"{f['name']}|{c}"].get("ok")
            for _, c in f["checks"])
        feat_challenged = any(r.get("mutation") and r.get("signature") == signature and k.startswith(f["name"] + "|")
                              for k, r in receipts.items())
        if not f["checks"] or not f["signals"]:
            action, detail = "map", "no check or literal fail-signal in VERIFY.md"
        elif failing:
            action, detail = "fix", f"{len(failing)} check(s) failing on last run"
        elif not f["proofs"] or not signature or not v.proven_by(f, receipts, signature, passing_out):
            action, detail = "prove", "no valid failure receipt matching fail-signal (or no fail-proof note)"
        elif not state.get("baseline") or any(k not in frozen_lines for k in ckeys):
            action, detail = "freeze", "checks not yet frozen in baseline"
        elif "challenge" in reqs and not any_challenged and not feat_challenged:
            action, detail = "challenge", "require: challenge is set and no mutation has been caught yet"
        elif "independent" in reqs and not _independently_verified(state, f, signature, cur_tree):
            who = ", ".join(freezers) if freezers else "an unnamed agent"
            action, detail = "independent", f"frozen by {who}; needs strict verification by a different VERIFY_AGENT"
        elif not all_passed or not tree_matches_last_strict:
            action, detail = "run", "needs a passing strict whole run on the current tree"
        else:
            action, detail = "done", "verified"

        lease = leases.get(f["name"]) if isinstance(leases.get(f["name"]), dict) else None
        active_claim = None
        if (action != "done" and lease and lease.get("action") == action
                and float(lease.get("expires") or 0) > now and lease.get("agent")):
            active_claim = {"agent": lease["agent"], "action": action,
                            "at": lease.get("at"), "expires": lease.get("expires")}
        items.append({
            "feature": f["name"],
            "journey": f["journey"],
            "action": action,
            "status": "done" if action == "done" else ("claimed" if active_claim else "open"),
            "detail": detail,
            "freezers": freezers,
            "paths": f.get("paths") or [],
            "claim": active_claim,
            "next": _next_command(repo, f, action, freezers),
        })
    return items


def eligible(item, agent, role="any"):
    """True when `agent` is allowed to claim `item` under `role`."""
    act = item["action"]
    if act == "done":
        return False
    if role == "worker" and act not in WORKER_ACTIONS:
        return False
    if role == "judge" and act not in JUDGE_ACTIONS:
        return False
    if (act == "independent" or role == "judge") and (not agent or agent in item["freezers"]):
        return False
    return True


def cmd_swarm_auto(v, repo, diff=None, jobs=1, limit=20, timeout=120, as_json=False):
    """Run mutation surveys across every mapped feature with checks and a fail-signal in one pass."""
    from challenge import prepare, mutable_target, judge
    from mutate import Lane, changed_files, changed_lines, detect_lang, generate, probe, run_lanes

    root = Path(repo).resolve()
    text = v.read(repo, v.RECIPE)
    features, _ = v.parse(text, repo=repo)
    candidates_by_feat = [f for f in features if f["checks"] and f["signals"]]
    if not candidates_by_feat:
        print("SWARM-AUTO: invalid (no feature in VERIFY.md has both checks and a fail-signal); score n/a")
        return 2

    try:
        if timeout <= 0 or jobs < 1:
            raise ValueError("timeout and jobs must be positive")
        frozen = v.check_hashes(repo)
        recipe = v.parse_run(text)
        diff_files = changed_files(v, repo, diff, frozen) if diff else None
        if diff and not diff_files:
            raise ValueError(f"no changed product file since {diff}")

        all_product = []
        for r_dir, dirs, files in v.os.walk(repo):
            dirs[:] = sorted(d for d in dirs if d not in v.SKIP_DIRS and not v.is_state_file(d))
            for fn in sorted(files):
                rel = v.os.path.relpath(v.os.path.join(r_dir, fn), repo).replace("\\", "/")
                if detect_lang(rel) == "other":
                    continue
                try:
                    mutable_target(v, repo, frozen, rel)
                    all_product.append(rel)
                except (OSError, ValueError):
                    continue

        sources = {}
        tasks = []  # [(feat_dict, candidate_dict)]
        for f in candidates_by_feat:
            _, feat, _ = prepare(v, repo, f["name"])
            if diff_files is not None:
                f_files = [p for p in diff_files if v.is_feature_affected(f, {p}, repo)] or list(diff_files)
            elif f.get("paths"):
                f_files = [p for p in all_product
                           if any(p == fp.rstrip("/") or p.startswith(fp.rstrip("/") + "/") for fp in f["paths"])]
            else:
                matched = [p for p in all_product if v.is_feature_affected(f, {p}, repo)]
                f_files = matched or list(all_product)
            f_budget = limit
            for rel in f_files:
                if f_budget <= 0:
                    break
                if rel not in sources:
                    target = mutable_target(v, repo, frozen, rel)
                    sources[rel] = target.read_text(encoding="utf-8")
                only = changed_lines(repo, diff, rel) if diff else None
                lang = detect_lang(rel)
                for c in generate(sources[rel], f_budget, is_py=(lang == "py"), lang=lang, only=only):
                    tasks.append((feat, dict(c, file=rel, feature=feat["name"])))
                    f_budget -= 1
    except (OSError, ValueError) as exc:
        print(f"SWARM-AUTO: invalid ({exc}); score n/a")
        return 2

    if not tasks:
        since = f"changed since {diff} " if diff else ""
        print(f"SWARM-AUTO: invalid (no mutable lines {since}across mapped features); score n/a")
        return 2

    if recipe:
        jobs = 1
    jobs = min(jobs, len(tasks))
    original_tree, original_state = v.tree_sig(repo), v.load_state(repo)

    # Combined feature so Lane.fresh() verifies all participating features' checks pass unmutated first.
    seen_cmds = []
    for f, _ in tasks:
        for pair in f["checks"]:
            if pair not in seen_cmds:
                seen_cmds.append(pair)
    union_feat = {"name": "__swarm__", "checks": seen_cmds, "signals": []}

    def run_for_feat(lane, feat, wrong):
        rel, text_w = wrong
        (lane.path / rel).write_text(text_w, encoding="utf-8")
        try:
            if lane.recipe:
                lane.feat = feat
                rows = lane.run_rows()
            else:
                rows = []
                for kind, cmd in feat["checks"]:
                    ok, code, out, _, _ = v.attempt(cmd, str(lane.path), lane.timeout, 1)
                    rows.append((kind, cmd, {"ok": ok, "exit": code, "output": out[-8000:]}))
            intact = v.check_hashes(str(lane.path)) == lane.frozen and all(
                (lane.path / r).read_text(encoding="utf-8") == (text_w if r == rel else src)
                for r, src in lane.sources.items())
        finally:
            (lane.path / rel).write_text(lane.sources[rel], encoding="utf-8")
        if v.tree_sig(str(lane.path)) != lane.sig:
            lane.feat = union_feat
            lane.fresh()
        return rows, intact

    def do_mutant(lane, item):
        feat, c = item
        rows, intact = run_for_feat(lane, feat, (c["file"], sources[c["file"]].replace(c["before"], c["after"], 1)))
        verdict, reason, _ = judge(v, feat, rows, intact)
        return dict(c, verdict=verdict, reason=reason)

    def probed(rel, line):
        return probe(sources[rel], line, detect_lang(rel))

    feat_by_name = {f["name"]: f for f in candidates_by_feat}

    def do_probe(lane, spot):
        fname, rel, line = spot
        feat = feat_by_name[fname]
        rows, intact = run_for_feat(lane, feat, (rel, probed(rel, line)))
        return not (intact and all(row and row["ok"] for _, _, row in rows))

    with tempfile.TemporaryDirectory(prefix="verify-swarm-auto-") as tmp:
        lanes = [Lane(v, repo, Path(tmp, f"lane{i}"), union_feat, frozen, recipe, timeout, sources)
                 for i in range(jobs)]
        done, errors = run_lanes(lanes, tasks, do_mutant)
        lane_error = next(iter(errors.values()), "lane stopped before this mutation")
        results = [done.get(i) or dict(c, verdict="inconclusive", reason=lane_error)
                   for i, (_, c) in enumerate(tasks)]
        spots = sorted({(r["feature"], r["file"], r["line"]) for r in results
                        if r["verdict"] == "survived" and probed(r["file"], r["line"])})
        live = [lane for lane in lanes if lane not in errors][:len(spots)]
        if live and spots:
            hit, _ = run_lanes(live, spots, do_probe)
            unreached = {spot for i, spot in enumerate(spots) if hit.get(i) is False}
            for r in results:
                if r["verdict"] == "survived" and (r["feature"], r["file"], r["line"]) in unreached:
                    r.update(verdict="uncovered",
                             reason="no check reaches this line: a probe that aborts there still passes")
        copies = sum(lane.copies for lane in lanes)

    def settled(st):
        return {k: val for k, val in st.items() if k != "failures"}

    if v.tree_sig(repo) != original_tree or settled(v.load_state(repo)) != settled(original_state):
        print("SWARM-AUTO: inconclusive (source files or verification state changed during survey); score n/a")
        return 2

    per_feature = []
    for f in candidates_by_feat:
        f_res = [r for r in results if r["feature"] == f["name"]]
        if not f_res:
            continue
        f_c = sum(r["verdict"] == "caught" for r in f_res)
        f_s = sum(r["verdict"] == "survived" for r in f_res)
        f_u = sum(r["verdict"] == "uncovered" for r in f_res)
        f_d = f_c + f_s + f_u
        per_feature.append({
            "feature": f["name"], "generated": len(f_res), "caught": f_c, "survived": f_s,
            "uncovered": f_u, "inconclusive": len(f_res) - f_d,
            "score": round(f_c / f_d, 3) if f_d else None,
        })

    caught = sum(r["verdict"] == "caught" for r in results)
    survived = [r for r in results if r["verdict"] == "survived"]
    uncovered = [r for r in results if r["verdict"] == "uncovered"]
    decided = caught + len(survived) + len(uncovered)
    score = round(caught / decided, 3) if decided else None
    summary = {
        "features": per_feature, "files": sorted(sources), "diff": diff,
        "generated": len(tasks), "run": len(results), "caught": caught,
        "survived": len(survived), "uncovered": len(uncovered),
        "inconclusive": len(results) - decided, "score": score,
        "jobs": jobs, "copies": copies, "results": results,
    }
    if as_json:
        print(json.dumps(summary, indent=2))
    else:
        shown = "n/a" if score is None else f"{score:.0%}"
        scope = f" (lines changed since {diff})" if diff else ""
        print(f"SWARM-AUTO: {caught}/{decided} caught (score {shown}), {len(uncovered)} uncovered, "
              f"{summary['inconclusive']} inconclusive across {len(per_feature)} feature(s){scope}")
        for pf in per_feature:
            pf_s = "n/a" if pf["score"] is None else f"{pf['score']:.0%}"
            print(f"  FEATURE {pf['feature']}: {pf['caught']}/{pf['caught'] + pf['survived'] + pf['uncovered']} "
                  f"caught ({pf_s}), {pf['survived']} survived, {pf['uncovered']} uncovered")
        for r in survived:
            print(f"  SURVIVED [{r['feature']}] {r['file']}:{r['line']} {r['operator']}: "
                  f"{r['before'].strip()} -> {r['after'].strip()}")
        for r in uncovered:
            print(f"  UNCOVERED [{r['feature']}] {r['file']}:{r['line']} {r['operator']}: "
                  f"no check reaches {r['before'].strip()}")
    if decided == 0:
        return 2
    return 1 if survived or uncovered else 0


def cmd_swarm(v, repo, claim=False, release=None, done=None, role="any", lease=600,
              auto=False, diff=None, jobs=1, limit=20, timeout=120, as_json=False):
    if not v.os.path.isfile(v.os.path.join(repo, v.RECIPE)):
        if as_json:
            print(json.dumps({"error": f"no {v.RECIPE} in {repo}", "exit": 2}))
        else:
            print(f"no {v.RECIPE} in {repo}. Run `verify.py init` to draft one.")
        return 2
    if auto:
        return cmd_swarm_auto(v, repo, diff=diff, jobs=jobs, limit=limit, timeout=timeout, as_json=as_json)

    agent = v.agent_name()
    now = time.time()

    if release is not None or done is not None:
        target_feat = release if release is not None else done
        if not agent and not target_feat:
            msg = "SWARM: set VERIFY_AGENT=<name> or pass a feature name to release"
            print(json.dumps({"error": msg, "exit": 2}) if as_json else msg)
            return 2
        state = v.load_state(repo)
        leases = dict(state.get("swarm") or {})
        removed = []
        for fname, entry in list(leases.items()):
            if (target_feat and fname == target_feat) or (not target_feat and isinstance(entry, dict)
                                                           and entry.get("agent") == agent):
                leases.pop(fname, None)
                removed.append(fname)
        state["swarm"] = leases
        v.save_state(repo, state)
        items = swarm_items(v, repo, state, now)
        still_open = [i for i in items if i["feature"] in removed and i["action"] != "done"]
        if as_json:
            print(json.dumps({"released": removed, "still_open": [i["feature"] for i in still_open], "exit": 0},
                             indent=2))
        else:
            print(f"SWARM: released {', '.join(removed) if removed else 'none'}"
                  + (f" ({', '.join(i['feature'] + ' still needs ' + i['action'] for i in still_open)})"
                     if still_open else ""))
        return 0

    if claim:
        if not agent:
            msg = "SWARM: VERIFY_AGENT=<name> is required to claim work so leases and independence are tracked"
            print(json.dumps({"error": msg, "exit": 2}) if as_json else msg)
            return 2
        if lease <= 0:
            msg = "SWARM: --lease must be positive seconds"
            print(json.dumps({"error": msg, "exit": 2}) if as_json else msg)
            return 2
        state = v.load_state(repo)
        items = swarm_items(v, repo, state, now)
        leases = {}
        for i in items:
            if i["claim"]:
                leases[i["feature"]] = i["claim"]
        # Reuse this agent's existing active claim if it is still valid and eligible
        chosen = next((i for i in items if i["claim"] and i["claim"]["agent"] == agent and eligible(i, agent, role)),
                      None)
        if chosen is None:
            chosen = next((i for i in items if i["status"] == "open" and eligible(i, agent, role)), None)
            if chosen is not None:
                entry = {"agent": agent, "action": chosen["action"],
                         "at": round(now, 3), "expires": round(now + lease, 3)}
                leases[chosen["feature"]] = entry
                chosen = dict(chosen, status="claimed", claim=entry)
        state["swarm"] = leases
        v.save_state(repo, state)

        todo = [i for i in items if i["action"] != "done"]
        if not todo:
            if as_json:
                print(json.dumps({"verdict": "green", "claimed": None, "items": items, "exit": 0}, indent=2))
            else:
                print("SWARM: green (every mapped feature is verified)")
            return 0
        if chosen is None:
            reasons = []
            by_others = [i["feature"] for i in todo if i["claim"] and i["claim"]["agent"] != agent]
            inelig = [i["feature"] for i in todo if not i["claim"] and not eligible(i, agent, role)]
            if by_others:
                reasons.append(f"claimed by others: {', '.join(by_others)}")
            if inelig:
                reasons.append(f"needs another agent/role ({role}): {', '.join(inelig)}")
            detail = "; ".join(reasons) or "no eligible open item"
            if as_json:
                print(json.dumps({"verdict": "waiting", "agent": agent, "role": role,
                                  "detail": detail, "claimed": None, "items": items, "exit": 3}, indent=2))
            else:
                print(f"SWARM: waiting ({detail})")
            return 3
        if as_json:
            print(json.dumps({"verdict": "claimed", "agent": agent, "role": role,
                              "claimed": chosen, "exit": 0}, indent=2))
        else:
            print(f"SWARM-CLAIM: {chosen['feature']} [{chosen['action'].upper()}] -> {agent} (lease {lease}s)")
            print(f"  Why:  {chosen['detail']}")
            print(f"  Next: {chosen['next']}")
        return 0

    state = v.load_state(repo)
    items = swarm_items(v, repo, state, now)
    counts = {
        "total": len(items),
        "done": sum(i["status"] == "done" for i in items),
        "claimed": sum(i["status"] == "claimed" for i in items),
        "open": sum(i["status"] == "open" for i in items),
    }
    all_done = counts["total"] > 0 and counts["done"] == counts["total"]
    if as_json:
        print(json.dumps({
            "verdict": "green" if all_done else "pending",
            "summary": counts,
            "items": items,
            "exit": 0 if all_done else 1,
        }, indent=2))
        return 0 if all_done else 1

    for i in items:
        if i["status"] == "done":
            tag = "DONE   "
            extra = ""
        elif i["status"] == "claimed":
            tag = "CLAIMED"
            rem = max(0, int(float(i["claim"]["expires"]) - now))
            extra = f" -> {i['claim']['agent']} ({i['action']}, {rem}s left)"
        else:
            tag = f"{i['action'].upper():7}"
            extra = f" ({i['detail']})"
        print(f"  {tag}  {i['feature']}{extra}")
    print(f"SWARM: {counts['done']}/{counts['total']} done | {counts['claimed']} claimed | {counts['open']} open")
    return 0 if all_done else 1
