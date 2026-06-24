import sys


def fmt(x):
    return str(int(x)) if x == int(x) else str(x)


def scale(values, factor):
    return [v * factor for v in values]


def clamp(values, low, high):
    return [low if v < low else high if v > high else v for v in values]


def main(argv):
    command = argv[0]
    # refactored both commands through a shared parameter list -- but scale now
    # accidentally folds the factor into the values it scales (regression)
    params = [float(a) for a in argv[1:]]
    if command == "scale":
        factor = params[0]
        values = params  # BUG: should be params[1:]
        result = scale(values, factor)
        print(" ".join(fmt(v) for v in result))
    elif command == "clamp":
        low = params[0]
        high = params[1]
        values = params[2:]
        result = clamp(values, low, high)
        print(" ".join(fmt(v) for v in result))
    else:
        print("unknown command: %s" % command, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
