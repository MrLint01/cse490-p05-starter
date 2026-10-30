# Runs stats.py and stats.js, captures their stdout, and compares them.
import subprocess
import sys


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"command failed: {cmd}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout


py_out = run([sys.executable, "stats.py"])
js_out = run(["node", "stats.js"])

print("--- stats.py ---")
print(py_out, end="")
print("--- stats.js ---")
print(js_out, end="")

if py_out == js_out:
    print("MATCH: outputs are identical")
else:
    print("MISMATCH: outputs differ")
    sys.exit(1)
