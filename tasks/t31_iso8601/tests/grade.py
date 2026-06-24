"""Irreducible grader. An ISO-8601 duration over W/D/H/M/S has exactly one correct
second-count, so CORE can be near-exhaustive. The antiref (drops weeks, truncates
fractional seconds) fails CORE -- proving the tests bite.

CONTRACT (from the goal sentence): read a duration over weeks/days/hours/minutes/
seconds from stdin and print the total seconds; "the seconds part can be fractional".
CORE therefore covers every unit (incl. weeks, which the prompt lists as a unit and
which it lets combine with the others, e.g. P3W2D) and fractional SECONDS -- the one
fractional case the prompt promises. Output is the single correct number, accepted in
whatever surrounding whitespace/format the model emits (we take the last numeric token
and compare as a float, so "90", "90.0", "= 90", a trailing newline all pass).

Fractional NON-second units (PT1.5H, P1.5D) are a reasonable extension but the goal
only promises fractional seconds, so a correct reading may treat them as out of scope;
they live in the IMPLICIT tier (an unstated-but-implied nicety), not CORE -- otherwise
CORE would fail a competent literal reading of the prompt.
"""
import glob, json, os, re, subprocess, sys

soldir = sys.argv[1]
# Prefer a sensibly-named entry script if present, else any .py the model produced.
pys = sorted(glob.glob(os.path.join(soldir, "*.py")))
pys = [p for p in pys if not os.path.basename(p).startswith(("test_", "conftest"))] or pys


def run(stdin):
    cp = subprocess.run([sys.executable, pys[0]], input=stdin, capture_output=True, text=True, timeout=10)
    return cp.stdout.strip()


_NUMRE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def num(out):
    # accept "90", "90.0", "0.5", "= 90", "Total: 90 seconds" etc. -- last numeric token, as float
    matches = _NUMRE.findall(out or "")
    if not matches:
        return None
    try:
        return float(matches[-1])
    except Exception:
        return None


# CORE: every unit the prompt lists (incl. weeks, and weeks combined with other parts),
# plus the one fractional case the prompt promises (fractional SECONDS).
core_cases = [
    ("PT1H30M", 5400.0),
    ("P2DT5S", 172805.0),
    ("PT0.5S", 0.5),
    ("P1W", 604800.0),
    ("PT1M", 60.0),
    ("PT1H", 3600.0),
    ("P1D", 86400.0),
    ("PT45S", 45.0),
    ("P1WT1S", 604801.0),
    ("P1DT1H1M1S", 90061.0),
    ("PT2H15M30S", 8130.0),
    ("P3W2D", 1987200.0),
    ("PT0S", 0.0),
    ("P0D", 0.0),
    ("PT90M", 5400.0),
    ("P2WT12H", 1252800.0),
]

# IMPLICIT: fractional non-second units -- supported by a thorough reading, but the
# goal only promised fractional seconds, so this is implied-not-stated, not CORE.
implicit_cases = [
    ("PT1.5H", 5400.0),
    ("P1.5D", 129600.0),
]

if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

subs = []
for inp, exp in core_cases:
    got = num(run(inp + "\n"))
    ok = got is not None and abs(got - exp) < 1e-6
    subs.append({"name": "dur:" + inp, "tier": "core", "ok": ok})

for inp, exp in implicit_cases:
    got = num(run(inp + "\n"))
    ok = got is not None and abs(got - exp) < 1e-6
    subs.append({"name": "dur:" + inp, "tier": "implicit", "ok": ok})

print(json.dumps({"subcases": subs}))
