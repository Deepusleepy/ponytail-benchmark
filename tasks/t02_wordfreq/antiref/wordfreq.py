import argparse
import json
import re
import sys
from collections import Counter


class WordCounter:
    """Configurable word-frequency analyzer with several output formats."""

    DEFAULT_PATTERN = r"[a-z0-9']+"

    def __init__(self, top=10, pattern=None, case_sensitive=False, output_format="plain"):
        self.top = top
        self.pattern = pattern or self.DEFAULT_PATTERN
        self.case_sensitive = case_sensitive
        self.output_format = output_format
        self._counter = Counter()

    def normalize(self, text):
        if not self.case_sensitive:
            text = text.lower()
        return text

    def tokenize(self, text):
        return re.findall(self.pattern, self.normalize(text))

    def feed(self, text):
        self._counter.update(self.tokenize(text))
        return self

    def ranking(self):
        return self._counter.most_common(self.top)

    def render_plain(self, ranking):
        lines = []
        for word, count in ranking:
            lines.append("{0} {1}".format(word, count))
        return "\n".join(lines)

    def render_table(self, ranking):
        if not ranking:
            return ""
        width = max(len(word) for word, _ in ranking)
        lines = []
        for word, count in ranking:
            lines.append("{0:<{1}}  {2}".format(word, width, count))
        return "\n".join(lines)

    def render_json(self, ranking):
        return json.dumps([{"word": w, "count": c} for w, c in ranking], indent=2)

    def render_csv(self, ranking):
        lines = ["word,count"]
        for word, count in ranking:
            lines.append("{0},{1}".format(word, count))
        return "\n".join(lines)

    def render(self, ranking):
        renderers = {
            "plain": self.render_plain,
            "table": self.render_table,
            "json": self.render_json,
            "csv": self.render_csv,
        }
        renderer = renderers.get(self.output_format, self.render_plain)
        return renderer(ranking)

    def report(self):
        return self.render(self.ranking())


def build_parser():
    parser = argparse.ArgumentParser(
        description="Print the most frequent words read from standard input."
    )
    parser.add_argument("-n", "--top", type=int, default=10,
                        help="how many words to show")
    parser.add_argument("--pattern", default=None,
                        help="regular expression used to split words")
    parser.add_argument("--case-sensitive", action="store_true",
                        help="do not fold case before counting")
    parser.add_argument("--format", dest="output_format", default="plain",
                        choices=["plain", "table", "json", "csv"],
                        help="how to print the ranking")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    counter = WordCounter(
        top=args.top,
        pattern=args.pattern,
        case_sensitive=args.case_sensitive,
        output_format=args.output_format,
    )
    counter.feed(sys.stdin.read())
    output = counter.report()
    if output:
        print(output)


if __name__ == "__main__":
    main()
