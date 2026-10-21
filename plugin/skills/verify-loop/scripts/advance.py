"""Bounded mechanical transitions; all judgments return to the caller."""
import contextlib
import io
import json
import os
import time

from swarm import swarm_items


def snapshot(v, repo):
    """Bind a plan to product, checks, receipts, loop memory and shared leases."""
    state = v.load_state(repo)
    return v.sha(json.dumps({'tree': v.tree_sig(repo, fast=False),
                             'checks': v.check_hashes(repo), 'state': state}, sort_keys=True))


def choose(v, repo, items, refresh=False):
    state = v.load_state(repo)
    if state.get('forged') or v.tampered(repo, state) or v.out_of_scope(repo, state):
        return None, 'guard', items
    # Both automatic actions operate on the whole recipe, including other features.
    foreign = [i for i in items if i['claim'] and i['claim']['agent'] != v.agent_name()]
    if foreign:
        return None, 'waiting', foreign
    unmapped = [i for i in items if i['action'] == 'map']
    if unmapped:
        return None, 'needs-agent', unmapped
    tree = v.tree_sig(repo, fast=False)
    if refresh or not state.get('result') or state.get('tree') != tree:
        return 'run', None, []
    pending = [i for i in items if i['action'] != 'done']
    if not pending and v.status_verdict(repo)[0] == 'green':
        return None, 'done', []
    blocked = [i for i in pending if i['action'] == 'blocked']
    if blocked:
        return None, 'blocked', blocked
    decisions = [i for i in pending if i['action'] not in ('freeze', 'run')]
    if decisions:
        return None, 'needs-agent', decisions
    if any(i['action'] == 'freeze' for i in pending):
        return 'freeze', None, []
    # A current strict red may reflect a gate outside feature classification (e.g. UNMAPPED).
    # Repeating it unchanged adds no evidence and may be expensive.
    if state.get('strict') and state.get('result') != 'green':
        return None, 'needs-agent', pending
    return 'run-strict', None, []


def cmd_advance(v, repo, max_steps=3, timeout=120, jobs=1, refresh=False, as_json=False):
    result = {'stop': None, 'steps': [], 'tasks': [], 'report': None, 'exit': 3}

    def finish(stop, tasks=(), error=None, code=None):
        result['stop'] = stop
        result['tasks'] = list(tasks)
        if error:
            result['error'] = str(error)
        if stop != 'invalid':
            result['report'] = v.answer(repo)
        result['exit'] = code if code is not None else (0 if stop == 'done' else 3)
        # Keep the bounded transition record alongside this agent's existing loop memory.
        if result['steps']:
            state = v.load_state(repo)
            state['last_advance'] = {'at': time.time(), 'stop': stop, 'steps': result['steps']}
            v.save_state(repo, state)
        if as_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"ADVANCE: {stop}")
            for step in result['steps']:
                print(f"  {step['action']}: exit {step['exit']}")
            for task in tasks:
                print(f"  {task['feature']} [{task['action']}]: {task['detail']}")
                print(f"  Next: {task['next']}")
            if error:
                print(f"  {error}")
            report = result['report']
            if report:
                print(f"VERDICT: {report['verdict']}")
                if report['verify_line']:
                    print(report['verify_line'])
                for kind, gaps in report['gaps'].items():
                    for gap in gaps:
                        print(f"  GAP {kind}: {gap}")
        return result['exit']

    if min(max_steps, timeout, jobs) <= 0:
        return finish('invalid', error='--max-steps, --timeout and --jobs must be positive', code=2)
    if not os.path.isfile(os.path.join(repo, v.RECIPE)):
        return finish('invalid', error=f'no {v.RECIPE} in {repo}', code=2)
    try:
        features, _ = v.parse(v.read(repo, v.RECIPE), repo=repo)
        if not features:
            return finish('invalid', error=f'{v.RECIPE} has no features', code=2)
        os.makedirs(v.state_home(repo), exist_ok=True)
        # Separate from the short state-save lock. Never steal a long-running executor's lock.
        # A crashed executor leaves this file for explicit removal after checking its process.
        lock = os.path.join(v.state_home(repo), '.verify-state.advance.lock')
        with v.file_lock(lock, wait=0, stale=float('inf')):
            while True:
                planned = snapshot(v, repo)
                items = swarm_items(v, repo)
                action, stop, tasks = choose(v, repo, items, refresh)
                if snapshot(v, repo) != planned:
                    return finish('stale', error='inputs or verification state changed before execution')
                if stop:
                    return finish(stop, tasks, code=1 if stop in ('blocked', 'guard') else None)
                if len(result['steps']) >= max_steps:
                    return finish('budget', [i for i in items if i['action'] != 'done'])
                before_tree = v.tree_sig(repo, fast=False)
                log = io.StringIO()
                with contextlib.redirect_stdout(log):
                    if action == 'freeze':
                        code = v.cmd_baseline(repo)  # no review override, ever
                    else:
                        code = v.cmd_run(repo, only=None, timeout=timeout,
                                         strict=action == 'run-strict', jobs=jobs, use_cache=False)
                result['steps'].append({'action': action, 'exit': code, 'input': planned,
                                        'output': log.getvalue()[-16000:]})
                refresh = False
                if v.tree_sig(repo, fast=False) != before_tree:
                    return finish('stale', error='product or checks changed during execution')
                if code and action == 'freeze':
                    return finish('guard', error='baseline refused; review the recorded output', code=1)
                if code == 2:
                    return finish('invalid', error='runner could not execute the recipe', code=2)
                # Recompute from receipts and gates, never from the human-readable NEXT command.
    except TimeoutError as exc:
        return finish('waiting', error=exc)
    except (OSError, ValueError) as exc:
        return finish('invalid', error=exc, code=2)
