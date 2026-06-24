#!/usr/bin/env python3
"""PonyBench v3 size meter (Python). Counts LOGICAL STATEMENTS (ast.stmt nodes),
split into core (the deliverable) vs selfcheck (a self-test the model added), plus
comment lines, imports, and a total AST-node count (the anti-golf companion).

Design goal: ARM-NEUTRAL bucketing. The skill arms add self-tests far more than the
baseline, so a self-test mis-bucketed into core biases the result. Detection is
STRUCTURAL, never name-only or assert-count-only (both proved too blunt in review):

A self-test region is:
  1. the top-level `if __name__ == '__main__'` block;
  2. any top-level `assert` statement (module level);
  3. a top-level function that is test-SHAPED, i.e. ANY of:
       - raises AssertionError or SystemExit, or
       - has a strong test name (test/selfcheck/selftest/smoke/sanity/demo); or
       - has >=1 "test assert" (an assert comparing a CALL result to an expected
         value, e.g. `assert f(x) == 2`) AND returns no value; or
       - has an assert-method call (self.assertEqual / assert(...) / expect(...))
         AND returns no value; or
       - is referenced inside the __main__ block AND its body asserts / raises
         SystemExit / prints a pass-fail literal;
  4. a top-level class that is test-shaped (name ~ Test*, subclasses *TestCase, or
     >=2 of its methods are test-ish).

We deliberately do NOT flag on: a bare name match alone (verify/check are real
deliverable verbs), ">=2 asserts" alone (validators use defensive asserts),
or "only called from __main__" (the real deliverable is naturally only called by its
own test). Each of those caused a confirmed false-positive in review.

Usage: python metrics_py.py <file.py>   -> prints JSON
"""
import ast, json, re, sys

STRONG_NAME = re.compile(r'(test|selfcheck|selftest|smoke|sanity|demo)(_.*)?$', re.I)
PASSFAIL = re.compile(r'\b(fail|pass|passed|failed|ok|error|assert)', re.I)


def _is_str_const(n):
    return isinstance(n, ast.Constant) and isinstance(n.value, str)


def _docstring_exprs(tree):
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = node.body[0] if node.body else None
            if isinstance(b, ast.Expr) and _is_str_const(getattr(b, 'value', None)):
                out.add(id(b))
    return out


def _docstring_ranges(tree):
    rng = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = node.body[0] if node.body else None
            if isinstance(b, ast.Expr) and _is_str_const(getattr(b, 'value', None)):
                rng.append((b.lineno, getattr(b, 'end_lineno', b.lineno)))
    return rng


def _has_call(node):
    return any(isinstance(x, ast.Call) for x in ast.walk(node))


def _is_test_assert(a):
    # assert whose condition compares a CALL result to something (test), not a bare
    # condition on a parameter (defensive). `assert f(x) == 2` -> True; `assert n>0` -> False.
    if not isinstance(a, ast.Assert):
        return False
    t = a.test
    if isinstance(t, ast.Compare):
        return _has_call(t.left) or any(_has_call(c) for c in t.comparators)
    return False


def _assert_call(node):
    # self.assertEqual(...) / assert(...) / expect(...) calls
    for x in ast.walk(node):
        if isinstance(x, ast.Call):
            f = x.func
            if isinstance(f, ast.Name) and f.id in ('assert', 'expect'):
                return True
            if isinstance(f, ast.Attribute) and (f.attr.startswith('assert') or f.attr in ('expect', 'fail')):
                return True
    return False


def _raises_ae_se(node):
    for x in ast.walk(node):
        if isinstance(x, ast.Raise) and x.exc is not None:
            e = x.exc
            nm = None
            if isinstance(e, ast.Call) and isinstance(getattr(e, 'func', None), ast.Name):
                nm = e.func.id
            elif isinstance(e, ast.Name):
                nm = e.id
            if nm in ('AssertionError', 'SystemExit'):
                return True
    return False


def _no_value_return(fn):
    return not any(isinstance(x, ast.Return) and x.value is not None for x in ast.walk(fn))


def _prints_passfail(fn):
    for x in ast.walk(fn):
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'print':
            for a in x.args:
                if _is_str_const(a) and PASSFAIL.search(a.value):
                    return True
    return False


def _func_is_selftest(fn, main_region):
    body_assert = any(isinstance(x, ast.Assert) for x in ast.walk(fn))
    test_assert = any(_is_test_assert(x) for x in ast.walk(fn))
    acall = _assert_call(fn)
    raises = _raises_ae_se(fn)
    novalue = _no_value_return(fn)
    strong = bool(STRONG_NAME.match(fn.name))
    span = (fn.lineno, fn.end_lineno or fn.lineno)
    referenced_in_main = False
    if main_region:
        # is the function name referenced inside the __main__ block?
        pass  # filled by caller via refs
    reasons = []
    if raises:
        reasons.append('raise')
    if strong and (body_assert or acall or raises or test_assert):
        reasons.append('name')
    if (test_assert or acall) and novalue:
        reasons.append('test-shape')
    return reasons, span


def _class_is_selftest(cls):
    name = bool(re.match(r'Test', cls.name)) or STRONG_NAME.match(cls.name)
    base_tc = any((isinstance(b, ast.Attribute) and b.attr.endswith('TestCase')) or
                  (isinstance(b, ast.Name) and b.id.endswith('TestCase')) for b in cls.bases)
    methods = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    testish = sum(1 for m in methods if STRONG_NAME.match(m.name) or m.name.startswith('test')
                  or any(isinstance(x, ast.Assert) for x in ast.walk(m)) or _assert_call(m))
    if name or base_tc or testish >= 2:
        why = 'test-class'
        return [why], (cls.lineno, cls.end_lineno or cls.lineno)
    return [], None


def _selftest_regions(tree):
    regions, reasons = [], []
    main_region = None
    for node in tree.body:
        if isinstance(node, ast.If):
            try:
                t = ast.dump(node.test)
            except Exception:
                t = ''
            if '__name__' in t and '__main__' in t:
                main_region = (node.lineno, node.end_lineno or node.lineno)
                regions.append(main_region); reasons.append('__main__')
        if isinstance(node, ast.Assert):  # top-level assert
            regions.append((node.lineno, node.end_lineno or node.lineno)); reasons.append('top-assert')

    funcs = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def in_main(ln):
        return main_region is not None and main_region[0] <= ln <= main_region[1]

    refs = {n: [] for n in funcs}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in funcs:
            refs[node.id].append(node.lineno)

    for name, fn in funcs.items():
        why, span = _func_is_selftest(fn, main_region)
        # extra rule: referenced from __main__ AND has assert/SystemExit/passfail-print
        ref_in_main = any(in_main(ln) for ln in refs[name] if not (span[0] <= ln <= span[1]))
        if ref_in_main and (any(isinstance(x, ast.Assert) for x in ast.walk(fn))
                            or _assert_call(fn) or _raises_ae_se(fn) or _prints_passfail(fn)):
            if 'main-ref' not in why:
                why.append('main-ref')
        if why:
            regions.append(span); reasons.append('func:%s(%s)' % (name, '+'.join(why)))

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            why, span = _class_is_selftest(node)
            if why:
                regions.append(span); reasons.append('class:%s' % node.name)
    return regions, reasons


def _merge(regs):
    if not regs:
        return []
    regs = sorted(regs)
    out = [list(regs[0])]
    for a, b in regs[1:]:
        if a <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [tuple(x) for x in out]


def py_metrics(text):
    lines = text.splitlines()
    nonblank = sum(1 for l in lines if l.strip())
    tree = ast.parse(text)
    doc_ids = _docstring_exprs(tree)
    regions, reasons = _selftest_regions(tree)

    def in_self(ln):
        return any(a <= ln <= b for a, b in regions)

    comment_lines = set(i for i, l in enumerate(lines, 1) if l.strip().startswith('#'))
    for a, b in _docstring_ranges(tree):
        comment_lines.update(range(a, b + 1))

    core = sc = imports = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt) and id(node) not in doc_ids:
            ln = getattr(node, 'lineno', None)
            if ln is None:
                continue
            if in_self(ln):
                sc += 1
            else:
                core += 1
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports += 1
    return {
        'lang': 'py',
        'core_stmts': core,
        'core_nonimport_stmts': core - imports,
        'import_stmts': imports,
        'selfcheck_stmts': sc,
        'total_stmts': core + sc,
        'ast_nodes': sum(1 for _ in ast.walk(tree)) - 1,
        'comment_lines': len(comment_lines),
        'nonblank_lines': nonblank,
        'selfcheck_line_span': sum(b - a + 1 for a, b in _merge(regions)),
        'selfcheck_reasons': reasons,
    }


if __name__ == '__main__':
    src = open(sys.argv[1], encoding='utf-8', errors='replace').read()
    try:
        print(json.dumps(py_metrics(src)))
    except SyntaxError as e:
        print(json.dumps({'error': 'syntax: %s' % e}))
