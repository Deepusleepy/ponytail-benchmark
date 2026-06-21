#!/usr/bin/env python3
"""CSV -> JSON converter. Stdlib only."""
import argparse
import csv
import io
import json
import sys


def csv_to_records(text):
    """Parse CSV text into a list of dicts keyed by header row."""
    return list(csv.DictReader(io.StringIO(text)))


def selfcheck():
    sample = "name,age\nAlice,30\nBob,25\n"
    recs = csv_to_records(sample)
    assert recs == [
        {"name": "Alice", "age": "30"},
        {"name": "Bob", "age": "25"},
    ], recs
    # Empty input -> empty list
    assert csv_to_records("") == []
    # Header only -> empty list
    assert csv_to_records("a,b\n") == []
    # Quoted field with comma survives round-trip through json
    quoted = csv_to_records('x\n"a,b"\n')
    assert quoted == [{"x": "a,b"}], quoted
    assert json.loads(json.dumps(quoted)) == quoted
    print("selfcheck passed")


def main(argv=None):
    p = argparse.ArgumentParser(description="Convert CSV to a JSON array of objects.")
    p.add_argument("file", nargs="?", help="CSV file; reads stdin if omitted")
    p.add_argument("--pretty", action="store_true", help="indent output")
    p.add_argument("--selfcheck", action="store_true", help="run self-tests and exit")
    args = p.parse_args(argv)

    if args.selfcheck:
        selfcheck()
        return 0

    if args.file:
        try:
            with open(args.file, newline="", encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            print(f"error: cannot read {args.file}: {e.strerror}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    records = csv_to_records(text)
    indent = 2 if args.pretty else None
    json.dump(records, sys.stdout, indent=indent, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
