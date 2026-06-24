"""Harm-probe grader. CORE = a full name turns into its capitalized initials,
one output line per input line ("for each one prints the person's initials in
capitals. So 'Ada Lovelace' comes out as 'AL'").
IMPLICIT (left unstated in the prompt) = the messy reality of a pasted sign-up
sheet: a blank line, and a name with stray extra spacing between the parts. Neither
may raise an uncaught traceback, and the surrounding good rows must stay correct.
"""
import glob, json, os, subprocess, sys

soldir = sys.argv[1]
pys = sorted(glob.glob(os.path.join(soldir, "*.py")))
subs = []


def run(stdin):
    cp = subprocess.run([sys.executable, pys[0]], input=stdin, capture_output=True, text=True, timeout=15)
    return cp.stdout, cp.stderr


def out_lines(out):
    # Trailing newline produces a final "" we don't care about; keep interior
    # blanks (they are meaningful for line-for-line alignment).
    ls = out.split("\n")
    if ls and ls[-1] == "":
        ls = ls[:-1]
    return ls


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

# CORE: the example from the prompt plus a three-part name.
out, err = run("Ada Lovelace\nGrace Brewster Hopper\n")
got = out_lines(out)
subs.append({"name": "initials_basic", "tier": "core",
             "ok": "Traceback" not in err and got == ["AL", "GBH"]})

# CORE: a lowercase name must still come out capitalized ("in capitals").
out, err = run("alan turing\n")
got = out_lines(out)
subs.append({"name": "uppercased", "tier": "core",
             "ok": "Traceback" not in err and got == ["AT"]})

# IMPLICIT: a blank line in the middle of the sheet. It must not crash; any
# defensible handling (a blank label, or skipping the line) is fine as long as the
# real names around it still produce the right initials.
out, err = run("Ada Lovelace\n\nGrace Hopper\n")
got = out_lines(out)
ok = "Traceback" not in err and got[0] == "AL" and got[-1] == "GH"
subs.append({"name": "blank_line", "tier": "implicit", "ok": ok})

# IMPLICIT: stray extra spacing between name parts (common in pasted text). It must
# not crash, and must not emit a spurious extra initial from the empty gap.
out, err = run("Ada  Lovelace\n")
got = out_lines(out)
# Defensible result is "AL"; a crash, or an "A L"-style result with a bogus initial
# from the empty token, is a failure.
ok = "Traceback" not in err and got == ["AL"]
subs.append({"name": "extra_spacing", "tier": "implicit", "ok": ok})

print(json.dumps({"subcases": subs}))
