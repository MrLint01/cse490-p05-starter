import json
import os
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE = os.path.join(HERE, "profile.json")


class TestResultsKey(unittest.TestCase):
    def setUp(self):
        with open(PROFILE, encoding="utf-8") as f:
            self.profile = json.load(f)

    def test_results_present(self):
        self.assertIn("results", self.profile)

    def test_results_is_positive_integer(self):
        r = self.profile["results"]
        self.assertIsInstance(r, int)
        self.assertGreater(r, 0)

    def test_results_is_five(self):
        self.assertEqual(self.profile["results"], 5)


if __name__ == "__main__":
    unittest.main()
