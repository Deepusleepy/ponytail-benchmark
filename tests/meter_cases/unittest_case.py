import unittest

def solve(x):
    return x + 1

class SolveTest(unittest.TestCase):
    def test_one(self):
        self.assertEqual(solve(1), 2)