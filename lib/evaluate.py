#!/usr/bin/env python3
"""PonyBench v3 grader harness. Runs a task's own tests/grade.py against a solution
directory and aggregates the per-subcase results into tier pass-counts.

Contract for a task's tests/grade.py:
  - invoked as: python grade.py <solution_dir>
  - it locates the produced solution (free filename), drives it BLACK-BOX
    (subprocess/import/HTTP/DOM), and prints ONE JSON line:
      {"subcases": [{"name": str, "tier": "core"|"implicit"|"security", "ok": bool}, ...]}
  - core  = behaviors stated in the prompt goal (every arm should pass; anti-stub)
    implicit = unstated-but-implied edge/error cases (robustness, delta_r)
    security = executed adversarial canaries (delta_s)

Usage: python evaluate.py <task_dir> <solution_dir>
"""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path


def evaluate(task_dir, solution_dir, timeout=120):
    task = Path(task_dir); sol = Path(solution_dir)
    grader = task / "tests" / "grade.py"
    if not grader.exists():
        return {"error": "no grader at %s" % grader}
    sand = Path(tempfile.mkdtemp(prefix="pbgrade_"))
    try:
        cp = subprocess.run([sys.executable, str(grader.resolve()), str(sol.resolve())],
                            capture_output=True, text=True, timeout=timeout, cwd=str(sand))
    except subprocess.TimeoutExpired:
        shutil.rmtree(sand, ignore_errors=True)
        return {"error": "grader timeout"}
    shutil.rmtree(sand, ignore_errors=True)
    data = None
    for line in reversed(cp.stdout.strip().splitlines()):
        try:
            data = json.loads(line); break
        except Exception:
            continue
    if data is None:
        return {"error": "grader emitted no JSON", "stderr": cp.stderr[-600:], "stdout": cp.stdout[-600:]}
    subs = data.get("subcases", [])

    def tier(t):
        xs = [s for s in subs if s.get("tier") == t]
        return sum(1 for s in xs if s.get("ok")), len(xs)

    cpas, ctot = tier("core"); ipas, itot = tier("implicit"); spas, stot = tier("security")
    return {
        "core_passed": cpas, "core_total": ctot,
        "implicit_passed": ipas, "implicit_total": itot,
        "security_passed": spas, "security_total": stot,
        "security_fails": [s["name"] for s in subs if s.get("tier") == "security" and not s.get("ok")],
        "implicit_fails": [s["name"] for s in subs if s.get("tier") == "implicit" and not s.get("ok")],
        "core_ok": ctot > 0 and cpas == ctot,
        "done": ctot > 0 and cpas == ctot,  # completeness proxy: passes the stated-goal tier
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(sys.argv[1], sys.argv[2]), indent=2))
