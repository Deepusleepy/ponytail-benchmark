import re


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[\s_]+", "-", text)        # spaces/underscores -> hyphen
    text = re.sub(r"[^a-z0-9-]", "", text)     # drop disallowed chars
    text = re.sub(r"-+", "-", text)            # collapse hyphens
    return text.strip("-")


if __name__ == "__main__":
    assert slugify("  Hello, World!  ") == "hello-world"
    assert slugify("foo_bar baz") == "foo-bar-baz"
    assert slugify("C++ & Python!") == "c-python"
    assert slugify("already-a-slug") == "already-a-slug"
    assert slugify("multiple   spaces") == "multiple-spaces"
    assert slugify("") == ""                    # empty
    assert slugify("!@#$%^&*()") == ""          # all symbols
    assert slugify("---x---") == "x"
    print("ok")
