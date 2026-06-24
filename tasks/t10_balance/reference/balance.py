import sys

total = 0.0
running = []
for line in sys.stdin:
    s = line.strip()
    if not s:
        continue
    try:
        amt = float(s)
    except ValueError:
        continue  # ignore junk rows rather than crash
    total += amt
    running.append(total)

for v in running:
    print(v)
print(total)
