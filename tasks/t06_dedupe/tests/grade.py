"""Over-build task grader (line dedupe). Correctness is a FLOOR both lean and bloated
solutions pass; the size meter (in the gate) discriminates. Core tier only.

Core behaviors from the prompt goal:
  - "reads lines on standard input and prints them back with the repeats removed"
  - "keeping only the first time each line appears and in that original order"
The produced script is driven black-box via subprocess over stdin; stdout is split into
lines and compared for exact dedup-in-first-occurrence-order.
"""
import glob, json, os, subprocess, sys


def _is_test_file(path):
    base = os.path.basename(path).lower()
    stem = os.path.splitext(base)[0]
    return (stem.startswith("test_") or stem.startswith("test-") or stem.endswith("_test")
            or stem.endswith("-test") or ".test." in base or ".spec." in base
            or stem in ("conftest", "setup", "__init__"))


def pick_sources(soldir, exts):
    """Return runnable source files, putting the real entry point first.
    A model may legitimately ship its own unit-test file next to the solution;
    drive the actual script, not the test module, regardless of sort order."""
    files = []
    for ext in exts:
        files += glob.glob(os.path.join(soldir, "*" + ext))
    files = sorted(set(files))
    non_test = [f for f in files if not _is_test_file(f)]
    return non_test or files


soldir = sys.argv[1]
pys = pick_sources(soldir, [".py"])
subs = []


def run(text):
    cp = subprocess.run([sys.executable, pys[0]], input=text,
                        capture_output=True, text=True, timeout=15)
    return [l for l in cp.stdout.split("\n")]


def out_lines(text):
    lines = run(text)
    # drop a single trailing empty element from the final newline
    if lines and lines[-1] == "":
        lines = lines[:-1]
    return lines


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

# --- Core 1: adjacent and non-adjacent repeats removed, first kept -----------
inp1 = "apple\nbanana\napple\ncherry\nbanana\napple\n"
want1 = ["apple", "banana", "cherry"]
subs.append({"name": "removes_repeats", "tier": "core", "ok": out_lines(inp1) == want1})

# --- Core 2: original first-appearance order is preserved --------------------
inp2 = "zebra\nyak\nzebra\nant\nyak\nant\nmole\n"
want2 = ["zebra", "yak", "ant", "mole"]
subs.append({"name": "first_occurrence_order", "tier": "core", "ok": out_lines(inp2) == want2})

# --- Core 3: already-unique input is returned unchanged ----------------------
inp3 = "one\ntwo\nthree\n"
want3 = ["one", "two", "three"]
subs.append({"name": "unique_unchanged", "tier": "core", "ok": out_lines(inp3) == want3})

# --- Core 4: distinct lines that are not duplicates all survive --------------
inp4 = "a\nA\nb\na\nB\nA\n"
want4 = ["a", "A", "b", "B"]  # case-sensitive: 'a' and 'A' are different lines
subs.append({"name": "case_sensitive_distinct", "tier": "core", "ok": out_lines(inp4) == want4})

print(json.dumps({"subcases": subs}))
