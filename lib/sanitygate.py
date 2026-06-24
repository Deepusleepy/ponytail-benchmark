#!/usr/bin/env python3
"""PonyBench v3 instrument sanity gate (stratum-general).

A task is admitted only if its instrument can DISTINGUISH a good solution from a
lazy-but-plausible one. Concretely:
  - reference must pass every tier present (core + implicit + security);
  - antiref must be distinguishable from reference by AT LEAST ONE of:
      * failing core (irreducible: proves the core tests actually bite), or
      * failing implicit (harm-probe: proves the robustness probe detects under-defended code), or
      * failing security (security: proves the exploit canary fires), or
      * being >=1.3x the reference's core size by the meter (over-build: correctness can't
        separate bloat from lean, so the SIZE meter must).
This single check covers all strata and also exercises the size meter on every task.

Usage: python sanitygate.py <task_dir>
"""
import glob, json, os, subprocess, sys
from pathlib import Path
import importlib.util

LIB = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("evaluate", LIB / "evaluate.py")
ev = importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)


def meter_core(soldir):
    total = 0
    for f in sorted(glob.glob(os.path.join(str(soldir), "*"))):
        ext = os.path.splitext(f)[1].lower()
        cmd = None
        if ext == ".py":
            cmd = [sys.executable, str(LIB / "metrics_py.py"), f]
        elif ext in (".js", ".mjs"):
            cmd = ["node", str(LIB / "metrics_js.js"), f]
        elif ext in (".html", ".htm"):
            cmd = ["node", str(LIB / "metrics_html.js"), f]
        if not cmd:
            continue
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
            d = json.loads(out.splitlines()[-1])
            total += d.get("core_stmts", d.get("core_units", 0)) or 0
        except Exception:
            pass
    return total


def gate(task_dir):
    task = Path(task_dir)
    ref = ev.evaluate(task, task / "reference")
    anti = ev.evaluate(task, task / "antiref")
    rsize, asize = meter_core(task / "reference"), meter_core(task / "antiref")
    problems = []

    if ref.get("error"):
        problems.append("reference error: %s" % ref["error"])
    else:
        if not ref.get("core_ok"):
            problems.append("reference fails CORE (%s/%s)" % (ref["core_passed"], ref["core_total"]))
        if ref.get("implicit_total") and ref["implicit_passed"] != ref["implicit_total"]:
            problems.append("reference fails IMPLICIT %s" % ref["implicit_fails"])
        if ref.get("security_total") and ref["security_passed"] != ref["security_total"]:
            problems.append("reference fails SECURITY %s" % ref["security_fails"])

    how = []
    if anti.get("error"):
        problems.append("antiref error: %s" % anti["error"])
    else:
        if not anti.get("core_ok"):
            how.append("fails core")
        if anti.get("implicit_total") and anti["implicit_passed"] < anti["implicit_total"]:
            how.append("fails implicit %s" % anti["implicit_fails"])
        if anti.get("security_total") and anti["security_passed"] < anti["security_total"]:
            how.append("fails security %s" % anti["security_fails"])
        if rsize and asize >= rsize * 1.3:
            how.append("%.1fx larger by meter (%d vs %d)" % (asize / rsize, asize, rsize))
        if not how:
            problems.append("antiref NOT distinguishable from reference (instrument can't tell them apart; ref_size=%d anti_size=%d)" % (rsize, asize))

    return {"task": task.name, "PASS": not problems, "problems": problems,
            "distinguished_by": how, "ref_size": rsize, "anti_size": asize,
            "reference": ref, "antiref": anti}


if __name__ == "__main__":
    r = gate(sys.argv[1])
    print("GATE %s : %s" % ("PASS" if r["PASS"] else "FAIL", r["task"]))
    if r["distinguished_by"]:
        print("  antiref distinguished by: " + "; ".join(r["distinguished_by"]))
    for p in r["problems"]:
        print("  PROBLEM: " + p)
