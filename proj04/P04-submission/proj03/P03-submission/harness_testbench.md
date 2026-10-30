# Harness testbench

Four everyday chores. Give each one to your harness, watch it work, and keep
the chat log running. Each task leaves a file the grader checks.

## 1. Untangle the graph

Done in step 7: untangle/moves.json reaches zero crossings. Nothing to do
here but confirm it, and note your score.

Check: `python untangle/check.py untangle/graph.json untangle/moves.json`
prints `"ok": true` and your turns.

## 2. Port a program to another language

stats.py reads scores.csv and prints the class average and the top scorer.

Ask your harness to rewrite it in JavaScript as stats.js, then run both.

Check: `node stats.js` prints the same two lines as `python stats.py`.

## 3. Write the missing tests

utils.py has four functions. test_utils.py is empty.

Ask your harness to write one test per function and run them until all four
pass. One function has a bug; the test for it can only pass once the function
is fixed. Do not change a test to make it pass.

Check: `python -m unittest test_utils` shows `Ran 4 tests` and `OK`.

## 4. Test a program against its documentation

inventory.py is a small module with four functions: add, remove, quantity,
total_value. Its docstring states the rules they follow. One function breaks a
rule.

Ask your harness to write test_inventory.py that checks every function against
the docstring, run it, and tell you which rule is broken.

Check: `python test_inventory.py` runs all four checks and names the broken rule.
