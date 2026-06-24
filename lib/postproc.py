#!/usr/bin/env python3
"""Turn a runs/ tree into the records aggregate.py consumes. No API calls -- pure
post-processing: for each cell, meter the produced solution (by file extension) and
grade it, then emit one record. Idempotent and re-runnable (offline rescore).

record = {task, cond, rep, out_tok, size, done, implicit_ok, security_ok, activated}

Usage: python postproc.py <runs_dir> <out_records.json> [tasks_dir]
"""
import glob, json, os, subprocess, sys
from pathlib import Path

LIB = Path(__file__).resolve().parent


def meter_file(path):
    ext = Path(path).suffix.lower()
    if ext == ".py":
        cmd = ["python", str(LIB / "metrics_py.py"), path]
    elif ext in (".js", ".mjs"):
        cmd = ["node", str(LIB / "metrics_js.js"), path]
    elif ext in (".html", ".htm"):
        cmd = ["node", str(LIB / "metrics_html.js"), path]
    else:
        return 0
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
        d = json.loads(out.splitlines()[-1])
        return d.get("core_stmts", d.get("core_units", 0)) or 0
    except Exception:
        return 0


def build_records(runs_dir, tasks_dir="tasks"):
    recs = []
    for rj in glob.glob(os.path.join(runs_dir, "*", "*", "*", "result.json")):
        try:
            d = json.load(open(rj, encoding="utf-8"))
        except Exception:
            continue
        task, cond, rep = d.get("task"), d.get("cond"), d.get("rep")
        soldir = os.path.join(os.path.dirname(rj), "solution")
        size = sum(meter_file(f) for f in glob.glob(os.path.join(soldir, "*")) if os.path.isfile(f))
        ev = {}
        try:
            ev = json.loads(subprocess.run(["python", str(LIB / "evaluate.py"), os.path.join(tasks_dir, task), soldir],
                                           capture_output=True, text=True, timeout=180).stdout or "{}")
        except Exception:
            pass
        def tier_ok(p, t):
            return ev.get(t, 0) == 0 or ev.get(p) == ev.get(t)
        recs.append({
            "task": task, "cond": cond, "rep": rep,
            "out_tok": d.get("out_tok"), "size": size,
            "done": bool(ev.get("core_ok")),
            "implicit_ok": tier_ok("implicit_passed", "implicit_total"),
            "security_ok": tier_ok("security_passed", "security_total"),
            "activated": d.get("activated"),
            "cost_usd": d.get("cost_usd"),
            "cache_read_tok": d.get("cache_read_tok"), "cache_creation_tok": d.get("cache_creation_tok"),
            "in_tok": d.get("in_tok"),
        })
    return recs


if __name__ == "__main__":
    recs = build_records(sys.argv[1], sys.argv[3] if len(sys.argv) > 3 else "tasks")
    os.makedirs(os.path.dirname(sys.argv[2]) or ".", exist_ok=True)
    json.dump(recs, open(sys.argv[2], "w", encoding="utf-8"), indent=2)
    print("wrote %d records to %s" % (len(recs), sys.argv[2]))
