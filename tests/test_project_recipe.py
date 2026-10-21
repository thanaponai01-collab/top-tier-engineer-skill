"""Real application acceptance trials for P02; no fixed ports or unrelated kills."""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from urllib.request import urlopen

from _helpers import ROOT, run
from test_verify import alive

FIXTURE = Path(ROOT) / 'tests/fixtures/p02'

class ApplicationRecipe(unittest.TestCase):
    def fixture(self, root, mode='api', managed=True):
        shutil.copytree(FIXTURE, root, dirs_exist_ok=True)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
        config = {'port': port, 'owner': uuid.uuid4().hex}
        (root / 'config.json').write_text(json.dumps(config))
        recipe = '## Run\n'
        if mode == 'api':
            if managed:
                recipe += '- start: `python app.py serve`\n- ready: `python probe.py ready`\n'
            recipe += '- doctor: `python probe.py doctor`\n'
        recipe += '- stop: `python probe.py cleanup`\n\n## Persistence\n'
        recipe += f'- path: app.py, broken.flag\n- run: `python probe.py {mode}`\n- oracle: probe.py\n'
        recipe += '- fail-signal: expected persisted note, got\n- fail-proof: disabled saving; acknowledged write but second read rejected it\n'
        (root / 'VERIFY.md').write_text(recipe)
        return config

    def invoke(self, root, *args):
        code, out, err = run('verify.py', *args, str(root), '--timeout', '8') if args[0] == 'run' else run('verify.py', *args, str(root))
        if os.environ.get('P02_EVIDENCE'):
            target = Path(os.environ['P02_EVIDENCE']) / root.name
            target.mkdir(parents=True, exist_ok=True)
            number = len(list(target.glob('*.txt')))
            (target / f'{number}-{args[0]}.txt').write_text(out + err, encoding='utf-8')
            if (root / '.verify-state.json').exists():
                shutil.copyfile(root / '.verify-state.json', target / f'{number}-state.json')
            if (root / '.verify-evidence').exists():
                shutil.copytree(root / '.verify-evidence', target / 'observations', dirs_exist_ok=True)
        return code, out + err

    def assert_clean(self, root):
        if (root / 'pid.txt').exists():
            self.assertFalse(alive(int((root / 'pid.txt').read_text())), 'owned app survived teardown')
        self.assertFalse((root / 'build/data').exists(), 'disposable data survived teardown')

    def test_api_and_cli_reject_ack_without_persistence_then_strict_green(self):
        for mode in ('api', 'cli'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.fixture(root, mode)
                (root / 'broken.flag').touch()
                code, out = self.invoke(root, 'run')
                self.assertEqual(code, 1, out); self.assertIn('expected persisted note, got', out)
                self.assert_clean(root)
                evidence = json.loads((root / f'.verify-evidence/{mode}.json').read_text())
                self.assertIsNone(evidence['actual'])
                state = json.loads((root / '.verify-state.json').read_text())
                self.assertIn('expected persisted note, got', json.dumps(state))
                (root / 'broken.flag').unlink()
                self.assertEqual(self.invoke(root, 'baseline')[0], 0)
                code, out = self.invoke(root, 'run', '--strict')
                self.assertEqual(code, 0, out); self.assert_clean(root)
                code, out = self.invoke(root, 'status')
                self.assertEqual(code, 0, out); self.assertIn('VERIFY-STATE: green', out)
                evidence = json.loads((root / f'.verify-evidence/{mode}.json').read_text())
                self.assertEqual(evidence['actual'], 'P02 persisted note')

    def test_old_server_is_rejected_and_not_terminated(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as oldtmp:
            root, old = Path(tmp), Path(oldtmp)
            config = self.fixture(root, managed=False)
            self.fixture(old)
            (old / 'config.json').write_text(json.dumps({**config, 'owner':'unrelated-old-server'}))
            proc = subprocess.Popen([sys.executable, 'app.py', 'serve'], cwd=old, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                deadline = time.monotonic() + 8
                while not (old / 'pid.txt').exists() and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertTrue((old / 'pid.txt').exists(), 'control server did not launch')
                code, out = self.invoke(root, 'run')
                self.assertEqual(code, 1, out); self.assertIn('wrong owned build', out)
                self.assertIn('wrong owned build', json.loads((root / '.verify-state.json').read_text())['doctor']['output'])
                self.assertIsNone(proc.poll(), 'unrelated server was killed')
                with urlopen(f"http://127.0.0.1:{config['port']}/identity", timeout=2) as response:
                    self.assertEqual(json.load(response)['owner'], 'unrelated-old-server')
                self.assertFalse((root / '.verify-evidence/api.json').exists(), 'write ran against old server')
            finally:
                proc.terminate(); proc.wait(timeout=5)

    def test_cleanup_failure_cannot_leave_a_successful_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            (root / 'cleanup-fail.flag').touch()
            code, out = self.invoke(root, 'run')
            self.assertEqual(code, 1, 'cleanup failure silently accepted: ' + out)
            self.assertIn('cleanup deliberately failed', out)
            self.assert_clean(root)
            self.assertEqual(json.loads((root / '.verify-evidence/api.json').read_text())['actual'], 'P02 persisted note')
            self.assertNotEqual(self.invoke(root, 'status')[0], 0)
            code, out = self.invoke(root, 'run', '--json')
            self.assertEqual(code, 1, out)
            report = json.loads(out)
            self.assertEqual(report['verdict'], 'red')
            self.assertIn('cleanup deliberately failed', report['cleanup']['output'])
