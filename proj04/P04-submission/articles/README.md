# articles

About a thousand Wikipedia articles, the vital articles at levels 1 to 3, as plain text:
the English article and, where one exists, the Simple English article, each cut to about
1,200 words. Fetched from the Wikimedia API by the course on 2026-10-19 for CSE 490's
Project 4. One article per line in all.jsonl.gz, gzip-compressed: id, title, subject, en, simple.

Unpacked it is about 12 MB, far more than a model's context holds, which is why it ships compressed: a program reads it
line by line with gzip.open(path, "rt", encoding="utf-8"), and an agent reads this README and SPEC.md for its shape, never
the file itself. The first line, shortened:

    {"id": "0001", "title": "Abstract art", "subject": "Arts", "en": "Abstract art uses visual language of shape, form, color, and line to create a composition ...", "simple": "Abstract art is modern art which does not represent images o ..."}

Text from Wikipedia (https://en.wikipedia.org) and Simple English Wikipedia
(https://simple.wikipedia.org), licensed under the Creative Commons Attribution-ShareAlike
4.0 License (https://creativecommons.org/licenses/by-sa/4.0/). Each article's title is
its page title; the full article and its history are at
https://en.wikipedia.org/wiki/<title>.
