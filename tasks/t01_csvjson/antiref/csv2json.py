import argparse, csv, json, sys


class CsvConverter:
    """Flexible CSV-to-JSON converter supporting multiple output formats."""

    def __init__(self, path, delimiter=None, output_format="jsonl"):
        self.path = path
        self.delimiter = delimiter
        self.output_format = output_format

    def detect_delimiter(self, sample):
        candidates = [",", ";", "\t", "|"]
        counts = {c: sample.count(c) for c in candidates}
        return max(counts, key=counts.get)

    def read_rows(self):
        with open(self.path, newline="", encoding="utf-8") as f:
            sample = f.read(4096)
            f.seek(0)
            delim = self.delimiter or self.detect_delimiter(sample)
            reader = csv.DictReader(f, delimiter=delim)
            return [dict(r) for r in reader]

    def convert(self):
        rows = self.read_rows()
        if self.output_format == "json":
            print(json.dumps(rows, indent=2))
        elif self.output_format == "pretty":
            for r in rows:
                print(json.dumps(r, indent=2))
        else:
            for r in rows:
                print(json.dumps(r))


def main():
    parser = argparse.ArgumentParser(description="Convert a CSV file to JSON.")
    parser.add_argument("path", help="path to the CSV file")
    parser.add_argument("--delimiter", default=None, help="force a delimiter")
    parser.add_argument("--format", dest="output_format", default="jsonl",
                        choices=["jsonl", "json", "pretty"], help="output format")
    args = parser.parse_args()
    converter = CsvConverter(args.path, args.delimiter, args.output_format)
    converter.convert()


if __name__ == "__main__":
    main()
