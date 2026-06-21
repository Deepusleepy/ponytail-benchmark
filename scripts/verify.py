#!/usr/bin/env python3
"""Functional verification of each build. Writes benchmark/verify.json (keyed by task -> arm A/B)."""
import json, os, subprocess, sys, time, glob, urllib.request, urllib.error, socket

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILDS = os.path.join(ROOT, 'builds')

PRIMARY = {
    'task-01': ('server','server.js'), 'task-02': ('server','server.js'),
    'task-03': ('node','limiter.js'),
    'task-04': ('html','index.html'), 'task-05': ('html','index.html'), 'task-06': ('html','index.html'),
    'task-07': ('py','slugify.py'), 'task-08': ('py','lru.py'), 'task-09': ('py','calc.py'),
    'task-10': ('pyflag','csv2json.py'), 'task-11': ('py','sales.py'), 'task-12': ('py','solution.py'),
}

def find_file(d, expected, exts):
    p = os.path.join(d, expected)
    if os.path.isfile(p):
        return p
    cands = []
    for e in exts:
        cands += glob.glob(os.path.join(d, '*'+e))
    return cands[0] if cands else None

def tail(s, n=1500):
    s = s or ''
    return s[-n:]

def run_py(path, args=None):
    args = args or []
    try:
        r = subprocess.run([sys.executable, path]+args, capture_output=True, text=True, timeout=30, cwd=os.path.dirname(path))
        ok = r.returncode == 0
        return {'ran': True, 'exit': r.returncode, 'ok': ok, 'output': tail((r.stdout or '')+(r.stderr or ''))}
    except subprocess.TimeoutExpired:
        return {'ran': True, 'exit': None, 'ok': False, 'output': 'TIMEOUT (30s)'}
    except Exception as e:
        return {'ran': False, 'exit': None, 'ok': False, 'output': f'ERROR: {e}'}

def run_node(path, args=None):
    args = args or []
    try:
        r = subprocess.run(['node', path]+args, capture_output=True, text=True, timeout=30, cwd=os.path.dirname(path), shell=False)
        ok = r.returncode == 0
        return {'ran': True, 'exit': r.returncode, 'ok': ok, 'output': tail((r.stdout or '')+(r.stderr or ''))}
    except subprocess.TimeoutExpired:
        return {'ran': True, 'exit': None, 'ok': False, 'output': 'TIMEOUT (30s)'}
    except Exception as e:
        return {'ran': False, 'exit': None, 'ok': False, 'output': f'ERROR: {e}'}

def port_open(port, host='127.0.0.1'):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(0.3)
    try:
        s.connect((host, port)); s.close(); return True
    except Exception:
        return False

def http(method, url, data=None):
    try:
        req = urllib.request.Request(url, method=method,
            data=json.dumps(data).encode() if data is not None else None,
            headers={'Content-Type':'application/json'} if data is not None else {})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode(errors='replace')[:400]
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode(errors='replace')[:400] if e.fp else '')
    except Exception as e:
        return None, f'ERR {e}'

def smoke_server(path, kind):
    # syntax check first
    chk = subprocess.run(['node','--check', path], capture_output=True, text=True)
    if chk.returncode != 0:
        return {'ran': True, 'exit': chk.returncode, 'ok': False, 'output': 'node --check FAILED: '+tail(chk.stderr,800)}
    # free the port if held
    proc = subprocess.Popen(['node', path], cwd=os.path.dirname(path),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log = []
    try:
        for _ in range(40):
            if port_open(3000): break
            if proc.poll() is not None: break
            time.sleep(0.1)
        if proc.poll() is not None:
            out = proc.stdout.read() if proc.stdout else ''
            return {'ran': True, 'exit': proc.returncode, 'ok': False, 'output': 'server exited early: '+tail(out,800)}
        if not port_open(3000):
            return {'ran': True, 'exit': None, 'ok': False, 'output': 'port 3000 never opened'}
        if kind == 'health':
            s1, b1 = http('GET','http://127.0.0.1:3000/health')
            s2, b2 = http('GET','http://127.0.0.1:3000/time')
            s3, b3 = http('GET','http://127.0.0.1:3000/nope')
            ok = s1==200 and 'ok' in b1 and s2==200 and 'now' in b2 and s3==404
            log = [f'GET /health -> {s1} {b1}', f'GET /time -> {s2} {b2}', f'GET /missing -> {s3}']
        else:  # todo api
            s1, b1 = http('GET','http://127.0.0.1:3000/todos')
            s2, b2 = http('POST','http://127.0.0.1:3000/todos', {'title':'buy milk'})
            s3, b3 = http('POST','http://127.0.0.1:3000/todos', {'title':''})
            s4, b4 = http('GET','http://127.0.0.1:3000/todos')
            ok = s1==200 and s2==201 and s3==400 and s4==200 and 'buy milk' in b4
            log = [f'GET /todos -> {s1}', f'POST valid -> {s2} {b2}', f'POST empty -> {s3}', f'GET /todos -> {s4} {b4}']
        return {'ran': True, 'exit': 0 if ok else 1, 'ok': ok, 'output': ' | '.join(log)}
    finally:
        try:
            proc.terminate(); proc.wait(timeout=3)
        except Exception:
            try:
                subprocess.run(['taskkill','/F','/T','/PID',str(proc.pid)], capture_output=True)
            except Exception: pass

out = {}
for tid, (kind, fname) in PRIMARY.items():
    out[tid] = {}
    for arm in ('A','B'):
        d = os.path.join(BUILDS, tid, arm)
        if kind == 'html':
            f = find_file(d, fname, ['.html','.htm'])
            out[tid][arm] = {'ran': False, 'exit': None, 'ok': bool(f), 'output': 'visual (screenshot)' if f else 'no html file'}
            continue
        if kind == 'py':
            f = find_file(d, fname, ['.py'])
            out[tid][arm] = run_py(f) if f else {'ran':False,'exit':None,'ok':False,'output':'no .py file'}
        elif kind == 'pyflag':
            f = find_file(d, fname, ['.py'])
            out[tid][arm] = run_py(f, ['--selfcheck']) if f else {'ran':False,'exit':None,'ok':False,'output':'no .py file'}
        elif kind == 'node':
            f = find_file(d, fname, ['.js','.mjs'])
            out[tid][arm] = run_node(f) if f else {'ran':False,'exit':None,'ok':False,'output':'no .js file'}
        elif kind == 'server':
            f = find_file(d, fname, ['.js','.mjs'])
            sub = 'health' if tid=='task-01' else 'todo'
            out[tid][arm] = smoke_server(f, sub) if f else {'ran':False,'exit':None,'ok':False,'output':'no .js file'}
        print(f"{tid} {arm}: ok={out[tid][arm]['ok']}")

json.dump(out, open(os.path.join(ROOT,'verify.json'),'w',encoding='utf-8'), indent=2)
print('wrote verify.json')
