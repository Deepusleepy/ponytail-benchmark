import argparse
import json
import sys


class DotenvParser:
    """Configurable parser for .env-style configuration files.

    Supports comments, blank lines, optional ``export`` prefixes, quoted values
    with escape sequences, inline comments, and several output formats.
    """

    def __init__(self, strip_export=True, strip_inline_comments=True,
                 unquote=True, coerce_types=False):
        self.strip_export = strip_export
        self.strip_inline_comments = strip_inline_comments
        self.unquote = unquote
        self.coerce_types = coerce_types

    def is_skippable(self, line):
        stripped = line.strip()
        return not stripped or stripped.startswith("#")

    def remove_export(self, key):
        if self.strip_export and key.startswith("export "):
            return key[len("export "):].strip()
        return key

    def remove_inline_comment(self, value):
        if not self.strip_inline_comments:
            return value
        in_single = False
        in_double = False
        out = []
        for ch in value:
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            elif ch == "#" and not in_single and not in_double:
                break
            out.append(ch)
        return "".join(out)

    def unquote_value(self, value):
        if not self.unquote:
            return value
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            inner = value[1:-1]
            if value[0] == '"':
                inner = inner.replace("\\n", "\n").replace("\\t", "\t")
                inner = inner.replace('\\"', '"').replace("\\\\", "\\")
            return inner
        return value

    def coerce(self, value):
        if not self.coerce_types:
            return value
        lowered = value.lower()
        if lowered in ("true", "false"):
            return lowered == "true"
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    def parse_line(self, line):
        if "=" not in line:
            return None
        key, _, raw_value = line.partition("=")
        key = self.remove_export(key.strip())
        value = self.remove_inline_comment(raw_value)
        value = self.unquote_value(value)
        if not (value and value[0] in ("'", '"')):
            value = value.strip()
        return key, self.coerce(value)

    def parse(self, text):
        settings = {}
        for line in text.splitlines():
            if self.is_skippable(line):
                continue
            parsed = self.parse_line(line)
            if parsed is None:
                continue
            key, value = parsed
            if key:
                settings[key] = value
        return settings


def render(settings, output_format):
    if output_format == "env":
        return "\n".join("%s=%s" % (k, v) for k, v in settings.items())
    if output_format == "pretty":
        return json.dumps(settings, indent=2)
    return json.dumps(settings)


def build_parser():
    parser = argparse.ArgumentParser(description="Parse a .env file into JSON.")
    parser.add_argument("path", help="path to the .env file")
    parser.add_argument("--format", dest="output_format", default="json",
                        choices=["json", "pretty", "env"], help="output format")
    parser.add_argument("--coerce", action="store_true",
                        help="coerce numeric and boolean values")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    with open(args.path, encoding="utf-8") as f:
        text = f.read()
    parser = DotenvParser(coerce_types=args.coerce)
    settings = parser.parse(text)
    print(render(settings, args.output_format))


if __name__ == "__main__":
    main()
