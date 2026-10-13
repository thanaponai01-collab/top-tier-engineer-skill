"""P02 bounded scratch mutations; never modifies the user's working tree."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / 'skills/verify-loop/scripts/verify.py').read_text()
mutations = {
    'skip-cli-cleanup': ('if proc or (recipe and recipe.get("stop")):', 'if proc:'),
    'ignore-stop-failure': ('result = run_check(stop_cmd, repo, timeout)', 'run_check(stop_cmd, repo, timeout)'),
    'skip-doctor': ('if recipe and recipe.get("doctor"):', 'if False:'),
}
for name, (old, new) in mutations.items():
    assert source.count(old) == 1, name
    with tempfile.TemporaryDirectory(prefix='p02-mutation-') as tmp:
        root = Path(tmp)
        shutil.copytree(ROOT / 'skills/verify-loop/scripts', root / 'skills/verify-loop/scripts')
        shutil.copytree(ROOT / 'evals/fixtures/p02', root / 'evals/fixtures/p02')
        (root / 'tests').mkdir()
        for file in ('_helpers.py', 'test_verify.py', 'test_project_recipe.py'):
            shutil.copyfile(ROOT / 'tests' / file, root / 'tests' / file)
        (root / 'skills/verify-loop/scripts/verify.py').write_text(source.replace(old, new), encoding='utf-8')
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', 'tests', '-p', 'test_project_recipe.py'], cwd=root, capture_output=True, text=True, timeout=60)
        (ROOT / 'work/p02' / (name + '.txt')).write_text(result.stdout + result.stderr, encoding='utf-8')
        assert result.returncode != 0 and 'FAIL:' in result.stderr and 'FAILED' in result.stderr, name + ' survived or harness broke'
        print(name + ': rejected by application acceptance assertions')
