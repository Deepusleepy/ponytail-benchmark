#!/usr/bin/env python3
"""Snapshot a provenance manifest before a run so the raw data is self-describing and
re-evaluable later: hashes of the harness code, every task (prompt/meta/grader/reference),
and the ponytail skill, plus run config. The raw runs/ tree (run.json + solution/) is the
source of truth; meters/grading/aggregation are all re-derivable offline from it, so a
wrong evaluation can be fixed later with NO re-spend as long as this manifest + runs/ exist.

Usage: python provenance.py [started_iso]
"""
import glob, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
    except Exception:
        return None


def main():
    runs = ROOT / "runs"
    runs.mkdir(exist_ok=True)
    man = {
        "started_iso": sys.argv[1] if len(sys.argv) > 1 else None,
        "started_epoch": int(time.time()),
        "model": "claude-opus-4-8",
        "conds": ["baseline", "lite", "full", "ultra"],
        "reps": 5,
        "note": "raw runs/<task>/<cond>/r<n>/{run.json,solution/} are the source of truth; "
                "rebuild records with postproc.py and re-aggregate any time without re-running models.",
        "lib": {Path(f).name: sha(f) for f in sorted(glob.glob(str(ROOT / "lib" / "*")))
                if Path(f).is_file()},
        "ponytail_skill_md": sha(ROOT.parent / "ponytail" / "skills" / "ponytail" / "SKILL.md"),
        "tasks": {},
    }
    for d in sorted(glob.glob(str(ROOT / "tasks" / "t*"))):
        t = Path(d).name
        man["tasks"][t] = {
            "prompt": sha(Path(d) / "prompt.txt"),
            "meta": sha(Path(d) / "meta.json"),
            "grader": sha(Path(d) / "tests" / "grade.py"),
            "reference": [sha(f) for f in sorted(glob.glob(str(Path(d) / "reference" / "*"))) if Path(f).is_file()],
            "antiref": [sha(f) for f in sorted(glob.glob(str(Path(d) / "antiref" / "*"))) if Path(f).is_file()],
        }
    out = runs / "manifest.json"
    json.dump(man, open(out, "w", encoding="utf-8"), indent=2)
    print("wrote %s: %d tasks, %d lib files, skill=%s" % (out, len(man["tasks"]), len(man["lib"]), man["ponytail_skill_md"]))


if __name__ == "__main__":
    main()
