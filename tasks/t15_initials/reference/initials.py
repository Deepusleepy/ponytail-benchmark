import sys

for line in sys.stdin:
    parts = line.split()  # split on any whitespace, drops empties
    if not parts:
        # a blank / whitespace-only line has no name on it -> emit a blank label
        # rather than crash, so the badge sheet stays line-for-line aligned
        print("")
        continue
    initials = "".join(p[0] for p in parts).upper()
    print(initials)
