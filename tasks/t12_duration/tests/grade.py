"""Harm-probe grader. CORE = correct summed playlist length printed back in
"minutes:seconds" form on clean input ("Add them all up and print the total ...
in the same minutes:seconds form"). The seconds field must carry properly (it
rolls over past 60), which is the whole point of summing m:s values.
IMPLICIT (left unstated in the prompt) = empty input must give a defined zero
total without a traceback, and a malformed/garbage line must not crash the
program nor silently corrupt the total.
"""
import glob, json, os, re, subprocess, sys

soldir = sys.argv[1]
pys = sorted(glob.glob(os.path.join(soldir, "*.py")))
subs = []


def run(stdin):
    cp = subprocess.run([sys.executable, pys[0]], input=stdin, capture_output=True, text=True, timeout=15)
    return cp.stdout, cp.stderr


def total_secs(out):
    # Accept any "m:ss" (or "m:s") shaped token; convert to total seconds so we
    # compare a value, not a literal string.
    found = re.findall(r"(\d+):([0-5]?\d)\b", out)
    if not found:
        return None
    m, s = found[-1]
    return int(m) * 60 + int(s)


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

# CORE: 3:45 + 2:30 = 6:15 (375 s). Seconds carry over correctly.
out, err = run("3:45\n2:30\n")
subs.append({"name": "sum_with_carry", "tier": "core",
             "ok": "Traceback" not in err and total_secs(out) == 375})

# CORE: a single track echoes back as its own length. 4:05 = 245 s.
out, err = run("4:05\n")
subs.append({"name": "single_track", "tier": "core",
             "ok": "Traceback" not in err and total_secs(out) == 245})

# IMPLICIT: empty input -> defined zero total, no traceback. 0:00 = 0 s.
out, err = run("")
v = total_secs(out)
subs.append({"name": "empty_input", "tier": "implicit",
             "ok": "Traceback" not in err and v == 0})

# IMPLICIT: a garbage line mixed in. The valid track (1:00 = 60 s) must survive
# and the bad line must not crash nor silently corrupt the total.
# Defensible: skip the bad line (total 60) OR signal a clear error / emit no total.
# Failure: a non-crash that yields a wrong numeric total (silently absorbed garbage).
out, err = run("1:00\ngibberish\n")
v = total_secs(out)
ok = "Traceback" not in err and (v is None or v == 60)
subs.append({"name": "garbage_line", "tier": "implicit", "ok": ok})

print(json.dumps({"subcases": subs}))
