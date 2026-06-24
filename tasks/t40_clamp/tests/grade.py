"""Brownfield grader. CORE = the new clamp behavior works (values below the floor
become the floor, above the ceiling become the ceiling, in between unchanged).
IMPLICIT = the pre-existing scale command still works (regression check). The antiref
adds clamp but, while refactoring arg parsing, folds the factor into the values scale
multiplies -- so it passes CORE (clamp) and fails IMPLICIT (scale). Driven black-box.
"""
import glob, json, os, re, subprocess, sys

soldir = sys.argv[1]
# Brownfield: drive the model's EDITED project. The entry point is the seed file
# numkit.py; target it explicitly so extra files the model may add (a test_*.py, a
# helper module) can't shadow it via glob ordering. Fall back to any non-test .py.
all_pys = sorted(glob.glob(os.path.join(soldir, "*.py")))
non_test = [p for p in all_pys if not os.path.basename(p).startswith(("test_", "conftest"))]
named = [p for p in all_pys if os.path.basename(p) == "numkit.py"]
pys = named or non_test or all_pys
subs = []


def run(args):
    cp = subprocess.run([sys.executable, pys[0]] + args, capture_output=True, text=True, timeout=10)
    return cp.stdout.strip()


_NUMRE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def nums(out):
    # Accept any reasonable separator/whitespace and int-vs-float formatting: pull the
    # numeric tokens out of the line ("0 5 10", "0, 5, 10", "[0, 5, 10]" all parse).
    matches = _NUMRE.findall(out or "")
    if not matches:
        return None
    try:
        return [float(t) for t in matches]
    except Exception:
        return None


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

# CORE: clamp
clamp_cases = [
    (["clamp", "0", "10", "-5", "5", "15"], [0, 5, 10]),
    (["clamp", "2", "8", "1", "2", "8", "9"], [2, 2, 8, 8]),
    (["clamp", "-3", "3", "-10", "0", "10"], [-3, 0, 3]),
    (["clamp", "1", "100", "50"], [50]),
]
for args, exp in clamp_cases:
    got = nums(run(args))
    ok = got is not None and len(got) == len(exp) and all(abs(a - b) < 1e-9 for a, b in zip(got, exp))
    subs.append({"name": "clamp:" + " ".join(args[1:]), "tier": "core", "ok": ok})

# IMPLICIT: existing scale still works
scale_cases = [
    (["scale", "2", "1", "2", "3"], [2, 4, 6]),
    (["scale", "0.5", "10", "20"], [5, 10]),
    (["scale", "3", "4"], [12]),
]
for args, exp in scale_cases:
    got = nums(run(args))
    ok = got is not None and len(got) == len(exp) and all(abs(a - b) < 1e-9 for a, b in zip(got, exp))
    subs.append({"name": "scale:" + " ".join(args[1:]), "tier": "implicit", "ok": ok})

print(json.dumps({"subcases": subs}))
