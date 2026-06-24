import sys

# plausible-but-wrong: lowercase letters before uppercase
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode(n):
    if n == 0:
        return ALPHABET[0]
    out = []
    while n > 0:
        n, r = divmod(n, 62)
        out.append(ALPHABET[r])
    return "".join(reversed(out))


def decode(s):
    n = 0
    for ch in s:
        n = n * 62 + ALPHABET.index(ch)
    return n


mode, value = sys.argv[1], sys.argv[2]
if mode == "encode":
    print(encode(int(value)))
elif mode == "decode":
    print(decode(value))
