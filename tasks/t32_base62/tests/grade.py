"""Irreducible grader. base62 over the canonical 0-9A-Za-z alphabet has exactly one
right string per number, so CORE can be near-exhaustive. The antiref (orders lowercase
before uppercase) round-trips with itself but produces the wrong canonical strings, so
it fails the encode and decode CORE cases -- proving the tests bite.
"""
import glob, json, os, re, subprocess, sys

soldir = sys.argv[1]
pys = sorted(glob.glob(os.path.join(soldir, "*.py")))
pys = [p for p in pys if not os.path.basename(p).startswith(("test_", "conftest"))] or pys
subs = []

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def b62(n):
    if n == 0:
        return ALPHABET[0]
    out = []
    while n > 0:
        n, r = divmod(n, 62)
        out.append(ALPHABET[r])
    return "".join(reversed(out))


def run(args):
    cp = subprocess.run([sys.executable, pys[0]] + args, capture_output=True, text=True, timeout=10)
    return cp.stdout.strip()


_TOKRE = re.compile(r"[0-9A-Za-z]+")


def last_b62_token(out):
    # The base62 alphabet IS exactly one correct canonical string per number, so CORE
    # stays precise -- but accept it in whatever whitespace/format the model emits
    # (trailing newline, a label like "result: 1Z"). We take the last base62-charset
    # token from the output and compare it to the canonical string.
    matches = _TOKRE.findall(out or "")
    return matches[-1] if matches else None


def last_int(out):
    matches = re.findall(r"[-+]?\d+", out or "")
    if not matches:
        return None
    try:
        return int(matches[-1])
    except Exception:
        return None


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

# numbers spanning single/multi "digit" boundaries and case boundaries
nums = [0, 1, 9, 10, 35, 36, 61, 62, 63, 100, 123, 999, 3843, 3844, 238327, 1000000, 9999999999]

for n in nums:
    exp = b62(n)
    got = last_b62_token(run(["encode", str(n)]))
    subs.append({"name": "encode:%d" % n, "tier": "core", "ok": got == exp})

for n in nums:
    s = b62(n)
    got = last_int(run(["decode", s]))
    subs.append({"name": "decode:%s" % s, "tier": "core", "ok": got == n})

# round-trip: encode then decode returns the original number
for n in [7, 42, 500, 100000, 123456789]:
    enc = last_b62_token(run(["encode", str(n)]))
    got = last_int(run(["decode", enc])) if enc is not None else None
    subs.append({"name": "roundtrip:%d" % n, "tier": "core", "ok": got == n})

print(json.dumps({"subcases": subs}))
