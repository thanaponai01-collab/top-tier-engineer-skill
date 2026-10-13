"""Disposable public HTTP/CLI note store for P02 application trials."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DATA = Path('build/data/note.json')

def save(value):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    if not Path('broken.flag').exists():
        DATA.write_text(json.dumps(value), encoding='utf-8')

def read():
    return json.loads(DATA.read_text(encoding='utf-8')) if DATA.exists() else None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            body = b'''<label>Note <input id="note"></label><button id="save">Save</button><button id="load">Reopen</button><output id="result"></output><script>
            save.onclick=async()=>{await fetch('/note',{method:'POST',body:JSON.stringify(note.value)});result.textContent='Saved'};
            load.onclick=async()=>{result.textContent=JSON.stringify(await(await fetch('/note')).json())};
            </script>'''
            self.send_response(200); self.send_header('Content-Type','text/html'); self.end_headers(); self.wfile.write(body)
            return
        if self.path == '/identity':
            value = {'build': 'p02-v1', 'owner': config['owner'], 'pid': os.getpid()}
        elif self.path == '/note':
            value = read()
        else:
            self.send_error(404); return
        self.reply(value)

    def do_POST(self):
        if self.path != '/note':
            self.send_error(404); return
        save(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
        self.reply({'saved': True})

    def reply(self, value):
        body = json.dumps(value).encode()
        self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(body)

    def log_message(self, *args):
        pass

if __name__ == '__main__':
    if sys.argv[1] == 'serve':
        config = json.loads(Path('config.json').read_text())
        server = HTTPServer(('127.0.0.1', config['port']), Handler)
        Path('pid.txt').write_text(str(os.getpid()))
        server.serve_forever()
    elif sys.argv[1] == 'put':
        save(sys.argv[2]); print('Saved')
    elif sys.argv[1] == 'get':
        print(json.dumps(read()))
