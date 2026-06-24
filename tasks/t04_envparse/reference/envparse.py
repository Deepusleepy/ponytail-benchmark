import json, sys

settings = {}
with open(sys.argv[1]) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        settings[key.strip()] = value.strip()

print(json.dumps(settings))
