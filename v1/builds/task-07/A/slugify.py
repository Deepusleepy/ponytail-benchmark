"""slugify: convert arbitrary text into a URL-friendly slug.

Rules:
- lowercase the text
- spaces and underscores become single hyphens
- remove characters that are not a-z, 0-9, or hyphen
- collapse consecutive hyphens into one
- strip leading/trailing hyphens
"""

import re


def slugify(text: str) -> str:
    """Return a URL-friendly slug for ``text``.

    Example:
        >>> slugify("  Hello, World!  ")
        'hello-world'
    """
    # Lowercase first so the character filter only needs a-z.
    text = text.lower()
    # Spaces and underscores act as word separators -> hyphens.
    text = re.sub(r"[\s_]+", "-", text)
    # Drop anything that is not a lowercase letter, digit, or hyphen.
    text = re.sub(r"[^a-z0-9-]", "", text)
    # Collapse runs of hyphens (created by removals or input) into one.
    text = re.sub(r"-{2,}", "-", text)
    # Remove any leading/trailing hyphens.
    text = text.strip("-")
    return text


if __name__ == "__main__":
    # Normal case from the task description.
    assert slugify("  Hello, World!  ") == "hello-world"

    # Basic lowercasing and single-space handling.
    assert slugify("Hello World") == "hello-world"

    # Underscores become hyphens.
    assert slugify("hello_world") == "hello-world"

    # Mixed spaces and underscores collapse to a single hyphen.
    assert slugify("hello __  world") == "hello-world"

    # Punctuation is removed entirely (not turned into hyphens).
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("C++ & Python: A Guide") == "c-python-a-guide"

    # Digits are preserved.
    assert slugify("Top 10 Movies of 2024") == "top-10-movies-of-2024"

    # Existing hyphens are kept but collapsed and trimmed.
    assert slugify("--already--slugged--") == "already-slugged"
    assert slugify("a---b") == "a-b"

    # Leading/trailing separators are stripped.
    assert slugify("___leading_and_trailing___") == "leading-and-trailing"
    assert slugify("!!!Wow!!!") == "wow"

    # Edge case: empty string.
    assert slugify("") == ""

    # Edge case: whitespace-only string.
    assert slugify("    ") == ""

    # Edge case: all symbols / nothing valid remains.
    assert slugify("!@#$%^&*()") == ""
    assert slugify("---") == ""

    print("All slugify self-checks passed.")
