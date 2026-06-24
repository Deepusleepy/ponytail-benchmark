import sys

for line in sys.stdin:
    parts = line.strip().split(" ")
    initials = "".join(p[0] for p in parts).upper()
    print(initials)
