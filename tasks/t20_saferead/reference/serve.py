import os, sys

base = os.path.realpath("public")
target = os.path.realpath(os.path.join(base, sys.argv[1]))
if os.path.commonpath([base, target]) != base:
    print("forbidden")
    sys.exit(1)
with open(target) as f:
    sys.stdout.write(f.read())
