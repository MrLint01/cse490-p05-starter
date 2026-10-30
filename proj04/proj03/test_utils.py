# Tests for utils.py.
# Run with: python -m unittest test_utils
import unittest

from utils import clamp, is_palindrome, median, slugify


class TestUtils(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_clamp(self):
        self.assertEqual(clamp(15, 0, 10), 10)
        self.assertEqual(clamp(-3, 0, 10), 0)
        self.assertEqual(clamp(7, 0, 10), 7)

    def test_median(self):
        self.assertEqual(median([3, 1, 2]), 2)
        self.assertEqual(median([1, 2, 3, 4]), 2.5)

    def test_is_palindrome(self):
        self.assertTrue(is_palindrome("A man, a plan, a canal: Panama"))
        self.assertFalse(is_palindrome("Hello"))


if __name__ == "__main__":
    unittest.main()
