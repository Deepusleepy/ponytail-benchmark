def add(a, b):
    return a + b


def average(numbers):
    return sum(numbers) / len(numbers)


if __name__ == '__main__':
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert average([1, 2, 3, 4]) == 2.5
    assert average([10]) == 10
    assert average([2, 4, 6]) == 4
    print('All checks passed.')
