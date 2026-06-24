import sys

values = []
for line in sys.stdin:
    s = line.strip()
    if not s:
        continue
    try:
        values.append(float(s))
    except ValueError:
        continue  # ignore non-numeric rows rather than crash

if not values:
    # no numbers to average -> say so instead of dividing by zero
    print("no data")
else:
    print(sum(values) / len(values))
