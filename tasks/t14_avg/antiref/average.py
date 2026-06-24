import sys

values = []
for line in sys.stdin:
    values.append(float(line))

print(sum(values) / len(values))
