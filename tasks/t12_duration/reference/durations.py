import sys

total = 0  # total seconds
for line in sys.stdin:
    s = line.strip()
    if not s:
        continue
    parts = s.split(":")
    if len(parts) != 2:
        continue  # not a "m:s" row -> skip rather than crash
    m_s, sec_s = parts[0].strip(), parts[1].strip()
    try:
        m = int(m_s)
        sec = int(sec_s)
    except ValueError:
        continue  # garbage row -> skip, don't blow up the total
    total += m * 60 + sec

print("%d:%02d" % (total // 60, total % 60))
