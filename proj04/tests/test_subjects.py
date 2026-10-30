import os
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE = os.path.join(HERE, "profile.json")

EXPECTED = [
    "People", "History", "Geography", "Arts", "Philosophy and religion",
    "Everyday life", "Society and social sciences",
    "Biological and health sciences", "Physical sciences",
    "Technology", "Mathematics",
]


class TestSubjectsKey(unittest.TestCase):
    def setUp(self):
        import json
        with open(PROFILE, encoding="utf-8") as f:
            self.profile = json.load(f)

    def test_subjects_present_and_list(self):
        self.assertIn("subjects", self.profile)
        self.assertIsInstance(self.profile["subjects"], list)

    def test_subjects_are_all_eleven_in_spec_order(self):
        self.assertEqual(self.profile["subjects"], EXPECTED)

    def test_subjects_have_no_duplicates(self):
        s = self.profile["subjects"]
        self.assertEqual(len(s), len(set(s)))


if __name__ == "__main__":
    unittest.main()
