import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
summary=json.loads((root/'evals/results/2026-10-13-1419/summary.json').read_text(encoding='utf-8'))
result=json.loads((root/'evals/results/2026-10-13-1419/scrutinize-unchanged-caller/with-1/result.json').read_text(encoding='utf-8'))
assert len(summary)==1 and summary[0]['passed'] is True
assert result['used_skill'] and result['skill_calls']
assert result['found']==3 and result['total']==3
assert result['changes']=={'changed': [], 'added': [], 'deleted': []}
actions=(root/'evals/results/2026-10-13-1419/scrutinize-unchanged-caller/with-1/actions.txt').read_text(encoding='utf-8')
assert 'git worktree add' in actions and 'git worktree remove' in actions
print('P06 live evidence: 1/1 passed, skill invoked, 3/3 findings, read-only worktree cleanup observed.')
