"""P03: failed subprocesses cannot become green through output matching."""
import os, sys, tempfile, unittest
from _helpers import ROOT
sys.path.insert(0, os.path.join(ROOT, 'evals'))
import agent, run

class EndStateEnforcement(unittest.TestCase):
    def check_command(self, source):
        with tempfile.TemporaryDirectory() as root:
            os.mkdir(os.path.join(root, 'fixture'))
            with open(os.path.join(root, 'fixture', 'probe.py'), 'w') as f:
                f.write(source)
            spec = {'end_state': {'cmd': f'"{sys.executable}" probe.py', 'must_print_any': ['OK']}}
            result = run.run_end_state(spec, root)
            return run.check_actions(spec, agent.parse_stream([]),
                                     {'changed': [], 'added': [], 'deleted': []}, result)[0]

    def test_success_text_on_stdout_does_not_hide_failed_exit(self):
        result = self.check_command("print('OK'); raise SystemExit(1)")
        self.assertFalse(result['ok'], 'failed stdout command silently accepted: ' + result['detail'])
        self.assertIn('exit', result['detail'])

    def test_success_text_on_stderr_does_not_hide_failed_exit(self):
        result = self.check_command("import sys; print('OK', file=sys.stderr); sys.exit(3)")
        self.assertFalse(result['ok'], 'failed stderr command silently accepted: ' + result['detail'])

    def test_valid_result_passes(self):
        self.assertTrue(self.check_command("print('OK')")['ok'])

    def test_legacy_output_without_exit_is_unknown(self):
        spec = {'end_state': {'cmd': 'probe', 'must_print_any': ['OK']}}
        result = run.check_actions(spec, agent.parse_stream([]),
                                   {'changed': [], 'added': [], 'deleted': []}, 'OK')[0]
        self.assertFalse(result['ok'])
        self.assertIn('rerun', result['detail'])
