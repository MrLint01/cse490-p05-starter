# pedia.py

A search over about a thousand Wikipedia articles, offline, shaped to its reader.
No model is involved; standard library only. The same query with the same
profile always gives the same output.

## Commands

    python pedia.py search "<query>"   the top articles, best first, numbered,
                                       shaped by profile.json; then it asks which
                                       one to read and prints that article's summary
    python pedia.py score              right first answers over questions.csv

search prints its results as a numbered list, one title per line with its subject,
then asks "Read which? [1-N, Enter for none]". A number prints that article's
summary: the first paragraph of its Simple English text when the article has one,
else the first paragraph of its English text, then the article's title and subject
on a last line. Enter, or any other input, prints nothing more. When search's
input is not a terminal it never asks. score runs search's ranking directly and
never its prompt.

score reads questions.csv (question, answer title), runs search for each question
with the profile's subject preference switched off, and counts the questions whose
first result is the answer. For every miss it prints one line: the question, the
answer, and the title that came first instead. Then it prints covered, total, and
PASS or below target. Exit 0 on PASS, 1 below it. If an index is needed, every
command builds it when it is missing.

Target: 27 of the 30 public questions.

## articles/

    articles/all.jsonl.gz   the articles, gzip-compressed: about 12 MB of text
                            as one article per line, a JSON object with the keys
                            id, title, subject, en (the English text) and simple
                            (the Simple English text, or null); each text about
                            1,200 words. Read it with gzip.open(path, "rt",
                            encoding="utf-8") from the standard library, line by
                            line; never unpack it to disk.
    articles/README.md      where the articles came from, their license, and one
                            line of the file, shortened

Subjects: People, History, Geography, Arts, Philosophy and religion, Everyday
life, Society and social sciences, Biological and health sciences, Physical
sciences, Technology, Mathematics.

## profile.json

The reader's answers from plan mode, read by search. Two keys:

    subjects    the subjects that win when two articles tie
    results     how many results search shows

## Rules

- Standard library only. No network. pedia.py never downloads anything.
- Deterministic: the same query and the same profile give the same output.
- questions.csv is read only by score. A program that reads it anywhere else, or
  special-cases its questions, fails the hidden questions and is flagged.
- More questions of the same shape, with answers from the same articles, are held
  back and run after submission.
