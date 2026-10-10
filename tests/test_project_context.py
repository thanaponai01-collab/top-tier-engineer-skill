import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/project-context/scripts/context.py'
spec = importlib.util.spec_from_file_location('project_context', SCRIPT)
context = importlib.util.module_from_spec(spec)
spec.loader.exec_module(context)


class ProjectContext(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name).resolve()
        self.put('AGENTS.md', '<!-- start-here -->\nintent: BRIEF.md\nwork: BUILD.md\n<!-- /start-here -->')
        self.put('BRIEF.md', '# Goal\nPreserve owner intent.\n')
        self.put('BUILD.md', '# Work\n## Next\nVerify expiry.\n- include: work/auth.md\n')
        self.put('work/auth.md', '<!-- context-id: task:auth -->\n<!-- context-status: active -->\n'
                 '<!-- context-paths: src/auth.py -->\n# Login\nExpiry remains unverified.\n')

    def put(self, path, text):
        file = self.repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding='utf-8')

    def test_cli_retrieves_without_writing_cache(self):
        run = subprocess.run([sys.executable,str(SCRIPT),'--repo',str(self.repo),'search','expiry'],
                             capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        result = json.loads(run.stdout)
        self.assertTrue(result['records'])
        self.assertFalse((self.repo/'.project-context').exists())

    def test_sql_search_show_and_path_impact(self):
        context.index(self.repo)
        self.assertEqual(context.retrieve(self.repo,'show',['task:auth'])['records'][0]['path'],'work/auth.md')
        self.assertEqual(context.retrieve(self.repo,'affected',['src/auth.py'])['records'][0]['id'],'task:auth')
        self.assertTrue(context.retrieve(self.repo,'search',['expiry'])['records'])

    def test_incremental_noop_and_deletion(self):
        context.index(self.repo)
        self.assertEqual(context.index(self.repo,['work/auth.md'])['changed_files'],0)
        self.put('work/auth.md','# Login\nChanged result.\n')
        self.assertEqual(context.index(self.repo,['work/auth.md'])['changed_files'],1)
        (self.repo/'work/auth.md').unlink()
        context.index(self.repo,['work/auth.md'])
        self.assertFalse(context.retrieve(self.repo,'search',['Changed'])['records'])

    def test_stale_cache_reads_actual_source(self):
        context.index(self.repo)
        self.put('work/auth.md','<!-- context-id: task:auth -->\n# Login\nExpiry check failed.\n')
        result = context.retrieve(self.repo,'show',['task:auth'])
        self.assertIn('failed',result['records'][0]['excerpt'])
        self.assertIn('stale-index: work/auth.md',result['warnings'])

    def test_duplicate_id_rolls_back_incremental_update(self):
        context.index(self.repo)
        self.put('work/duplicate.md','<!-- context-id: task:auth -->\n# Wrong\n')
        with self.assertRaises(sqlite3.IntegrityError):
            context.index(self.repo,['work/duplicate.md'])
        self.assertEqual(context.retrieve(self.repo,'show',['task:auth'])['records'][0]['title'],'Login')

    def test_corrupt_cache_fallback_and_rebuild(self):
        context.index(self.repo)
        (self.repo/'.project-context/index.sqlite').write_bytes(b'broken')
        self.assertTrue(context.retrieve(self.repo,'search',['expiry'])['records'])
        context.index(self.repo,rebuild=True)
        self.assertFalse(context.retrieve(self.repo,'show',['task:auth'])['warnings'])

    def test_history_and_bounded_output(self):
        self.put('work/auth.md','<!-- context-id: task:auth -->\n<!-- context-status: completed -->\n# Login\n'+ 'expiry '*1000)
        context.index(self.repo)
        self.assertFalse(context.retrieve(self.repo,'search',['expiry'])['records'][-1]['status']=='completed')
        result = context.retrieve(self.repo,'show',['task:auth'])['records'][0]
        self.assertEqual(len(result['excerpt']),4000)
        self.assertTrue(result['truncated'])
        self.assertTrue(any(r['status']=='completed' for r in context.retrieve(self.repo,'search',['expiry'],True)['records']))

    def test_escape_and_symlink_rejected(self):
        with self.assertRaises(ValueError):
            context.index(self.repo,['../outside.md'])
        with self.assertRaises(ValueError):
            context.local(self.repo,'.git/config')

    def test_equivalent_pointer_and_broken_link(self):
        self.put('AGENTS.md','<!-- start-here -->\nintent: spec.md\nwork: BUILD.md\n<!-- /start-here -->')
        self.put('spec.md','# Intent\nOwner goal.\n[missing](absent.md)\n')
        self.assertIn('spec.md',context.discover(self.repo)[0])
        self.assertTrue(any('broken link' in i for i in context.check(self.repo)['issues']))

    def test_large_history_result_limit(self):
        self.put('work/auth.md','\n'.join(f'## Task {i}\nExpiry item {i}' for i in range(1000)))
        context.index(self.repo)
        result = context.retrieve(self.repo,'search',['expiry'],limit=5)
        self.assertEqual(len(result['records']),5)
        self.assertTrue(result['more'])

    def test_incremental_reads_only_selected_file(self):
        context.index(self.repo)
        with patch.object(context, 'read', wraps=context.read) as reader:
            context.index(self.repo, ['work/auth.md'])
        self.assertEqual([call.args[1] for call in reader.call_args_list], ['work/auth.md'])

    def test_query_hashes_each_matching_source_once(self):
        self.put('work/auth.md', '\n'.join(f'## Task {i}\nExpiry item {i}' for i in range(1000)))
        context.index(self.repo)
        with patch.object(context, 'read', wraps=context.read) as reader:
            context.retrieve(self.repo, 'search', ['expiry'])
        paths = [call.args[1] for call in reader.call_args_list]
        self.assertEqual(paths.count('work/auth.md'), 1)

    def test_inserted_heading_preserves_existing_record_id(self):
        self.put('work/auth.md', '# Login\nResult.\n## Expiry\nUnknown.\n')
        before = context.records('work/auth.md', context.read(self.repo, 'work/auth.md'))
        self.put('work/auth.md', '# Intro\nNew.\n# Login\nResult.\n## Expiry\nUnknown.\n')
        after = context.records('work/auth.md', context.read(self.repo, 'work/auth.md'))
        self.assertEqual(before[1]['id'], after[2]['id'])

    def test_fenced_examples_are_not_records_or_links(self):
        text = '# Guide\n```markdown\n<!-- context-id: fake -->\n# Example\n[bad](missing.md)\n```\n'
        rows = context.records('guide.md', text)
        self.assertEqual(len(rows), 1)
        self.assertNotEqual(rows[0]['id'], 'fake')
        self.assertEqual(context.links('guide.md', text), [])


if __name__ == '__main__':
    unittest.main()
