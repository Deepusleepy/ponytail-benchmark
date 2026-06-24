import csv, json, sys

with open(sys.argv[1], newline="") as f:
    sample = f.read(2048)
    f.seek(0)
    delim = ";" if sample.count(";") > sample.count(",") else ","
    for row in csv.DictReader(f, delimiter=delim):
        print(json.dumps(dict(row)))
