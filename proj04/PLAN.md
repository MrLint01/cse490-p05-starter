# PLAN: pedia.py

## Decisions (from your answers)
- profile.json: subjects = all eleven subjects in spec order; results = 5. Already written.
- Matching: a query word counts when it appears in the title or the text. A title match counts 3 times a text match. Ties go to the article whose subject appears earlier in profile.json subjects.
- Index file: index.json (approved), stored next to pedia.py.

## Files
- profile.json: written (done). The earlier score check failed only because pedia.py does not exist yet.
- pedia.py: new. Standard library only.
  - search "<query>": ranks articles by the scoring above, prints the top `results` as a numbered list (title and subject), then asks "Read which? [1-N, Enter for none]" only when stdin is a terminal. A number prints the summary (first paragraph of simple, else en), then title and subject.
  - score: runs the same ranking with the subject preference off, over questions.csv (question, answer title). Prints one line per miss (question, answer, first title), then covered, total, and PASS or below target. Exit 0 on PASS (27 of 30), else 1.
  - Index: built on first use when missing, from articles/all.jsonl.gz, read line by line with gzip.open(..., "rt", encoding="utf-8"), written to index.json.
- tests/test_search.py: new. Tests the search command.
- tests/test_score.py: new. Tests the score command.
- tests/test_subjects.py: new. Tests the profile key `subjects`.
- tests/test_results.py: new. Tests the profile key `results`.

## Verification
- Run `python3 pedia.py score` after each write. Report the covered count and PASS or below target only from that output.
- CHECK runs automatically after each write. Do not claim a test passes until its output has been read.