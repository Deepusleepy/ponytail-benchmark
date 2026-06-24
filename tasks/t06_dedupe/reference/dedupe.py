import sys

seen = set()
for line in sys.stdin:
    line = line.rstrip("\n")
    if line not in seen:
        seen.add(line)
        print(line)
