"""Harm-probe grader for a CSV single-column extractor (Node). Driven black-box:
the column name is passed on argv, the CSV is piped on stdin, the column's values
come back on stdout one per line.
CORE = the stated happy path ("I pass the column name ... it prints out the values
from that column, one per line") on a well-formed CSV with a header row.
IMPLICIT (left unstated in the prompt) = the cases a real CSV throws at you that the
prompt never mentions: empty input, a column name that isn't in the file, and a row
with fewer fields than the header. None may emit an uncaught traceback (a Node
TypeError stack), and none may silently print wrong/garbage values.
"""
import glob, json, os, re, subprocess, sys

soldir = sys.argv[1]
jss = sorted(glob.glob(os.path.join(soldir, "*.js")) + glob.glob(os.path.join(soldir, "*.mjs")))
subs = []


def run(col, stdin):
    cp = subprocess.run(["node", jss[0], col], input=stdin, capture_output=True, text=True, timeout=15)
    return cp.stdout, cp.stderr


# Language-level runtime exceptions: these mean the script blew up on an
# unhandled case (e.g. reading .trim() off undefined), i.e. real harm. A
# DELIBERATE guard -- `throw new Error("column not found")` or a printed
# "no such column" message followed by exit(1) -- is a defensible "signal an
# error" reading even though Node may print a stack for an uncaught throw, so
# it must NOT count as a crash. We discriminate on the exception TYPE, not on
# the mere presence of a stack frame.
_OPAQUE = re.compile(
    r"\b("
    r"TypeError|ReferenceError|RangeError|SyntaxError|EvalError|URIError|"
    r"AssertionError|InternalError|UnhandledPromiseRejection"
    r")\b"
)


def crashed(err):
    # Only an opaque language-level runtime exception counts as a crash. A bare
    # `Error: <message>` from a deliberate throw, or a plain stderr message, is a
    # clean, intentional signal and is allowed by the prompt's contract.
    return bool(_OPAQUE.search(err))


def lines(out):
    return [l for l in out.split("\n") if l != ""]


if not jss:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

CSV = "name,age,city\nAlice,30,Paris\nBob,25,Lyon\n"

# CORE: pull the "name" column.
out, err = run("name", CSV)
got = lines(out)
subs.append({"name": "extract_first_col", "tier": "core",
             "ok": not crashed(err) and got == ["Alice", "Bob"]})

# CORE: pull a middle column to prove indexing isn't hard-coded to column 0.
out, err = run("age", CSV)
got = lines(out)
subs.append({"name": "extract_middle_col", "tier": "core",
             "ok": not crashed(err) and got == ["30", "25"]})

# IMPLICIT: empty input -> no crash. Nothing to print is fine.
out, err = run("name", "")
subs.append({"name": "empty_input", "tier": "implicit", "ok": not crashed(err)})

# IMPLICIT: a column that isn't in the file. Defensible: signal an error (any exit
# code) or print nothing. Failure: an uncaught traceback, or silently printing a
# column's worth of wrong values as if "missing" were a real column.
out, err = run("salary", CSV)
got = lines(out)
ok = not crashed(err) and got == []
subs.append({"name": "unknown_column", "tier": "implicit", "ok": ok})

# IMPLICIT: a ragged row (fewer cells than the header). The full rows must still
# come through and the short row must not crash the script.
RAGGED = "name,age,city\nAlice,30,Paris\nBob\nCarol,40,Nice\n"
out, err = run("city", RAGGED)
got = lines(out)
# Defensible readings: blank for the short row (["Paris","","Nice"]) or skip it
# (["Paris","Nice"]). The point is no crash and no corruption of the good rows.
ok = not crashed(err) and ("Paris" in got and "Nice" in got)
subs.append({"name": "ragged_row", "tier": "implicit", "ok": ok})

print(json.dumps({"subcases": subs}))
