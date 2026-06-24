"""Over-build task grader. Correctness is a FLOOR both lean and bloated solutions pass;
the size meter (in the gate) is what discriminates. So tests are core-only here.
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


def run(csv_text):
    p = os.path.join(os.getcwd(), "in.csv")
    with open(p, "w", newline="") as f:
        f.write(csv_text)
    cp = subprocess.run([sys.executable, pys[0], p], capture_output=True, text=True, timeout=15)
    return cp.stdout


def parse_jsonl(out):
    objs = []
    for line in out.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            objs.append(json.loads(line))
        except Exception:
            return None
    return objs


def norm_rows(objs):
    """Normalize a list of row dicts for comparison: values compared as strings so
    that a solution which leaves CSV fields as strings ("30") and one that coerces
    numeric-looking fields (30) both count as correct -- the prompt only asks for
    'each row as a JSON object', not a type policy."""
    if objs is None:
        return None
    out = []
    for o in objs:
        if not isinstance(o, dict):
            return None
        out.append({k: str(v) for k, v in o.items()})
    return out


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

want = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
subs.append({"name": "comma_csv", "tier": "core",
             "ok": norm_rows(parse_jsonl(run("name,age\nAlice,30\nBob,25\n"))) == want})
subs.append({"name": "semicolon_csv", "tier": "core",
             "ok": norm_rows(parse_jsonl(run("name;age\nAlice;30\nBob;25\n"))) == want})
print(json.dumps({"subcases": subs}))
