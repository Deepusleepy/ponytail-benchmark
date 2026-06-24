import re, sys

text = sys.stdin.readline().lower()
print(re.sub(r"[^a-z0-9]+", "-", text).strip("-"))
