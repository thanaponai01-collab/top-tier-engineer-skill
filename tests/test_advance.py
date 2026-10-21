"""Automatic progression through the real CLI, retaining proof gates."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _helpers import SCRIPTS, run


def fixture(root):
    root = Path(root)
    (root / 'app.py').write_text('def answer():\n    return 42\n')
    (root / 'test_app.py').write_text(
        'from app import answer\n'
        'def test_answer():\n    assert answer() == 42, "ANSWER_WRONG"\n'
        'if __name__ == "__main__":\n    test_answer()\n')
    (root / 'VERIFY.md').write_text(
        '## Answer\n- path: app.py\n- test: `python test_app.py`\n'
        '- fail-signal: ANSWER_WRONG\n- fail-proof: app returns 41 instead of 42\n')
    return root


class AdvanceCLI(unittest.TestCase):
    def advance(self, root, *args):
        code, out, err = run('verify.py', 'advance', str(root), '--json', *args)
        self.assertFalse(err, err)
        data = json.loads(out)
        self.assertEqual(code, data['exit'], out)
        return data

    def prove(self, root):
        code, out, err = run('verify.py', 'challenge', str(root), '--feature', 'Answer',
                             '--file', 'app.py', '--before', 'return 42', '--after', 'return 41')
        self.assertEqual(code, 0, out + err)

    def test_proven_feature_automatically_freezes_and_runs_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            self.prove(root)
            result = self.advance(root)
            self.assertEqual(result['stop'], 'done', result)
            self.assertEqual(result['report']['verdict'], 'green', result)
            self.assertIn('freeze', [s['action'] for s in result['steps']])
            self.assertEqual(result['steps'][-1]['action'], 'run-strict')
            again = self.advance(root)
            self.assertEqual(again['stop'], 'done')
            self.assertEqual(again['steps'], [])

    def test_missing_proof_yields_task_without_inventing_a_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            result = self.advance(root)
            self.assertEqual(result['stop'], 'needs-agent', result)
            self.assertEqual(result['tasks'][0]['action'], 'prove')
            self.assertFalse(result['report']['rejections'])
            self.assertEqual({n: (root / n).read_bytes() for n in before}, before)
            self.assertEqual(self.advance(root)['steps'], [])

    def test_failed_product_stops_without_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            (root / 'app.py').write_text('def answer():\n    return 41\n')
            result = self.advance(root)
            self.assertEqual(result['stop'], 'needs-agent', result)
            self.assertEqual(result['tasks'][0]['action'], 'fix')
            self.assertEqual(len(result['steps']), 1)
            self.assertEqual(self.advance(root)['steps'], [])

    def test_environment_failure_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            recipe = root / 'VERIFY.md'
            recipe.write_text(recipe.read_text().replace('python test_app.py', 'missing_verify_tool_913'))
            result = self.advance(root)
            self.assertEqual(result['stop'], 'blocked', result)
            self.assertEqual(len(result['steps']), 1)

    def test_independence_always_yields_a_judge_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            recipe = root / 'VERIFY.md'
            recipe.write_text('require: independent\n\n' + recipe.read_text())
            self.prove(root)
            result = self.advance(root)
            self.assertEqual(result['stop'], 'needs-agent', result)
            self.assertEqual(result['tasks'][0]['action'], 'independent')
            self.assertNotEqual(result['report']['verdict'], 'green')

    def test_budget_and_invalid_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            self.prove(root)
            result = self.advance(root, '--max-steps', '1')
            self.assertEqual(result['stop'], 'budget', result)
            self.assertEqual(len(result['steps']), 1)
            for args in [('--max-steps', '0'), ('--timeout', '0'), ('--jobs', '0')]:
                self.assertEqual(self.advance(root, *args)['exit'], 2)

    def test_missing_and_empty_recipe_are_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.advance(tmp)['exit'], 2)
            Path(tmp, 'VERIFY.md').write_text('# Empty\n')
            self.assertEqual(self.advance(tmp)['exit'], 2)

    def test_foreign_claim_prevents_whole_recipe_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            with patch.dict(os.environ, {'VERIFY_AGENT': 'other'}):
                code, out, _ = run('verify.py', 'swarm', str(root), '--claim')
            self.assertEqual(code, 0, out)
            with patch.dict(os.environ, {'VERIFY_AGENT': 'worker'}):
                result = self.advance(root)
            self.assertEqual(result['stop'], 'waiting', result)
            self.assertEqual(result['steps'], [])

    def test_external_state_and_plain_output(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as state:
            root = fixture(tmp)
            result = self.advance(root, '--state-dir', state)
            self.assertEqual(result['stop'], 'needs-agent')
            self.assertFalse(list(root.glob('.verify-state*')))
            code, out, err = run('verify.py', 'advance', str(root), '--state-dir', state)
            self.assertEqual(code, 3, out + err)
            self.assertIn('ADVANCE: needs-agent', out)
            self.assertIn('Answer', out)

    def test_changed_product_refreshes_a_previous_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            (root / 'app.py').write_text('def answer():\n    return 41\n')
            self.advance(root)
            (root / 'app.py').write_text('def answer():\n    return 42\n')
            result = self.advance(root)
            self.assertTrue(result['steps'])
            self.assertNotEqual(result['tasks'][0]['action'] if result['tasks'] else '', 'fix')

    def test_refresh_reruns_checks_after_an_external_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            self.advance(root)
            result = self.advance(root, '--refresh')
            self.assertEqual([s['action'] for s in result['steps']], ['run'])

    def test_unmapped_product_blocks_strict_green_without_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            (root / 'unrelated.py').write_text('def other(): return 1\n')
            self.prove(root)
            result = self.advance(root)
            self.assertEqual(result['stop'], 'needs-agent', result)
            self.assertTrue(result['report']['gaps']['unmapped'])
            self.assertEqual(self.advance(root)['steps'], [])

    def test_frozen_check_changes_are_never_rebaselined(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            self.prove(root)
            self.advance(root)
            (root / 'test_app.py').write_text('assert True\n')
            result = self.advance(root)
            self.assertEqual(result['stop'], 'guard', result)
            self.assertEqual(result['steps'], [])
            self.assertNotEqual(result['report']['verdict'], 'green')

    def test_executor_lock_is_not_stolen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            lock = root / '.verify-state.advance.lock'
            lock.write_text('')
            os.utime(lock, (1, 1))
            result = self.advance(root)
            self.assertEqual(result['stop'], 'waiting', result)
            self.assertEqual(result['steps'], [])
            self.assertTrue(lock.exists())

    def test_check_that_changes_product_stops_as_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            check = root / 'test_app.py'
            check.write_text(check.read_text() +
                '\nfrom pathlib import Path\nPath("app.py").write_text("def answer(): return 41\\n")\n')
            result = self.advance(root)
            self.assertEqual(result['stop'], 'stale', result)
            self.assertEqual(len(result['steps']), 1)

    def test_plan_invalidated_before_execution_does_not_run(self):
        # A controlled edit between planning and dispatch exercises the race guard.
        scripts = SCRIPTS['verify.py']
        sys.path.insert(0, scripts)
        try:
            spec = importlib.util.spec_from_file_location('advance_test_verify', Path(scripts, 'verify.py'))
            v = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = v
            spec.loader.exec_module(v)
            import advance
            original_choose = advance.choose
            with tempfile.TemporaryDirectory() as tmp:
                root = fixture(tmp)
                def changing_choose(*args, **kwargs):
                    decision = original_choose(*args, **kwargs)
                    (root / 'app.py').write_text('def answer(): return 99\n')
                    return decision
                import contextlib
                import io
                output = io.StringIO()
                with patch.object(advance, 'choose', changing_choose), contextlib.redirect_stdout(output):
                    code = advance.cmd_advance(v, str(root), as_json=True)
                result = json.loads(output.getvalue())
                self.assertEqual(code, 3)
                self.assertEqual(result['stop'], 'stale')
                self.assertEqual(result['steps'], [])
        finally:
            sys.modules.pop('advance_test_verify', None)
            sys.path.remove(scripts)


if __name__ == '__main__':
    unittest.main()
