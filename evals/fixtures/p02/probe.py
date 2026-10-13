"""Independent expectations from P02: owned build and persisted public writes."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

config = json.loads(Path('config.json').read_text())
url = 'http://127.0.0.1:' + str(config['port'])

def get(path):
    with urlopen(url + path, timeout=2) as response:
        return json.load(response)

mode = sys.argv[1]
if mode == 'ready':
    get('/identity')
elif mode == 'doctor':
    identity = get('/identity')
    assert identity['owner'] == config['owner'] and identity['build'] == 'p02-v1', 'wrong owned build'
    assert identity['pid'] == int(Path('pid.txt').read_text()), 'wrong owned process'
    print(json.dumps(identity))
elif mode == 'cleanup':
    shutil.rmtree('build/data', ignore_errors=True)
    if Path('cleanup-fail.flag').exists():
        raise SystemExit('cleanup deliberately failed')
elif mode in ('api', 'cli'):
    expected = 'P02 persisted note'
    if mode == 'api':
        with urlopen(Request(url + '/note', data=json.dumps(expected).encode(), method='POST'), timeout=2) as response:
            ack = json.load(response)
        actual = get('/note')
    else:
        ack = subprocess.check_output([sys.executable, 'app.py', 'put', expected], text=True).strip()
        actual = json.loads(subprocess.check_output([sys.executable, 'app.py', 'get'], text=True))
    Path('.verify-evidence').mkdir(exist_ok=True)
    Path('.verify-evidence/' + mode + '.json').write_text(json.dumps({'ack':ack,'expected':expected,'actual':actual}), encoding='utf-8')
    assert actual == expected, 'expected persisted note, got ' + repr(actual)
    print('persisted note verified through second public read')
