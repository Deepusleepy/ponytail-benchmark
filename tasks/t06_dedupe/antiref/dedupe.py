import argparse
import sys
from collections import OrderedDict


class LineDeduplicator:
    """Remove duplicate lines from a stream with configurable matching.

    Supports case-insensitive comparison, ignoring surrounding whitespace when
    deciding equality, keeping either the first or the last occurrence, and an
    optional repeat count alongside each surviving line.
    """

    def __init__(self, ignore_case=False, ignore_whitespace=False,
                 keep="first", show_count=False):
        self.ignore_case = ignore_case
        self.ignore_whitespace = ignore_whitespace
        self.keep = keep
        self.show_count = show_count

    def key_for(self, line):
        key = line
        if self.ignore_whitespace:
            key = key.strip()
        if self.ignore_case:
            key = key.lower()
        return key

    def deduplicate(self, lines):
        order = OrderedDict()
        counts = OrderedDict()
        for line in lines:
            key = self.key_for(line)
            counts[key] = counts.get(key, 0) + 1
            if key not in order:
                order[key] = line
            elif self.keep == "last":
                order[key] = line
        result = []
        for key, line in order.items():
            result.append((line, counts[key]))
        return result

    def format_line(self, line, count):
        if self.show_count:
            return "%d\t%s" % (count, line)
        return line

    def run(self, stream, out):
        lines = [raw.rstrip("\n") for raw in stream]
        for line, count in self.deduplicate(lines):
            out.write(self.format_line(line, count) + "\n")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Print input lines with duplicate lines removed.")
    parser.add_argument("-i", "--ignore-case", action="store_true",
                        help="compare lines case-insensitively")
    parser.add_argument("-w", "--ignore-whitespace", action="store_true",
                        help="ignore leading/trailing whitespace when comparing")
    parser.add_argument("--keep", choices=["first", "last"], default="first",
                        help="which occurrence of a duplicate to keep")
    parser.add_argument("-c", "--count", action="store_true",
                        help="prefix each line with how many times it appeared")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    dedup = LineDeduplicator(
        ignore_case=args.ignore_case,
        ignore_whitespace=args.ignore_whitespace,
        keep=args.keep,
        show_count=args.count,
    )
    dedup.run(sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
