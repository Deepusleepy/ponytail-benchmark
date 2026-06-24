"""Arithmetic expression evaluator (no eval/exec).

Supports + - * / with parentheses and integer/decimal numbers, honoring
standard precedence (* / before + -) and left-to-right associativity.
Whitespace is ignored. Malformed input and division by zero raise
``CalcError``.

Grammar (recursive descent):

    expr   := term (('+' | '-') term)*
    term   := factor (('*' | '/') factor)*
    factor := ('+' | '-') factor | primary
    primary := NUMBER | '(' expr ')'
"""

from __future__ import annotations


class CalcError(Exception):
    """Raised for malformed input or division by zero."""


# --- Tokenizer ---------------------------------------------------------------

# Token kinds: NUMBER, '+', '-', '*', '/', '(', ')'

def _tokenize(expr: str):
    tokens = []
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "+-*/()":
            tokens.append((ch, ch))
            i += 1
            continue
        if ch.isdigit() or ch == ".":
            start = i
            seen_dot = False
            while i < n and (expr[i].isdigit() or expr[i] == "."):
                if expr[i] == ".":
                    if seen_dot:
                        raise CalcError(
                            f"Malformed number with multiple dots at position {start}"
                        )
                    seen_dot = True
                i += 1
            text = expr[start:i]
            if text == ".":
                raise CalcError(f"Invalid number '.' at position {start}")
            try:
                value = float(text)
            except ValueError as exc:  # pragma: no cover - defensive
                raise CalcError(f"Invalid number '{text}'") from exc
            tokens.append(("NUMBER", value))
            continue
        raise CalcError(f"Unexpected character {ch!r} at position {i}")
    return tokens


# --- Parser / evaluator ------------------------------------------------------

class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (None, None)

    def _advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse(self) -> float:
        if not self.tokens:
            raise CalcError("Empty expression")
        value = self._expr()
        if self.pos != len(self.tokens):
            kind, _ = self._peek()
            raise CalcError(f"Unexpected token {kind!r} at position {self.pos}")
        return value

    def _expr(self) -> float:
        value = self._term()
        while True:
            kind, _ = self._peek()
            if kind == "+":
                self._advance()
                value += self._term()
            elif kind == "-":
                self._advance()
                value -= self._term()
            else:
                break
        return value

    def _term(self) -> float:
        value = self._factor()
        while True:
            kind, _ = self._peek()
            if kind == "*":
                self._advance()
                value *= self._factor()
            elif kind == "/":
                self._advance()
                divisor = self._factor()
                if divisor == 0:
                    raise CalcError("Division by zero")
                value /= divisor
            else:
                break
        return value

    def _factor(self) -> float:
        kind, _ = self._peek()
        if kind == "+":
            self._advance()
            return self._factor()
        if kind == "-":
            self._advance()
            return -self._factor()
        return self._primary()

    def _primary(self) -> float:
        kind, value = self._peek()
        if kind == "NUMBER":
            self._advance()
            return value
        if kind == "(":
            self._advance()
            inner = self._expr()
            close_kind, _ = self._peek()
            if close_kind != ")":
                raise CalcError("Missing closing parenthesis")
            self._advance()
            return inner
        if kind is None:
            raise CalcError("Unexpected end of expression")
        raise CalcError(f"Unexpected token {kind!r} at position {self.pos}")


def evaluate(expr: str) -> float:
    """Parse and evaluate an arithmetic expression, returning a float.

    Raises ``CalcError`` on malformed input or division by zero.
    """
    if not isinstance(expr, str):
        raise CalcError("Expression must be a string")
    tokens = _tokenize(expr)
    return _Parser(tokens).parse()


# --- Self-checks -------------------------------------------------------------

if __name__ == "__main__":
    def _approx(a: float, b: float, tol: float = 1e-9) -> bool:
        return abs(a - b) <= tol

    # Basic arithmetic
    assert _approx(evaluate("1 + 2"), 3.0)
    assert _approx(evaluate("7 - 3"), 4.0)
    assert _approx(evaluate("6 * 7"), 42.0)
    assert _approx(evaluate("8 / 2"), 4.0)

    # Precedence: * / bind tighter than + -
    assert _approx(evaluate("2 + 3 * 4"), 14.0)
    assert _approx(evaluate("2 * 3 + 4"), 10.0)
    assert _approx(evaluate("10 - 2 * 3"), 4.0)
    assert _approx(evaluate("1 + 8 / 2 - 3"), 2.0)

    # Left-to-right associativity
    assert _approx(evaluate("10 - 2 - 3"), 5.0)
    assert _approx(evaluate("100 / 5 / 2"), 10.0)
    assert _approx(evaluate("2 - 3 + 4"), 3.0)

    # Parentheses
    assert _approx(evaluate("(2 + 3) * 4"), 20.0)
    assert _approx(evaluate("2 * (3 + 4)"), 14.0)
    assert _approx(evaluate("((1 + 2) * (3 + 4))"), 21.0)
    assert _approx(evaluate("(1 + (2 * (3 + 4)))"), 15.0)

    # Decimals
    assert _approx(evaluate("3.5 + 1.5"), 5.0)
    assert _approx(evaluate("0.1 + 0.2"), 0.3)
    assert _approx(evaluate("2.5 * 4"), 10.0)
    assert _approx(evaluate(".5 + .5"), 1.0)
    assert _approx(evaluate("10.0 / 4"), 2.5)

    # Unary operators
    assert _approx(evaluate("-5"), -5.0)
    assert _approx(evaluate("-5 + 3"), -2.0)
    assert _approx(evaluate("3 * -2"), -6.0)
    assert _approx(evaluate("-(2 + 3)"), -5.0)
    assert _approx(evaluate("--5"), 5.0)
    assert _approx(evaluate("+7"), 7.0)

    # Whitespace handling
    assert _approx(evaluate("   1   +   2   "), 3.0)
    assert _approx(evaluate("\t2*\n3\r"), 6.0)
    assert _approx(evaluate("2+3"), 5.0)

    # Error cases
    def _expect_error(expression: str):
        try:
            evaluate(expression)
        except CalcError:
            return
        raise AssertionError(f"Expected CalcError for {expression!r}")

    _expect_error("1 / 0")          # division by zero
    _expect_error("5 / (3 - 3)")    # division by zero via parens
    _expect_error("")               # empty
    _expect_error("   ")            # whitespace only
    _expect_error("1 +")            # dangling operator
    _expect_error("* 3")            # leading binary operator
    _expect_error("(1 + 2")         # unbalanced open paren
    _expect_error("1 + 2)")         # unbalanced close paren
    _expect_error("1 2")            # missing operator
    _expect_error("1.2.3")          # malformed number
    _expect_error("1 + a")          # invalid character
    _expect_error("()")             # empty parens
    _expect_error(".")              # lone dot

    print("All self-checks passed.")
