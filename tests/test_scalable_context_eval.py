"""The handoff grader must reject stale area notes and unrelated edits."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from _helpers import ROOT

sys.path.insert(0, str(Path(ROOT) / 'evals'))
import grade

class ScalableHandoff(unittest.TestCase):
    def test_area_upkeep_discriminates(self):
        case = grade.load_case('project-update-preserves-intent')
        base = Path(case['dir'])
        report = (base / 'reference/good.md').read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / 'repo'
            shutil.copytree(base / 'fixture', repo)
            self.assertFalse(grade.grade(case, report, str(repo))['passed'])
            (repo / 'BUILD.md').write_text(
                '# Current work\nLogin retains return URL; unverified. Session expiry unfinished.\n'
                '- include: work/auth.md\n- include: work/billing.md\n'
                '## Next\nVerify return URL and expiry checks.\n', encoding='utf-8')
            auth = repo / 'work/auth.md'
            auth.write_text(auth.read_text().replace('Login loses its return URL.',
                'Login retains its return URL; unverified.'), encoding='utf-8')
            shared = repo / 'work/redirect.md'
            original = shared.read_text()
            finished = original.replace('Helper always returns /.',
                'Helper preserves the requested target; unverified.')
            shared.write_text(finished, encoding='utf-8')
            self.assertTrue(grade.grade(case, report, str(repo))['passed'])
            shared.write_text(finished + '\nHelper always returns /.\n', encoding='utf-8')
            result = grade.grade(case, report, str(repo))
            self.assertFalse(result['passed'])
            self.assertTrue(any(c['id'] == 'stale-removed' and not c['ok']
                for c in result['workdir']['checks']))
            shared.write_text(finished, encoding='utf-8')
            billing = repo / 'work/billing.md'
            billing.write_text('Completed.\n', encoding='utf-8')
            result = grade.grade(case, report, str(repo))
            self.assertFalse(result['passed'])
            self.assertIn('work/billing.md', [v['path'] for v in result['workdir']['violations']])
