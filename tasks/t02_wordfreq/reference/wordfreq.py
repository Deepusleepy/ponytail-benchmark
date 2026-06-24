import re, sys
from collections import Counter

words = re.findall(r"[a-z0-9']+", sys.stdin.read().lower())
for word, count in Counter(words).most_common(10):
    print(word, count)
