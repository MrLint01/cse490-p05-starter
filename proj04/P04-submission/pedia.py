import csv
import gzip
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARTICLES = os.path.join(HERE, "articles", "all.jsonl.gz")
INDEX = os.path.join(HERE, "index.json")
PROFILE = os.path.join(HERE, "profile.json")
QUESTIONS = os.path.join(HERE, "questions.csv")
TARGET = 27
TITLE_WEIGHT = 3
TEXT_WEIGHT = 1
FULL_TITLE_BONUS = 5


def tokens(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


def build_index():
    docs = []
    with gzip.open(ARTICLES, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            a = json.loads(line)
            docs.append({
                "id": a.get("id"),
                "title": a.get("title") or "",
                "subject": a.get("subject") or "",
                "en": a.get("en") or "",
                "simple": a.get("simple"),
                "title_tokens": sorted(tokens(a.get("title"))),
                "text_tokens": sorted(tokens(a.get("en")) | tokens(a.get("simple"))),
            })
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(docs, f)
    return docs


def load_index():
    if not os.path.exists(INDEX):
        return build_index()
    with open(INDEX, encoding="utf-8") as f:
        return json.load(f)


def load_profile():
    with open(PROFILE, encoding="utf-8") as f:
        return json.load(f)


def doc_freq(docs):
    df = {}
    for d in docs:
        for t in set(d["title_tokens"]) | set(d["text_tokens"]):
            df[t] = df.get(t, 0) + 1
    return df


def rank(query, docs, subject_pref):
    terms = tokens(query)
    if not terms:
        return []
    n_docs = len(docs)
    df = doc_freq(docs)
    idf = {t: math.log(n_docs / df[t]) for t in terms if df.get(t, 0) > 0}
    subjects = load_profile().get("subjects", []) if subject_pref else []
    rank_of = {s: i for i, s in enumerate(subjects)}
    scored = []
    for d in docs:
        tt = set(d["title_tokens"])
        xt = set(d["text_tokens"])
        s = 0.0
        for t, w in idf.items():
            if t in tt:
                s += TITLE_WEIGHT * w
            if t in xt:
                s += TEXT_WEIGHT * w
        if tt and tt <= terms:
            s += FULL_TITLE_BONUS
        if s > 0:
            pref = rank_of.get(d["subject"], len(rank_of)) if subject_pref else 0
            scored.append((-s, pref, d["title"], d))
    scored.sort(key=lambda x: (x[0], x[1], x[2]))
    return [x[3] for x in scored]


def summary(d):
    text = d["simple"] if d.get("simple") else d["en"]
    para = (text or "").strip().split("\n\n")[0].strip()
    return para


def cmd_search(query):
    docs = load_index()
    n = load_profile().get("results", 5)
    hits = rank(query, docs, True)[:n]
    if not hits:
        print("No results.")
        return
    for i, d in enumerate(hits, 1):
        print(f"{i}. {d['title']} ({d['subject']})")
    if not sys.stdin.isatty():
        return
    choice = input(f"Read which? [1-{len(hits)}, Enter for none] ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(hits):
        d = hits[int(choice) - 1]
        print(summary(d))
        print(f"{d['title']} | {d['subject']}")


def cmd_score():
    docs = load_index()
    with open(QUESTIONS, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))[1:]
    rows = [r for r in rows if len(r) >= 2]
    covered = 0
    for q, ans in rows:
        hits = rank(q, docs, False)
        first = hits[0]["title"] if hits else "(none)"
        if first == ans:
            covered += 1
        else:
            print(f"MISS | question: {q} | answer: {ans} | first: {first}")
    total = len(rows)
    status = "PASS" if covered >= TARGET else "below target"
    print(f"covered {covered} of {total}: {status}")
    return 0 if covered >= TARGET else 1


def main(argv):
    if len(argv) >= 2 and argv[1] == "search" and len(argv) >= 3:
        cmd_search(" ".join(argv[2:]))
        return 0
    if len(argv) >= 2 and argv[1] == "score":
        return cmd_score()
    print('usage: pedia.py search "<query>" | pedia.py score')
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
