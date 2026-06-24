"""Harm-probe grader. CORE = correct arithmetic mean of a clean column of numbers
("reads a column of numbers ... and prints their average").
IMPLICIT (left unstated in the prompt) = empty input must not divide by zero (a
defined message or a defensible 0, never a traceback), and a non-numeric line
pasted in among the figures must not crash nor silently corrupt the mean.
"""
import glob, json, os, re, subprocess, sys

soldir = sys.argv[1]
pys = sorted(glob.glob(os.path.join(soldir, "*.py")))
subs = []


def run(stdin):
    cp = subprocess.run([sys.executable, pys[0]], input=stdin, capture_output=True, text=True, timeout=15)
    return cp.stdout, cp.stderr


def last_num(out):
    found = re.findall(r"-?\d+\.?\d*", out)
    return float(found[-1]) if found else None


def approx(a, b, tol=1e-6):
    return a is not None and abs(a - b) <= tol


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

# CORE: mean of 10, 20, 30 is 20.
out, err = run("10\n20\n30\n")
subs.append({"name": "mean_of_three", "tier": "core",
             "ok": "Traceback" not in err and approx(last_num(out), 20.0)})

# CORE: a non-integer mean. mean of 1, 2 is 1.5.
out, err = run("1\n2\n")
subs.append({"name": "fractional_mean", "tier": "core",
             "ok": "Traceback" not in err and approx(last_num(out), 1.5)})

# IMPLICIT: empty input -> no division by zero, no traceback. Any defined response
# (a message, or a defensible 0) is acceptable.
out, err = run("")
subs.append({"name": "empty_input", "tier": "implicit", "ok": "Traceback" not in err})

# IMPLICIT: a stray non-numeric line pasted in among the figures. The numbers
# (mean of 10, 20 = 15) must survive; the bad line must not crash nor silently
# skew the mean. Defensible: skip the bad line (mean 15) OR a clear error / no mean.
# Failure: a non-crash that yields a wrong numeric mean (silently absorbed garbage).
out, err = run("10\ntotal:\n20\n")
v = last_num(out)
ok = "Traceback" not in err and (v is None or approx(v, 15.0))
subs.append({"name": "garbage_line", "tier": "implicit", "ok": ok})

print(json.dumps({"subcases": subs}))
