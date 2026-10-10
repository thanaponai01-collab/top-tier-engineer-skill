#!/usr/bin/env python3
"""Bounded project-memory retrieval. Files own facts; SQLite is a rebuildable cache."""
import argparse
from collections import deque
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

VERSION = 2
ROOTS = ('BRIEF.md', 'BUILD.md', 'FEATURES.md', 'VERIFY.md', 'WHY.md',
         'PLAN.md', 'docs/architecture.md', 'docs/arch-design.md')
INSTRUCTIONS = ('AGENTS.md', 'CLAUDE.md', '.claude/CLAUDE.md')
HISTORY = {'completed', 'archived', 'superseded'}
MAX_FILES = 500
MAX_BYTES = 512_000


def local(repo, path):
    candidate = (repo / path).resolve()
    if not candidate.is_relative_to(repo) or '.git' in candidate.relative_to(repo).parts:
        raise ValueError('path outside project or inside .git: ' + str(path))
    return candidate


def read(repo, path):
    file = local(repo, path)
    if file.stat().st_size > MAX_BYTES:
        raise ValueError('context file exceeds 512KB; split it: ' + str(path))
    return file.read_text(encoding='utf-8-sig')


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def structure(text):
    """Hide fenced examples while preserving offsets for section extraction."""
    return re.sub(r'(?ms)^(```|~~~)[^\n]*\n.*?^\1[^\n]*$',
                  lambda match: re.sub(r'[^\n]', ' ', match[0]), text)


def pointers(repo):
    result = {'intent': 'BRIEF.md', 'work': 'BUILD.md'}
    for path in INSTRUCTIONS:
        if not local(repo, path).is_file():
            continue
        text = read(repo, path)
        block = re.search(r'<!-- start-here -->(.*?)<!-- /start-here -->', text, re.S)
        if block:
            for role, value in re.findall(r'^\s*(intent|work):\s*(\S+)', block[1], re.M):
                local(repo, value)
                result[role] = value
            break
    return result


def links(path, text):
    text = structure(text)
    found = re.findall(r'^\s*(?:[-*]\s+)?include:\s*(\S+)', text, re.M)
    found += re.findall(r'\]\(([^)]+)\)', text)
    result = []
    for value in found:
        value = value.strip('<>').split('#', 1)[0]
        if not value or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', value):
            continue
        # Existing include paths are project-relative; Markdown links are file-relative.
        is_include = bool(re.search(r'include:\s*' + re.escape(value), text))
        result.append(value if is_include else str(Path(path).parent / value))
    return result


def discover(repo, max_files=MAX_FILES):
    queue = deque(dict.fromkeys((*ROOTS, *pointers(repo).values())))
    seen, files, warnings = set(), [], []
    while queue and len(files) < max_files:
        path = queue.popleft()
        try:
            file = local(repo, path)
            path = file.relative_to(repo).as_posix()
            if path in seen:
                continue
            seen.add(path)
            if not file.is_file() or file.suffix.lower() != '.md':
                continue
            text = read(repo, path)
            files.append(path)
            queue.extend(links(path, text))
        except (ValueError, OSError, UnicodeError) as exc:
            warnings.append(str(exc))
    if queue:
        warnings.append(f'discovery truncated at {max_files} files; use explicit area paths')
    return files, warnings


def records(path, text):
    clean = structure(text)
    headings = list(re.finditer(r'^#{1,3}\s+(.+)$', clean, re.M))
    prefix = clean[:headings[0].start()] if headings else clean
    meta = dict(re.findall(r'<!-- context-([a-z]+):\s*(.*?)\s*-->', prefix))
    default_type = {'BRIEF.md': 'intent', 'BUILD.md': 'task', 'FEATURES.md': 'feature',
                    'VERIFY.md': 'check', 'WHY.md': 'decision'}.get(Path(path).name, 'document')
    chunks = [(path, text)] if 'id' in meta or not headings else [
        (m[1], text[m.start():headings[i+1].start() if i+1 < len(headings) else len(text)])
        for i, m in enumerate(headings)]
    rows, occurrences = [], {}
    for i, (title, body) in enumerate(chunks):
        occurrences[title] = occurrences.get(title, 0) + 1
        suffix = '' if occurrences[title] == 1 else ':' + str(occurrences[title])
        plain = re.sub(r'<!--.*?-->', '', body, flags=re.S).strip()
        code_paths = meta.get('paths', '')
        inferred = re.findall(r'@\s+([^\s>`]+)', body)
        paths = sorted(set(filter(None, [p.strip() for p in code_paths.split(',')] + inferred)))
        rows.append(dict(id=meta.get('id', f'{path}#{title}{suffix}'), path=path,
                         title=(headings[0][1] if 'id' in meta and headings else title),
                         kind=meta.get('type', default_type), area=meta.get('area', ''),
                         status=meta.get('status', 'archived' if '.archive.' in path else 'unknown'),
                         paths=paths, links=[p.strip() for p in meta.get('links', '').split(',') if p.strip()],
                         body=plain, hash=digest(text)))
    return rows


@contextmanager
def database(repo, write=False):
    path = cache_path(repo)
    if not write and not path.is_file():
        raise ValueError('index missing; using file fallback')
    if write:
        path.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(path if write else path.as_uri() + '?mode=ro', uri=not write)
    try:
        version = con.execute('PRAGMA user_version').fetchone()[0]
        if version != VERSION and not (write and version == 0):
            raise ValueError('index schema mismatch; use index --rebuild or file fallback')
        if write:
            con.executescript('''CREATE TABLE IF NOT EXISTS records (
              id TEXT PRIMARY KEY, path TEXT, title TEXT, kind TEXT, area TEXT, status TEXT,
              paths TEXT, links TEXT, body TEXT, hash TEXT);
              CREATE INDEX IF NOT EXISTS records_path ON records(path);
              CREATE TABLE IF NOT EXISTS associations (id TEXT, path TEXT);
              CREATE INDEX IF NOT EXISTS association_path ON associations(path);
              CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(id UNINDEXED, title, body);
              PRAGMA user_version=2;''')
        con.row_factory = sqlite3.Row
        with con:
            yield con
    finally:
        con.close()


def cache_path(repo):
    path = repo / '.project-context/index.sqlite'
    if local(repo, '.project-context/index.sqlite') != path:
        raise ValueError('cache must not be a symlink or redirected directory')
    return path


def index(repo, files=None, rebuild=False):
    if rebuild:
        cache_path(repo).unlink(missing_ok=True)
    selected, warnings = (files, []) if files is not None else discover(repo)
    with database(repo, True) as con:
        if files is None:
            con.execute('DELETE FROM records')
            con.execute('DELETE FROM search')
            con.execute('DELETE FROM associations')
        changed = 0
        for path in dict.fromkeys(selected):
            file = local(repo, path)
            path = file.relative_to(repo).as_posix()
            if file.exists() and file.suffix.lower() != '.md':
                raise ValueError('index accepts context Markdown only: ' + path)
            text = read(repo, path) if file.is_file() else None
            old = con.execute('SELECT hash FROM records WHERE path=? LIMIT 1', (path,)).fetchone()
            if old and text is not None and old[0] == digest(text):
                continue
            con.execute('DELETE FROM search WHERE id IN (SELECT id FROM records WHERE path=?)', (path,))
            con.execute('DELETE FROM associations WHERE id IN (SELECT id FROM records WHERE path=?)', (path,))
            con.execute('DELETE FROM records WHERE path=?', (path,))
            for row in records(path, text) if text is not None else []:
                con.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?)',
                            tuple(json.dumps(row[k]) if k in ('paths','links') else row[k]
                                  for k in ('id','path','title','kind','area','status','paths','links','body','hash')))
                con.execute('INSERT INTO search VALUES (?,?,?)', (row['id'],row['title'],row['body']))
                con.executemany('INSERT INTO associations VALUES (?,?)',
                                [(row['id'], p) for p in row['paths']])
            changed += 1
    return dict(changed_files=changed, selected_files=len(selected), warnings=warnings)


def unpack(row):
    result = dict(row)
    for key in ('paths', 'links'):
        result[key] = json.loads(result[key])
    return result


def retrieve(repo, action, terms, history=False, limit=5):
    warnings, rows = [], []
    try:
        with database(repo) as con:
            current = '' if history else " AND records.status NOT IN ('completed','archived','superseded')"
            if action == 'search':
                words = re.findall(r'\w+', ' '.join(terms))[:20]
                query = ' OR '.join('"' + w + '"' for w in words)
                if query:
                    rows = [unpack(r) for r in con.execute(
                        'SELECT records.* FROM search JOIN records ON records.id=search.id '
                        'WHERE search MATCH ?' + current + ' ORDER BY rank LIMIT 100', (query,))]
            elif action == 'show':
                rows = [unpack(r) for r in con.execute('SELECT * FROM records WHERE id=?', (terms[0],))]
            elif action == 'affected':
                clauses, values = [], []
                for term in terms:
                    clauses.append('(associations.path=? OR substr(associations.path,1,?)=?)')
                    prefix = term.rstrip('/')+'/'
                    values.extend((term, len(prefix), prefix))
                rows = [unpack(r) for r in con.execute(
                    'SELECT DISTINCT records.* FROM records JOIN associations ON records.id=associations.id '
                    'WHERE ('+' OR '.join(clauses)+')'+current+' LIMIT 100', values)]
        refreshed, seen, sources = [], set(), {}
        for row in rows:
            if row['path'] in seen:
                continue
            if row['path'] not in sources:
                text = read(repo, row['path']) if local(repo, row['path']).is_file() else None
                sources[row['path']] = (text, digest(text) if text is not None else None)
            text, current_hash = sources[row['path']]
            if text is None or current_hash != row['hash']:
                seen.add(row['path'])
                warnings.append('stale-index: ' + row['path'])
                if text is not None:
                    refreshed.extend(records(row['path'], text))
            else:
                refreshed.append(row)
        rows = refreshed
    except (sqlite3.Error, ValueError, OSError, UnicodeError) as exc:
        warnings.append(str(exc))
        files, notes = discover(repo, max_files=50)
        warnings.extend(notes)
        for path in files:
            try:
                rows.extend(records(path, read(repo, path)))
            except (ValueError, OSError, UnicodeError) as error:
                warnings.append(str(error))
    if action == 'search':
        words = re.findall(r'\w+', ' '.join(terms).lower())[:20]
        rows = [r for r in rows if any(w in (r['title']+' '+r['body']).lower() for w in words)]
    elif action == 'show':
        rows = [r for r in rows if r['id'] == terms[0]]
    elif action == 'affected':
        rows = [r for r in rows if any(p == t or p.startswith(t.rstrip('/')+'/')
                                      for p in r['paths'] for t in terms)]
        if not rows:
            warnings.append('no path associations found; coverage gap, inspect shared callers')
    if not history and action != 'show':
        rows = [r for r in rows if r['status'] not in HISTORY]
    result = []
    for row in rows[:limit]:
        item = {k: row[k] for k in ('id','path','title','kind','area','status','paths','links')}
        item['excerpt'] = row['body'][:4000 if action == 'show' else 240]
        item['truncated'] = len(row['body']) > (4000 if action == 'show' else 240)
        result.append(item)
    return dict(records=result, warnings=warnings, more=len(rows)>limit,
                coverage='indexed context graph; new/unindexed records require upkeep')


def check(repo, files=None):
    selected, warnings = (files, []) if files is not None else discover(repo)
    issues, ids, related = list(warnings), set(), []
    startup = []
    for path in INSTRUCTIONS:
        if local(repo, path).is_file():
            text = read(repo, path)
            startup.extend(re.findall(r'<!-- start-here -->(.*?)<!-- /start-here -->', text, re.S))
    if len(startup) != 1:
        issues.append('expected one start-here block; found ' + str(len(startup)))
    elif len(startup[0].strip().splitlines()) > 30:
        issues.append('start-here exceeds 30 lines')
    for path in selected:
        if not local(repo, path).is_file():
            issues.append('missing context file: ' + path)
            continue
        text = read(repo, path)
        budget = {'BRIEF.md':120, 'BUILD.md':80, 'FEATURES.md':150, 'VERIFY.md':150,
                  'WHY.md':300}.get(Path(path).name, 80)
        if '.archive.' not in path and len(text.splitlines()) > budget:
            issues.append(f'over budget: {path} ({budget} lines)')
        for link in links(path, text):
            try:
                if not local(repo, link).exists():
                    issues.append(f'broken link: {path} -> {link}')
            except ValueError as exc:
                issues.append(str(exc))
        for row in records(path, text):
            if row['id'] in ids:
                issues.append('duplicate record ID: ' + row['id'])
            ids.add(row['id'])
            related.extend((row['id'], target) for target in row['links'])
    if files is not None:
        try:
            with database(repo) as con:
                ids.update(row[0] for row in con.execute('SELECT id FROM records'))
        except (ValueError, sqlite3.Error):
            if related:
                issues.append('record links require full check or an updated index')
    for origin, target in related:
        if target not in ids:
            issues.append(f'broken record link: {origin} -> {target}')
    roles = pointers(repo)
    for role, path in roles.items():
        if not local(repo, path).is_file():
            issues.append('missing '+role+': '+path)
    if local(repo, roles['work']).is_file():
        text = read(repo, roles['work'])
        if not re.search(r'^## Next\s*\n\s*\S', text, re.M):
            issues.append('missing actionable Next: '+roles['work'])
    return dict(issues=issues, coverage='structural only; not product correctness')


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ('search','show','affected'):
        command = sub.add_parser(name)
        command.add_argument('terms', nargs='+' if name != 'show' else 1)
        command.add_argument('--limit', type=int, default=5, choices=range(1,21))
        command.add_argument('--history', action='store_true')
    sub.add_parser('next')
    for name in ('index','check'):
        command = sub.add_parser(name)
        command.add_argument('--files', nargs='+')
        if name == 'index':
            command.add_argument('--rebuild', action='store_true')
    args = parser.parse_args()
    repo = args.repo.resolve()
    try:
        if args.action == 'index':
            result = index(repo, args.files, args.rebuild)
        elif args.action == 'check':
            result = check(repo, args.files)
        elif args.action == 'next':
            result = {'sources': []}
            if local(repo, 'RUN.json').is_file():
                result['execution_state_source'] = 'RUN.json is authoritative; inspect it before acting on summary Next'
            for role, path in pointers(repo).items():
                if local(repo, path).is_file():
                    text = read(repo, path)
                    result['sources'].append(dict(role=role, path=path, excerpt=text[:4000],
                                                   truncated=len(text)>4000))
        else:
            result = retrieve(repo,args.action,args.terms,args.history,args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get('issues') else 0
    except (ValueError, OSError, sqlite3.Error, UnicodeError) as exc:
        print(json.dumps({'error':str(exc)}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
