"""Arithmetic expression evaluator (no eval/exec).

Grammar (recursive descent, standard precedence + left associativity):
    expr   = term (('+' | '-') term)*
    term   = factor (('*' | '/') factor)*
    factor = '-' factor | '(' expr ')' | number
"""
import re


class CalcError(Exception):
    """Raised on malformed input or division by zero."""


# Tokenizer: numbers (int/decimal), operators, parens. Whitespace is dropped.
_TOKEN = re.compile(r"\s*(?:(\d+\.?\d*|\.\d+)|([-+*/()]))")


def _tokenize(expr):
    tokens, pos = [], 0
    while pos < len(expr):
        if expr[pos].isspace():
            pos += 1
            continue
        m = _TOKEN.match(expr, pos)
        if not m or m.end() == pos:
            raise CalcError(f"invalid character at position {pos}: {expr[pos]!r}")
        num, op = m.groups()
        tokens.append(("num", float(num)) if num is not None else ("op", op))
        pos = m.end()
    return tokens


def evaluate(expr: str) -> float:
    tokens = _tokenize(expr)
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else (None, None)

    def parse_expr():
        nonlocal pos
        val = parse_term()
        while peek() == ("op", "+") or peek() == ("op", "-"):
            op = tokens[pos][1]
            pos += 1
            rhs = parse_term()
            val = val + rhs if op == "+" else val - rhs
        return val

    def parse_term():
        nonlocal pos
        val = parse_factor()
        while peek() == ("op", "*") or peek() == ("op", "/"):
            op = tokens[pos][1]
            pos += 1
            rhs = parse_factor()
            if op == "*":
                val *= rhs
            else:
                if rhs == 0:
                    raise CalcError("division by zero")
                val /= rhs
        return val

    def parse_factor():
        nonlocal pos
        kind, value = peek()
        if (kind, value) == ("op", "-"):
            pos += 1
            return -parse_factor()
        if (kind, value) == ("op", "+"):  # unary plus
            pos += 1
            return parse_factor()
        if (kind, value) == ("op", "("):
            pos += 1
            val = parse_expr()
            if peek() != ("op", ")"):
                raise CalcError("missing closing parenthesis")
            pos += 1
            return val
        if kind == "num":
            pos += 1
            return value
        raise CalcError("unexpected end of input" if kind is None
                        else f"unexpected token {value!r}")

    if not tokens:
        raise CalcError("empty expression")
    result = parse_expr()
    if pos != len(tokens):
        raise CalcError(f"unexpected token {tokens[pos][1]!r}")
    return result


if __name__ == "__main__":
    eq = lambda a, b: abs(a - b) < 1e-9

    # precedence & associativity
    assert eq(evaluate("1 + 2 * 3"), 7)
    assert eq(evaluate("2 * 3 + 1"), 7)
    assert eq(evaluate("10 - 2 - 3"), 5)          # left-assoc
    assert eq(evaluate("8 / 4 / 2"), 1)           # left-assoc
    assert eq(evaluate("2 + 3 * 4 - 5"), 9)

    # parentheses
    assert eq(evaluate("(1 + 2) * 3"), 9)
    assert eq(evaluate("2 * (3 + (4 - 1))"), 12)
    assert eq(evaluate("-(3 + 4)"), -7)

    # decimals & unary
    assert eq(evaluate("3.5 + 1.5"), 5.0)
    assert eq(evaluate(".5 * 4"), 2.0)
    assert eq(evaluate("-2 * -3"), 6)
    assert eq(evaluate("  7  "), 7)

    # error cases
    for bad in ["1 +", "(1 + 2", "1 + 2)", "", "  ", "1 / 0",
                "2 ** 3", "1 2", "abc", "3 + * 4"]:
        try:
            evaluate(bad)
        except CalcError:
            pass
        else:
            raise AssertionError(f"expected CalcError for {bad!r}")

    print("all checks passed")
