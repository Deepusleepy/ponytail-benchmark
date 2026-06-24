#!/usr/bin/env python3
"""csv2json.py - Convert CSV to a JSON array of objects (stdlib only).

Usage:
    python csv2json.py [file.csv]        # read from file, or stdin if omitted
    python csv2json.py --pretty [file]   # indented JSON output
    python csv2json.py --selfcheck       # run built-in assert-based tests

Each CSV row becomes a JSON object keyed by the header row. Output is a JSON
array of those objects, printed to stdout.
"""

import argparse
import csv
import io
import json
import sys


def csv_to_records(text):
    """Parse CSV text into a list of dict records keyed by the header row.

    Returns an empty list if the input has no header row.
    """
    reader = csv.DictReader(io.StringIO(text))
    records = []
    for row in reader:
        # csv.DictReader yields OrderedDict; convert to plain dict for clean
        # JSON serialization. A None key may appear if a row has more fields
        # than the header (the extras are collected under the None key); we
        # drop that to keep keys string-typed and predictable.
        clean = {}
        for key, value in row.items():
            if key is None:
                continue
            # DictReader uses None for fields missing from a short row; emit an
            # empty string instead so every record has string-valued fields.
            clean[key] = "" if value is None else value
        records.append(clean)
    return records


def convert(text, pretty=False):
    """Convert CSV text into a JSON string (array of objects)."""
    records = csv_to_records(text)
    if pretty:
        return json.dumps(records, indent=2, ensure_ascii=False)
    return json.dumps(records, ensure_ascii=False)


def read_input(path):
    """Read CSV text from a file path, or from stdin if path is None.

    Raises FileNotFoundError / OSError on file problems so the caller can
    report a clear error and exit non-zero.
    """
    if path is None:
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def selfcheck():
    """Run assert-based tests against small in-memory CSV inputs."""
    # Basic conversion.
    sample = "name,age,city\nAlice,30,NYC\nBob,25,LA\n"
    records = csv_to_records(sample)
    assert records == [
        {"name": "Alice", "age": "30", "city": "NYC"},
        {"name": "Bob", "age": "25", "city": "LA"},
    ], records

    # Compact JSON output round-trips back to the same data.
    compact = convert(sample, pretty=False)
    assert json.loads(compact) == records, compact
    assert "\n" not in compact, "compact output should be single-line"

    # Pretty output is indented but parses to the same data.
    pretty = convert(sample, pretty=True)
    assert json.loads(pretty) == records, pretty
    assert "\n" in pretty and "  " in pretty, "pretty output should be indented"

    # Header only (no data rows) yields an empty array.
    assert csv_to_records("a,b,c\n") == []
    assert convert("a,b,c\n") == "[]"

    # Completely empty input yields an empty array.
    assert csv_to_records("") == []
    assert convert("") == "[]"

    # Quoted fields containing commas and embedded newlines are preserved.
    quoted = 'name,note\n"Smith, John","line1\nline2"\n'
    qrecords = csv_to_records(quoted)
    assert qrecords == [{"name": "Smith, John", "note": "line1\nline2"}], qrecords

    # Missing trailing value is kept as an empty string.
    missing = "a,b,c\n1,2\n"
    mrecords = csv_to_records(missing)
    assert mrecords == [{"a": "1", "b": "2", "c": ""}], mrecords

    # Non-ASCII content is preserved without escaping (ensure_ascii=False).
    unicode_csv = "city\nMünchen\n"
    assert csv_to_records(unicode_csv) == [{"city": "München"}]
    assert "München" in convert(unicode_csv)

    print("selfcheck: all tests passed")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert CSV to a JSON array of objects.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="CSV file to read (reads from stdin if omitted)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="indent the JSON output for readability",
    )
    parser.add_argument(
        "--selfcheck",
        action="store_true",
        help="run built-in assert-based tests and exit",
    )
    args = parser.parse_args(argv)

    if args.selfcheck:
        return selfcheck()

    try:
        text = read_input(args.file)
    except FileNotFoundError:
        sys.stderr.write("error: file not found: {}\n".format(args.file))
        return 1
    except IsADirectoryError:
        sys.stderr.write("error: not a file (is a directory): {}\n".format(args.file))
        return 1
    except OSError as exc:
        sys.stderr.write("error: could not read {}: {}\n".format(args.file, exc))
        return 1

    output = convert(text, pretty=args.pretty)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
