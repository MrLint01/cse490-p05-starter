import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEDIA = os.path.join(HERE, "pedia.py")


def run_search(query):
    # stdin is DEVNULL, so search is not a terminal and never prompts.
    return subprocess.run(
        [sys.executable, PEDIA, "search", query],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        cwd=HERE,
    )


class TestSearch(unittest.TestCase):
    def test_lists_numbered_results(self):
        r = run_search("history")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        self.assertTrue(lines, "no output")
        self.assertTrue(lines[0].startswith("1. "), lines[0])

    def test_result_count_matches_profile(self):
        r = run_search("history")
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        self.assertLessEqual(len(lines), 5)

    def test_no_prompt_when_not_terminal(self):
        r = run_search("history")
        self.assertNotIn("Read which?", r.stdout)

    def test_same_query_same_output(self):
        a = run_search("river")
        b = run_search("river")
        self.assertEqual(a.stdout, b.stdout)


if __name__ == "__main__":
    unittest.main()
