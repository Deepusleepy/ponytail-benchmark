#!/usr/bin/env node
/* PonyBench v3 size meter (JavaScript) -- mirrors lib/metrics_py.py definitions.
 * Counts logical statements (real acorn AST, not lines), split into core vs selfcheck,
 * plus comment lines, imports, and a total node count (anti-golf companion).
 *
 * Self-test detection is STRUCTURAL, mirroring the Python rules (no name-only flagging):
 *   1. `if (require.main === module) { ... }` block (the JS analog of `if __name__==...`);
 *   2. top-level test-runner calls: describe(...) / it(...) / test(...) / suite(...);
 *   3. a top-level function (decl, or const fn = ()=>{}) that is test-SHAPED:
 *        - has an assert-ish call (assert(...), assert.x(...), expect(...), .toBe/.toEqual/
 *          .deepEqual/.strictEqual/.equal/.ok) AND returns no value; or
 *        - has a strong test name (test/selfcheck/selftest/smoke/sanity/demo) AND asserts.
 * We do NOT flag on a bare name (verify/check are real deliverable verbs) or on
 * "only called from the main block" (false-flags the deliverable).
 *
 * Usage: node metrics_js.js <file.js>   -> prints JSON (same shape as metrics_py)
 */
const fs = require('fs');
const acorn = require('acorn');
const walk = require('acorn-walk');

const STRONG = /^(test|selfcheck|selftest|smoke|sanity|demo)(_|$)/i;
const ASSERT_PROPS = new Set(['tobe', 'toequal', 'tobetruthy', 'tobefalsy', 'deepequal', 'strictequal', 'equal', 'notequal', 'ok', 'fail', 'throws']);

function tryParse(src) {
  const comments = [];
  for (const st of ['script', 'module']) {
    try {
      const ast = acorn.parse(src, {
        ecmaVersion: 'latest', sourceType: st, locations: true,
        allowReturnOutsideFunction: true, allowAwaitOutsideFunction: true,
        allowHashBang: true, onComment: comments,
      });
      return { ast, comments, mode: st };
    } catch (e) { comments.length = 0; }
  }
  return null;
}

function isStmt(t) {
  return (t.endsWith('Statement') && t !== 'BlockStatement' && t !== 'EmptyStatement')
    || t === 'VariableDeclaration' || t === 'FunctionDeclaration' || t === 'ClassDeclaration';
}

function isAssertCall(node) {
  let found = false;
  walk.full(node, (n) => {
    if (n.type !== 'CallExpression') return;
    const c = n.callee;
    if (c.type === 'Identifier' && (c.name === 'assert' || c.name === 'expect')) found = true;
    if (c.type === 'MemberExpression') {
      const obj = c.object, prop = c.property;
      if (obj.type === 'Identifier' && (obj.name === 'assert' || obj.name === 'expect')) found = true;
      if (prop && prop.type === 'Identifier' && ASSERT_PROPS.has(prop.name.toLowerCase())) found = true;
    }
  });
  return found;
}

function noValueReturn(fnBody) {
  let bad = false;
  walk.full(fnBody, (n) => { if (n.type === 'ReturnStatement' && n.argument) bad = true; });
  return !bad;
}

function fnInfo(name, bodyNode) {
  const acall = isAssertCall(bodyNode);
  const novalue = noValueReturn(bodyNode);
  const strong = STRONG.test(name || '');
  const why = [];
  if (acall && novalue) why.push('test-shape');
  if (strong && acall) why.push('name');
  return why;
}

function selftestRegions(ast) {
  const regions = [], reasons = [];
  for (const node of ast.body) {
    // require.main === module
    if (node.type === 'IfStatement' && node.test.type === 'BinaryExpression') {
      const src = JSON.stringify(node.test);
      if (src.includes('"main"') && src.includes('"module"') && src.includes('require')) {
        regions.push([node.loc.start.line, node.loc.end.line]); reasons.push('require.main');
      }
    }
    // top-level test-runner call: describe()/it()/test()/suite()
    if (node.type === 'ExpressionStatement' && node.expression.type === 'CallExpression') {
      const c = node.expression.callee;
      if (c.type === 'Identifier' && ['describe', 'it', 'test', 'suite'].includes(c.name)) {
        regions.push([node.loc.start.line, node.loc.end.line]); reasons.push('runner:' + c.name);
      }
    }
    // function declaration
    if (node.type === 'FunctionDeclaration') {
      const why = fnInfo(node.id && node.id.name, node.body);
      if (why.length) { regions.push([node.loc.start.line, node.loc.end.line]); reasons.push('fn:' + (node.id && node.id.name) + '(' + why.join('+') + ')'); }
    }
    // const fn = () => {} / function expr
    if (node.type === 'VariableDeclaration') {
      for (const d of node.declarations) {
        if (d.init && (d.init.type === 'ArrowFunctionExpression' || d.init.type === 'FunctionExpression')) {
          const why = fnInfo(d.id && d.id.name, d.init.body);
          if (why.length) { regions.push([node.loc.start.line, node.loc.end.line]); reasons.push('fn:' + (d.id && d.id.name) + '(' + why.join('+') + ')'); }
        }
      }
    }
  }
  return { regions, reasons };
}

function inRegions(line, regions) { return regions.some(([a, b]) => a <= line && line <= b); }

function meterSource(src) {
  const parsed = tryParse(src);
  if (!parsed) { return { error: 'parse failed' }; }
  const { ast, comments } = parsed;
  const { regions, reasons } = selftestRegions(ast);

  const commentLines = new Set();
  for (const c of comments) for (let l = c.loc.start.line; l <= c.loc.end.line; l++) commentLines.add(l);

  let core = 0, sc = 0, imports = 0, nodes = 0;
  walk.full(ast, (n) => {
    nodes++;
    if (isStmt(n.type)) {
      const line = n.loc.start.line;
      if (inRegions(line, regions)) sc++;
      else {
        core++;
        if (n.type === 'ImportDeclaration') imports++;
        if (n.type === 'VariableDeclaration') {
          const isReq = JSON.stringify(n).includes('"name":"require"');
          if (isReq) imports++;
        }
      }
    }
  });
  const nonblank = src.split('\n').filter((l) => l.trim()).length;
  return {
    lang: 'js', core_stmts: core, core_nonimport_stmts: core - imports, import_stmts: imports,
    selfcheck_stmts: sc, total_stmts: core + sc, ast_nodes: nodes,
    comment_lines: commentLines.size, nonblank_lines: nonblank,
    selfcheck_reasons: reasons, parse_mode: parsed.mode,
  };
}

if (require.main === module) {
  console.log(JSON.stringify(meterSource(fs.readFileSync(process.argv[2], 'utf8'))));
}
module.exports = { meterSource };
