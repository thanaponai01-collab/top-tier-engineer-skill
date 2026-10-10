import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'skills/project-setup/scripts/foundation.py'
spec=importlib.util.spec_from_file_location('foundation',SCRIPT)
foundation=importlib.util.module_from_spec(spec)
spec.loader.exec_module(foundation)


class Foundation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo=Path(self.tmp.name).resolve()

    def put(self,name,text):
        path=self.repo/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text,encoding='utf-8')

    def complete(self, equivalents=False):
        paths={role:('notes/'+role+'.md' if equivalents else name)
               for role,name in foundation.DOCUMENTS.items()}
        for role,name in paths.items():
            self.put(name,'# '+role+'\nRecorded context.\n'+('## Next\nRun the selected check.\n' if role=='work' else ''))
        self.put('AGENTS.md','<!-- start-here -->\n'+'\n'.join(role+': '+name for role,name in paths.items())+'\n<!-- /start-here -->')
        return paths

    def cli(self,*args):
        result=subprocess.run([sys.executable,str(SCRIPT),'--repo',str(self.repo),*args],
                              capture_output=True,text=True,encoding='utf-8')
        return result.returncode,json.loads(result.stdout)

    def test_missing_foundation_is_reported_without_writes(self):
        code,result=self.cli('check')
        self.assertEqual(code,1)
        self.assertEqual(result['documents']['architecture']['state'],'missing')
        self.assertFalse((self.repo/'.project-context').exists())

    def test_equivalent_documents_and_pointers(self):
        paths=self.complete(True)
        self.assertEqual(foundation.check(self.repo)['issues'],[])
        self.assertEqual(foundation.roles(self.repo)[0],paths)

    def test_missing_pointer_is_not_full_setup(self):
        self.complete()
        self.put('AGENTS.md','<!-- start-here -->\nintent: BRIEF.md\nwork: BUILD.md\n<!-- /start-here -->')
        self.assertIn('startup must point to every foundation category',foundation.check(self.repo)['issues'])

    def test_refresh_detects_selected_source_change_and_noop(self):
        self.complete()
        self.put('src/main.py','print("first")\n')
        self.assertEqual(self.cli('remember','--sources','src/main.py')[0],0)
        before=(self.repo/'.project-context/foundation.json').stat().st_mtime_ns
        self.assertEqual(foundation.inventory(self.repo)['changed_inputs'],[])
        self.cli('remember')
        self.assertEqual(before,(self.repo/'.project-context/foundation.json').stat().st_mtime_ns)
        self.put('src/main.py','print("changed")\n')
        self.assertIn('src/main.py',foundation.inventory(self.repo)['changed_inputs'])

    def test_unknown_freshness_and_empty_document(self):
        self.complete()
        self.put('docs/architecture.md','')
        self.assertIn('unknown',foundation.inventory(self.repo)['freshness'])
        self.assertTrue(any('architecture: empty' in item for item in foundation.check(self.repo)['issues']))
        self.assertEqual(self.cli('remember')[0],1)
        self.assertFalse((self.repo/'.project-context/foundation.json').exists())

    def test_deleted_source_invalidates_snapshot(self):
        self.complete()
        self.put('src/main.py','pass\n')
        self.cli('remember','--sources','src/main.py')
        (self.repo/'src/main.py').unlink()
        self.assertIn('src/main.py',foundation.inventory(self.repo)['changed_inputs'])

    def test_outside_sources_are_rejected(self):
        with self.assertRaises(ValueError):
            foundation.inventory(self.repo,['../private.md'])


if __name__=='__main__':
    unittest.main()
