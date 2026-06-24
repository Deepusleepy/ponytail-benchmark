"""Brownfield grader. CORE = a route can capture a path segment and the captured value
reaches the handler (so /users/123 yields output carrying "123", and a different id
yields that id). IMPLICIT = the pre-existing router still works: the fixed routes still
resolve, and an unknown path still reports not-found (regression check). The antiref
adds capture but falls back to the home page for unmatched paths, swallowing the 404 --
it passes CORE and fails IMPLICIT. Driven black-box via subprocess.
"""
import glob, json, os, subprocess, sys

soldir = sys.argv[1]
# Brownfield: drive the model's EDITED project. The entry point is the seed file
# router.py; target it explicitly so an added test_*.py / helper module can't shadow it
# via glob ordering. Fall back to any non-test .py the model produced.
all_pys = sorted(glob.glob(os.path.join(soldir, "*.py")))
non_test = [p for p in all_pys if not os.path.basename(p).startswith(("test_", "conftest"))]
named = [p for p in all_pys if os.path.basename(p) == "router.py"]
pys = named or non_test or all_pys
subs = []


def run(args):
    cp = subprocess.run([sys.executable, pys[0]] + args, capture_output=True, text=True, timeout=10)
    return (cp.stdout or "").strip()


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

# CORE: captured value reaches the handler. The prompt pins only that the captured
# segment ("123") gets to the handler so it can use it -- it does not pin the response
# wording. So we assert the captured value appears in the output and the route resolved
# (not the 404), accepting any surrounding handler text.
def resolved(out):
    return "404" not in out and out.strip() != ""


out1 = run(["GET", "/users/123"])
subs.append({"name": "capture_123", "tier": "core", "ok": ("123" in out1) and resolved(out1)})

out2 = run(["GET", "/users/42"])
subs.append({"name": "capture_42", "tier": "core", "ok": ("42" in out2) and resolved(out2)})

# Captured value tracks the path segment (it is the real captured value, not a constant
# and not the literal pattern token). We reject a solution that merely echoes the whole
# request path unchanged, but we DON'T forbid the handler from mentioning a path.
out3 = run(["GET", "/users/abc"])
echoes_path = out3.strip() in ("/users/abc", "GET /users/abc")
subs.append({"name": "capture_varies", "tier": "core",
             "ok": ("abc" in out3) and resolved(out3) and (out3 != out1)
                   and (":id" not in out3) and ("{id}" not in out3) and (not echoes_path)})

# IMPLICIT: existing exact routes still resolve
subs.append({"name": "exact_about", "tier": "implicit", "ok": run(["GET", "/about"]) == "about page"})
subs.append({"name": "exact_users", "tier": "implicit", "ok": run(["GET", "/users"]) == "all users"})
subs.append({"name": "exact_home", "tier": "implicit", "ok": run(["GET", "/"]) == "home page"})

# IMPLICIT: unknown paths still report not-found (must not be swallowed)
nf1 = run(["GET", "/nope"])
subs.append({"name": "notfound_unknown", "tier": "implicit", "ok": "404" in nf1})
nf2 = run(["GET", "/users/123/extra"])
subs.append({"name": "notfound_too_deep", "tier": "implicit", "ok": "404" in nf2})

print(json.dumps({"subcases": subs}))
