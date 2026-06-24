#!/usr/bin/env python3
"""PonyBench v3 orchestrator. Runs every (task, condition, rep) cell via run_one.py,
with a few parallel workers (each cell has its own isolated config dir, so parallel is
safe). Idempotent: a cell with a valid result.json (real output) is skipped, so a
crashed/interrupted run resumes where it left off.

Usage:
  python run_all.py [--reps 5] [--workers 3] [--conds baseline,lite,full,ultra]
                    [--tasks t01,t10,...] [--out runs] [--dry-run]
"""
import argparse, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

LIB = Path(__file__).resolve().parent
ROOT = LIB.parent
ALL_CONDS = ["baseline", "lite", "full", "ultra"]


def all_tasks():
    return sorted(d.name for d in (ROOT / "tasks").iterdir()
                  if d.is_dir() and d.name.startswith("t") and (d / "meta.json").exists())


def cell_already_done(out):
    rj = Path(out) / "result.json"
    if not rj.exists():
        return False
    try:
        d = json.load(open(rj, encoding="utf-8"))
        return d.get("status") == "ok" and bool(d.get("out_tok"))  # real run with output
    except Exception:
        return False


def run_cell(task, cond, rep, outroot, dry):
    out = os.path.join(outroot, task, cond, "r%d" % rep)
    if cell_already_done(out):
        return (task, cond, rep, "skip")
    cmd = ["python", str(LIB / "run_one.py"), "--task", str(ROOT / "tasks" / task),
           "--cond", cond, "--rep", str(rep), "--out", out]
    if dry:
        cmd.append("--dry-run")
    cp = subprocess.run(cmd, capture_output=True, text=True)
    status = "ran" if cp.returncode == 0 else "ERR"
    return (task, cond, rep, status)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--conds", default=",".join(ALL_CONDS))
    ap.add_argument("--tasks", default="")
    ap.add_argument("--out", default=str(ROOT / "runs"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    tasks = [t.strip() for t in a.tasks.split(",") if t.strip()] or all_tasks()
    conds = [c.strip() for c in a.conds.split(",") if c.strip()]
    cells = [(t, c, r) for t in tasks for c in conds for r in range(1, a.reps + 1)]
    print("Tasks: %d | conds: %s | reps: %d | total cells: %d | workers: %d"
          % (len(tasks), conds, a.reps, len(cells), a.workers))
    if a.dry_run:
        print("[dry-run: not executing]")

    done = ran = err = skip = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(run_cell, t, c, r, a.out, a.dry_run) for (t, c, r) in cells]
        for f in as_completed(futs):
            t, c, r, st = f.result()
            done += 1
            if st == "ran":
                ran += 1
            elif st == "skip":
                skip += 1
            elif st == "ERR":
                err += 1
                print("  ERR: %s/%s/r%d" % (t, c, r))
            if done % 20 == 0 or done == len(cells):
                print("  progress %d/%d (ran=%d skip=%d err=%d)" % (done, len(cells), ran, skip, err))
    print("RUN_ALL COMPLETE: ran=%d skip=%d err=%d of %d" % (ran, skip, err, len(cells)))


if __name__ == "__main__":
    main()
