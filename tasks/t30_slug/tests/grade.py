"""Irreducible grader. The contract is total (a slug has one right answer), so CORE
tests can be near-exhaustive. The antiref (a plausible wrong impl that keeps
punctuation / doesn't collapse separators) fails CORE -- proving the tests bite.
"""
import glob, json, os, subprocess, sys

soldir = sys.argv[1]


def find_solution(d):
    """Pick the runnable script, ignoring obvious test/helper files so a solution
    that ships its own tests alongside the script is still graded on the script."""
    cands = sorted(glob.glob(os.path.join(d, "*.py")))
    primary = [p for p in cands
               if not os.path.basename(p).lower().startswith(("test_", "conftest"))
               and not os.path.basename(p).lower().endswith("_test.py")]
    return (primary or cands)


pys = find_solution(soldir)
subs = []


def run(stdin):
    cp = subprocess.run([sys.executable, pys[0]], input=stdin, capture_output=True, text=True, timeout=10)
    return cp.stdout.strip()


cases = [
    ("Hello, World!", "hello-world"),
    ("  Multiple   Spaces! ", "multiple-spaces"),
    ("Already-Slug", "already-slug"),
    ("Cafe & Bar", "cafe-bar"),
]

if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

for inp, exp in cases:
    subs.append({"name": "slug:" + inp.strip()[:12], "tier": "core", "ok": run(inp + "\n") == exp})

print(json.dumps({"subcases": subs}))
