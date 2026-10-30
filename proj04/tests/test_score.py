import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEDIA = os.path.join(HERE, "pedia.py")


def run_score():
    return subprocess.run(
        [sys.executable, PEDIA, "score"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        cwd=HERE,
    )


class TestScore(unittest.TestCase):
    def test_summary_line_present(self):
        r = run_score()
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        self.assertTrue(lines, "no output")
        self.assertTrue(lines[-1].startswith("covered "), lines[-1])
        self.assertIn("of 30", lines[-1])

    def test_exit_code_matches_status(self):
        r = run_score()
        last = [l for l in r.stdout.splitlines() if l.strip()][-1]
        if "PASS" in last and "below" not in last:
            self.assertEqual(r.returncode, 0)
        else:
            self.assertEqual(r.returncode, 1)

    def test_same_output_each_run(self):
        self.assertEqual(run_score().stdout, run_score().stdout)


if __name__ == "__main__":
    unittest.main()
