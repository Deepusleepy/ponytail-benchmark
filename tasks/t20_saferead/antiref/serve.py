import sys

with open("public/" + sys.argv[1]) as f:
    sys.stdout.write(f.read())
