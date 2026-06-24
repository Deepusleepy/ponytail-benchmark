"""Smoke-task grader: drives the produced script black-box (subprocess, free filename).
core   = adds two integers (the stated goal)
implicit = bad input is handled gracefully (no raw traceback) -- unstated but implied
"""
import glob, json, os, subprocess, sys

soldir = sys.argv[1]
pys = sorted(glob.glob(os.path.join(soldir, "*.py")))
subs = []


def num_eq(out, want):
    try:
        return abs(float(out.strip().split()[-1]) - want) < 1e-9
    except Exception:
        return False


def run(args):
    try:
        cp = subprocess.run([sys.executable, pys[0]] + args, capture_output=True, text=True, timeout=10)
        return cp.returncode, cp.stdout.strip(), cp.stderr
    except Exception as e:
        return -1, "", str(e)


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_a_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

rc, out, err = run(["2", "3"])
subs.append({"name": "adds", "tier": "core", "ok": num_eq(out, 5)})
rc, out, err = run(["-4", "10"])
subs.append({"name": "adds_negative", "tier": "core", "ok": num_eq(out, 6)})
rc, out, err = run(["2", "x"])  # bad input: implied to be handled, never stated
subs.append({"name": "bad_input_graceful", "tier": "implicit", "ok": "Traceback" not in err})

print(json.dumps({"subcases": subs}))
