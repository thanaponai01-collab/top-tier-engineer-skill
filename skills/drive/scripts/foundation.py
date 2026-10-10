#!/usr/bin/env python3
"""Inventory/check setup documents and remember scoped input hashes; never verify behavior."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

DOCUMENTS = {'intent':'BRIEF.md', 'work':'BUILD.md', 'features':'FEATURES.md',
             'verify':'VERIFY.md', 'architecture':'docs/architecture.md',
             'commands':'docs/commands.md'}
INSTRUCTIONS = ('AGENTS.md', 'CLAUDE.md', '.claude/CLAUDE.md')
MANIFESTS = ('package.json','pyproject.toml','requirements.txt','Cargo.toml','go.mod',
             'pom.xml','build.gradle','Makefile','CMakeLists.txt','.claude-plugin/plugin.json')


def safe(repo, name):
    file = (repo / name).resolve()
    if not file.is_relative_to(repo) or '.git' in file.relative_to(repo).parts:
        raise ValueError('path outside project or inside .git: ' + name)
    return file


def text(repo, name):
    file = safe(repo, name)
    if file.stat().st_size > 512_000:
        raise ValueError('split oversized setup input: ' + name)
    return file.read_text(encoding='utf-8-sig')


def roles(repo):
    paths, blocks = dict(DOCUMENTS), []
    for name in INSTRUCTIONS:
        if safe(repo,name).is_file():
            for block in re.findall(r'<!-- start-here -->(.*?)<!-- /start-here -->',text(repo,name),re.S):
                blocks.append((name,block))
    if blocks:
        for role,path in re.findall(r'^\s*(intent|work|features|verify|architecture|commands):\s*(\S+)',blocks[0][1],re.M):
            safe(repo,path)
            paths[role] = path
    return paths,blocks


def hashes(repo, paths):
    return {name: hashlib.sha256(safe(repo,name).read_bytes()).hexdigest()
            if safe(repo,name).is_file() else None for name in dict.fromkeys(paths)}


def snapshot(repo):
    raw = repo / '.project-context/foundation.json'
    if safe(repo,'.project-context/foundation.json') != raw:
        raise ValueError('setup cache must not be redirected')
    return raw


def inventory(repo, sources=()):
    paths,blocks = roles(repo)
    cache = snapshot(repo)
    previous = json.loads(cache.read_text(encoding='utf-8')) if cache.is_file() else {}
    if not isinstance(previous,dict) or not isinstance(previous.get('inputs',{}),dict):
        raise ValueError('invalid setup snapshot; remove the cache and inspect inputs again')
    selected = list(dict.fromkeys([*previous.get('sources',[]),*sources,
                                  *(name for name in MANIFESTS if safe(repo,name).is_file())]))
    if len(selected)>100:
        raise ValueError('select at most 100 setup input paths; split by package/area')
    current = hashes(repo,[*paths.values(),*(name for name,_ in blocks),*selected])
    docs = {}
    for role,name in paths.items():
        docs[role] = {'path':name, 'state':'missing' if not safe(repo,name).is_file() else
                     'empty' if not text(repo,name).strip() else 'present'}
    return {'documents':docs,'startup_blocks':len(blocks),'sources':selected,'inputs':current,
            'changed_inputs':[name for name,value in current.items() if previous.get('inputs',{}).get(name)!=value]
                             if previous else [],
            'freshness':'compared scoped hashes' if previous else 'unknown; no setup snapshot',
            'coverage':'structural inventory of selected inputs, not semantic or behavioral proof'}


def check(repo, sources=()):
    result = inventory(repo,sources)
    issues = [role+': '+doc['state']+' '+doc['path'] for role,doc in result['documents'].items()
              if doc['state']!='present']
    paths,blocks = roles(repo)
    if len(blocks)!=1:
        issues.append('expected one startup block')
    elif len(blocks[0][1].strip().splitlines())>30:
        issues.append('startup block exceeds 30 lines')
    elif any(not re.search(r'^\s*'+role+r':\s*'+re.escape(name)+r'\s*$',blocks[0][1],re.M)
             for role,name in paths.items()):
        issues.append('startup must point to every foundation category')
    work = paths['work']
    if safe(repo,work).is_file() and not re.search(r'^## Next\s*\n\s*\S',text(repo,work),re.M):
        issues.append('missing Next: '+work)
    result['issues'] = issues
    return result


def main():
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path.cwd())
    parser.add_argument('action',choices=('inventory','check','remember'))
    parser.add_argument('--sources',nargs='*',default=[])
    args = parser.parse_args()
    try:
        repo=args.repo.resolve()
        result=check(repo,args.sources) if args.action in ('check','remember') else inventory(repo,args.sources)
        if args.action=='remember' and not result['issues']:
            cache=snapshot(repo)
            cache.parent.mkdir(exist_ok=True)
            payload=json.dumps({'sources':result['sources'],'inputs':result['inputs']},indent=2)+'\n'
            if not cache.exists() or cache.read_text(encoding='utf-8')!=payload:
                temporary=cache.with_suffix('.tmp')
                if temporary.is_symlink():
                    raise ValueError('temporary setup cache must not be redirected')
                temporary.write_text(payload,encoding='utf-8')
                temporary.replace(cache)
            result['snapshot']='recorded; does not certify correctness'
        # Hash values stay in the cache; the agent needs only changed paths and gaps.
        result.pop('inputs',None)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return int(bool(result.get('issues')))
    except (ValueError,OSError,UnicodeError) as exc:
        print(json.dumps({'error':str(exc)}))
        return 1


if __name__=='__main__':
    sys.exit(main())
