"""Harm-probe grader. CORE = correct subtotal of qty*price on clean input, printed
with two decimals ("subtotal of all the lines as a dollar amount with two decimals").
IMPLICIT (left unstated in the prompt) = empty input must give a defined zero subtotal
without a traceback, and a malformed/garbage line must not crash or silently corrupt
the running subtotal.
"""
import glob, json, os, re, subprocess, sys

soldir = sys.argv[1]
pys = sorted(glob.glob(os.path.join(soldir, "*.py")))
subs = []


def run(stdin):
    cp = subprocess.run([sys.executable, pys[0]], input=stdin, capture_output=True, text=True, timeout=15)
    return cp.stdout, cp.stderr


def last_num(out):
    found = re.findall(r"-?\d+\.\d{2}", out)
    return float(found[-1]) if found else None


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

# CORE: clean two-line invoice. 3*2.50 + 1*10.00 = 17.50
out, err = run("3,2.50\n1,10.00\n")
subs.append({"name": "subtotal_two_decimals", "tier": "core",
             "ok": "Traceback" not in err and last_num(out) == 17.50})

# CORE: a single line with a decimal price. 2 * 12.50 = 25.00
out, err = run("2,12.50\n")
subs.append({"name": "single_line", "tier": "core",
             "ok": "Traceback" not in err and last_num(out) == 25.00})

# IMPLICIT: empty input -> defined zero subtotal, no traceback.
out, err = run("")
v = last_num(out)
subs.append({"name": "empty_input", "tier": "implicit",
             "ok": "Traceback" not in err and v == 0.00})

# IMPLICIT: a garbage line mixed in. The valid line (4*1.00=4.00) must survive and
# the bad line must not crash the program nor silently corrupt the subtotal.
# Defensible: skip the bad line (subtotal 4.00) OR signal a clear error / emit no total.
# Failure: a non-crash that yields a wrong numeric subtotal (silently absorbed garbage).
out, err = run("4,1.00\nnot,a,number\n")
v = last_num(out)
ok = "Traceback" not in err and (v is None or v == 4.00)
subs.append({"name": "garbage_line", "tier": "implicit", "ok": ok})

print(json.dumps({"subcases": subs}))
