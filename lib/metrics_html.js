#!/usr/bin/env node
/* PonyBench v3 size meter (HTML/CSS) -- real parsers, no regex.
 * HTML has no "statements", so the structural size unit is:
 *   - DOM element count (node-html-parser)        -- the markup
 *   - CSS rule + declaration count (postcss)      -- the styling
 *   - embedded <script> statements via the JS meter (lib/metrics_js.meterSource)
 * core_units = html_elements + css_rules + css_decls + js_core ; selfcheck_units = js_selfcheck.
 * Comments come from each real parser (HTML <!-- -->, CSS /* *​/, JS //). Self-test only
 * exists if an embedded <script> is itself a test harness (the JS meter flags it).
 *
 * Usage: node metrics_html.js <file.html>  -> prints JSON
 */
const fs = require('fs');
const { parse } = require('node-html-parser');
const postcss = require('postcss');
const safe = require('postcss-safe-parser');
const { meterSource } = require('./metrics_js');

function countComments(node, acc) {
  // node-html-parser: nodeType 8 = comment
  if (node.nodeType === 8) {
    acc.lines += (node.rawText || '').split('\n').length;
    return;
  }
  for (const c of node.childNodes || []) countComments(c, acc);
}

function cssStats(cssText) {
  let rules = 0, decls = 0, comments = 0;
  try {
    const root = postcss().process(cssText, { parser: safe, from: undefined }).root;
    root.walkRules(() => rules++);
    root.walkDecls(() => decls++);
    root.walkComments(() => comments++);
  } catch (e) { /* leave zeros */ }
  return { rules, decls, comments };
}

function main() {
  const src = fs.readFileSync(process.argv[2], 'utf8');
  const root = parse(src, { comment: true, blockTextElements: { script: true, style: true } });

  const elements = root.querySelectorAll('*').length;

  let css = { rules: 0, decls: 0, comments: 0 };
  for (const st of root.querySelectorAll('style')) {
    const s = cssStats(st.rawText || st.text || '');
    css.rules += s.rules; css.decls += s.decls; css.comments += s.comments;
  }

  let jsCore = 0, jsSelf = 0, jsComments = 0;
  const jsReasons = [];
  for (const sc of root.querySelectorAll('script')) {
    if (sc.getAttribute('src')) continue; // external script, no body to measure
    const code = sc.rawText || sc.text || '';
    if (!code.trim()) continue;
    const m = meterSource(code);
    if (m.error) continue;
    jsCore += m.core_stmts; jsSelf += m.selfcheck_stmts; jsComments += m.comment_lines;
    if (m.selfcheck_reasons && m.selfcheck_reasons.length) jsReasons.push(...m.selfcheck_reasons);
  }

  const htmlComments = { lines: 0 };
  countComments(root, htmlComments);

  const nonblank = src.split('\n').filter((l) => l.trim()).length;
  const core_units = elements + css.rules + css.decls + jsCore;
  console.log(JSON.stringify({
    lang: 'html',
    core_units, selfcheck_units: jsSelf,
    html_elements: elements, css_rules: css.rules, css_decls: css.decls,
    js_core_stmts: jsCore, js_selfcheck_stmts: jsSelf,
    comment_lines: htmlComments.lines + css.comments + jsComments,
    nonblank_lines: nonblank,
    selfcheck_reasons: jsReasons,
  }));
}
main();
