#!/usr/bin/env python3
"""Objective code metrics for each build. Reads benchmark/builds, writes benchmark/metrics/metrics.json.
Un-blinds A/B -> baseline/ponytail using the same parity rule the workflow used:
  task index i (0-based): A is baseline when i is even, else A is ponytail.
"""
import json, os, re, math, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILDS = os.path.join(ROOT, 'builds')
TASKS = json.load(open(os.path.join(ROOT, 'tasks.json'), encoding='utf-8'))

PY_STDLIB = set('''sys os re json math random time datetime collections itertools functools
typing argparse csv io string heapq bisect dataclasses enum decimal fractions statistics
unittest abc copy hashlib pathlib urllib http socket textwrap operator'''.split())

CODE_EXT = {'.py','.js','.mjs','.ts','.html','.htm','.css','.json'}

def is_comment_line(line, ext, state):
    s = line.strip()
    if not s:
        return True, state  # blank counts as non-code
    if state['block']:
        if '*/' in s:
            state['block'] = False
        return True, state
    if ext in ('.py',):
        return s.startswith('#'), state
    if ext in ('.js','.mjs','.ts','.css'):
        if s.startswith('//'):
            return True, state
        if s.startswith('/*'):
            if '*/' not in s:
                state['block'] = True
            return True, state
        return False, state
    if ext in ('.html','.htm'):
        if s.startswith('<!--'):
            if '-->' not in s:
                state['block'] = True  # crude
            return True, state
        return False, state
    return False, state

def count_imports(text, ext):
    if ext == '.py':
        ext_deps = set()
        for m in re.finditer(r'^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)', text, re.M):
            top = m.group(1).split('.')[0]
            if top not in PY_STDLIB:
                ext_deps.add(top)
        return len(ext_deps)
    if ext in ('.js','.mjs','.ts'):
        deps = set()
        for m in re.finditer(r'require\(\s*[\'"]([^\'"]+)[\'"]\s*\)', text):
            mod = m.group(1)
            if not mod.startswith('.') and not mod.startswith('node:'):
                deps.add(mod.split('/')[0])
        for m in re.finditer(r'from\s+[\'"]([^\'"]+)[\'"]', text):
            mod = m.group(1)
            if not mod.startswith('.') and not mod.startswith('node:'):
                deps.add(mod.split('/')[0])
        return len(deps)
    return 0

def measure_dir(d):
    files = []
    total_lines = code_lines = chars = ext_deps = 0
    has_test = False
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if not os.path.isfile(p):
                continue
            ext = os.path.splitext(name)[1].lower()
            files.append(name)
            try:
                text = open(p, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            chars += len(text)
            if name.lower() in ('package.json',) :
                try:
                    pj = json.loads(text)
                    ext_deps += len(pj.get('dependencies', {}) or {})
                except Exception:
                    pass
            lines = text.splitlines()
            total_lines += len(lines)
            state = {'block': False}
            for ln in lines:
                comment, state = is_comment_line(ln, ext, state)
                if not comment:
                    code_lines += 1
            if ext in CODE_EXT and name.lower() != 'package.json':
                ext_deps += count_imports(text, ext)
            if re.search(r'test|assert|selfcheck|self_check|__main__', text):
                has_test = True
    return {
        'files': files,
        'file_count': len(files),
        'total_lines': total_lines,
        'code_lines': code_lines,
        'chars': chars,
        'artifact_tokens_est': math.ceil(chars/4),
        'ext_dependencies': ext_deps,
        'has_check': has_test,
    }

out = {}
for i, t in enumerate(TASKS):
    a_is_baseline = (i % 2 == 0)
    da = os.path.join(BUILDS, t['id'], 'A')
    db = os.path.join(BUILDS, t['id'], 'B')
    baseline_dir = da if a_is_baseline else db
    ponytail_dir = db if a_is_baseline else da
    out[t['id']] = {
        'title': t['title'], 'domain': t['domain'], 'difficulty': t['difficulty'], 'lang': t['lang'],
        'a_is_baseline': a_is_baseline,
        'baseline': measure_dir(baseline_dir),
        'ponytail': measure_dir(ponytail_dir),
    }

os.makedirs(os.path.join(ROOT, 'metrics'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'metrics', 'metrics.json'), 'w', encoding='utf-8'), indent=2)
print('wrote metrics for', len(out), 'tasks')
for tid, m in out.items():
    b, p = m['baseline'], m['ponytail']
    print(f"{tid:8} base {b['code_lines']:4} cl / {b['file_count']} files | pony {p['code_lines']:4} cl / {p['file_count']} files")
