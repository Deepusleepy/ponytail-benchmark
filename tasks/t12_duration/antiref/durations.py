import sys

total = 0
for line in sys.stdin:
    m, sec = line.strip().split(":")
    total += int(m) * 60 + int(sec)

print("%d:%02d" % (total // 60, total % 60))
