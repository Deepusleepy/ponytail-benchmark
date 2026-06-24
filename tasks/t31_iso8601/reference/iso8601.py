import re, sys

text = sys.stdin.readline().strip()

# PnWnDTnHnMnS -- weeks, days, then a T-separated time part with hours, minutes,
# seconds (seconds may be fractional). Every component is optional.
m = re.fullmatch(
    r"P(?:(\d+(?:\.\d+)?)W)?(?:(\d+(?:\.\d+)?)D)?"
    r"(?:T(?:(\d+(?:\.\d+)?)H)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?)?",
    text,
)
if not m:
    raise ValueError("not an ISO-8601 duration: %r" % text)

w, d, h, mi, s = (float(g) if g is not None else 0.0 for g in m.groups())
total = w * 604800 + d * 86400 + h * 3600 + mi * 60 + s

# print an integer when the result is whole, else the decimal value
print(int(total) if total == int(total) else total)
