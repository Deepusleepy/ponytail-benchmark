import sys


def fmt(x):
    return str(int(x)) if x == int(x) else str(x)


def scale(values, factor):
    return [v * factor for v in values]


def clamp(values, low, high):
    return [low if v < low else high if v > high else v for v in values]


def main(argv):
    command = argv[0]
    if command == "scale":
        factor = float(argv[1])
        values = [float(a) for a in argv[2:]]
        result = scale(values, factor)
        print(" ".join(fmt(v) for v in result))
    elif command == "clamp":
        low = float(argv[1])
        high = float(argv[2])
        values = [float(a) for a in argv[3:]]
        result = clamp(values, low, high)
        print(" ".join(fmt(v) for v in result))
    else:
        print("unknown command: %s" % command, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
