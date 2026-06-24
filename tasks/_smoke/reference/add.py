import sys

try:
    a = int(sys.argv[1])
    b = int(sys.argv[2])
except (IndexError, ValueError):
    print("usage: add.py A B  (two integers)")
    sys.exit(1)

print(a + b)
