"""Over-build task grader (slugify). Correctness is a FLOOR both lean and bloated
solutions pass; the size meter (in the gate) discriminates. Core tier only.

Core behaviors from the prompt goal:
  - "reads a title on standard input and prints the slug"
  - example: "My First Post!" -> "my-first-post"
  - "lowercase, with the spaces and punctuation turned into single dashes and no dash
     hanging off either end"
The produced script is driven black-box via node over stdin.
"""
import glob, json, os, subprocess, sys


def _is_test_file(path):
    base = os.path.basename(path).lower()
    stem = os.path.splitext(base)[0]
    return (stem.startswith("test_") or stem.startswith("test-") or stem.endswith("_test")
            or stem.endswith("-test") or stem.endswith(".test") or stem.endswith(".spec")
            or ".test." in base or ".spec." in base
            or stem in ("conftest", "setup"))


def pick_sources(soldir, exts):
    """Return runnable source files, putting the real entry point first.
    A model may legitimately ship its own unit-test file (e.g. slugify.test.js)
    next to the solution; drive the actual script, not the test module."""
    files = []
    for ext in exts:
        files += glob.glob(os.path.join(soldir, "*" + ext))
    files = sorted(set(files))
    non_test = [f for f in files if not _is_test_file(f)]
    return non_test or files


soldir = sys.argv[1]
jss = pick_sources(soldir, [".js", ".mjs"])
subs = []


def run(title):
    cp = subprocess.run(["node", jss[0]], input=title,
                        capture_output=True, text=True, timeout=15)
    return cp.stdout.strip()


if not jss:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

cases = [
    ("worked_example", "My First Post!", "my-first-post"),
    ("lowercase", "HELLO World", "hello-world"),
    ("punctuation_to_dash", "Hello, World!", "hello-world"),
    ("collapse_runs", "a   b---c", "a-b-c"),
    ("trim_edges", "  spaced out  ", "spaced-out"),
    ("leading_trailing_punct", "***wow***", "wow"),
    ("alnum_kept", "Top 10 Tips for 2024", "top-10-tips-for-2024"),
]

for name, title, want in cases:
    subs.append({"name": name, "tier": "core", "ok": run(title) == want})

print(json.dumps({"subcases": subs}))
