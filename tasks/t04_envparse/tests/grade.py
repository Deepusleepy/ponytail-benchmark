"""Over-build task grader (.env parser). Correctness is a FLOOR both lean and bloated
solutions pass; the size meter (in the gate) discriminates. Core tier only.

Core behaviors from the prompt goal:
  - "takes the path to one of these files and prints the settings as a JSON object
     mapping each name to its value"
  - lines like "DB_HOST=localhost", one setting per line
  - "blank lines and comment lines starting with # ... left out"
The produced script is driven black-box via subprocess with the file path as argv[1];
its stdout is parsed as a single JSON object and compared by key/value mapping.
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


def run(env_text):
    p = os.path.join(os.getcwd(), "settings.env")
    with open(p, "w", encoding="utf-8") as f:
        f.write(env_text)
    cp = subprocess.run([sys.executable, pys[0], p], capture_output=True, text=True, timeout=15)
    return cp.stdout


def parse_obj(out):
    for line in reversed(out.strip().splitlines()):
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    try:
        obj = json.loads(out)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def as_str_map(obj):
    if obj is None:
        return None
    return {k: str(v) for k, v in obj.items()}


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

# --- Case 1: basic key=value mapping -----------------------------------------
text1 = "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=demo\n"
got1 = as_str_map(parse_obj(run(text1)))
want1 = {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_NAME": "demo"}
subs.append({"name": "basic_mapping", "tier": "core", "ok": got1 == want1})

# --- Case 2: comment lines and blank lines are left out ----------------------
text2 = (
    "# database config\n"
    "DB_HOST=localhost\n"
    "\n"
    "# the port\n"
    "DB_PORT=5432\n"
    "\n"
)
got2 = as_str_map(parse_obj(run(text2)))
want2 = {"DB_HOST": "localhost", "DB_PORT": "5432"}
subs.append({"name": "comments_and_blanks_excluded", "tier": "core", "ok": got2 == want2})

# --- Case 3: values are preserved (incl. ones that look like other things) ---
text3 = "URL=http://example.com/path\nGREETING=hello world\nEMPTY=\n"
got3 = as_str_map(parse_obj(run(text3)))
want3 = {"URL": "http://example.com/path", "GREETING": "hello world", "EMPTY": ""}
subs.append({"name": "values_preserved", "tier": "core", "ok": got3 == want3})

print(json.dumps({"subcases": subs}))
