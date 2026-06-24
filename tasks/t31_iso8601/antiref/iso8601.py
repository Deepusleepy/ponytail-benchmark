import re, sys

text = sys.stdin.readline().strip()

# walk the duration token by token and add up the seconds
units = {"D": 86400, "H": 3600, "M": 60, "S": 1}
total = 0
for value, letter in re.findall(r"(\d+)([DHMS])", text):
    total += int(value) * units[letter]

print(total)
