"""Irreducible grader. A number in 1..3999 has exactly one standard Roman numeral and
each numeral one value, so CORE can be near-exhaustive. The antiref (additive only:
4 -> "IIII", and decode that just sums symbols so "IV" reads as 6) fails CORE in both
directions -- proving the tests bite. The produced script is driven black-box via node.
"""
import glob, json, os, re, subprocess, sys

soldir = sys.argv[1]
jss = sorted(glob.glob(os.path.join(soldir, "*.js")) + glob.glob(os.path.join(soldir, "*.mjs"))
             + glob.glob(os.path.join(soldir, "*.cjs")))
jss = [p for p in jss if not re.search(r"(\.test\.|\.spec\.|^test[._-])", os.path.basename(p))] or jss
subs = []

TABLE = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
         (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
         (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def to_roman(n):
    out = ""
    for value, sym in TABLE:
        while n >= value:
            out += sym
            n -= value
    return out


def run(arg):
    cp = subprocess.run(["node", jss[0], arg], capture_output=True, text=True, timeout=10)
    return cp.stdout.strip()


_ROMRE = re.compile(r"[MDCLXVImdclxvi]+")
_NUMRE = re.compile(r"[-+]?\d+")


def last_roman(out):
    # A number in 1..3999 has exactly one canonical numeral, so CORE stays precise --
    # but accept it in whatever whitespace/case/format the model emits. The numeral's
    # CASE is a presentation choice the prompt never pins (subtractive forms ARE pinned),
    # so we compare case-insensitively and pull the last roman-letter token.
    matches = _ROMRE.findall(out or "")
    return matches[-1].upper() if matches else None


def last_int(out):
    matches = _NUMRE.findall(out or "")
    if not matches:
        return None
    try:
        return int(matches[-1])
    except Exception:
        return None


if not jss:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

# numbers that exercise every subtractive form plus boundaries
nums = [1, 2, 3, 4, 5, 9, 10, 14, 19, 40, 44, 49, 50, 90, 99, 100, 400, 444,
        500, 900, 990, 1000, 1984, 2024, 3549, 3888, 3999]

for n in nums:
    exp = to_roman(n)
    got = last_roman(run(str(n)))
    subs.append({"name": "to_roman:%d" % n, "tier": "core", "ok": got == exp})

for n in nums:
    s = to_roman(n)
    got = last_int(run(s))
    subs.append({"name": "to_number:%s" % s, "tier": "core", "ok": got == n})

print(json.dumps({"subcases": subs}))
