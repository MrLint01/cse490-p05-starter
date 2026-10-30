# Reads scores.csv and prints the class average and the top scorer.
import csv

rows = list(csv.DictReader(open("scores.csv", encoding="utf-8")))
scores = [int(r["score"]) for r in rows]
average = sum(scores) / len(scores)
top = max(rows, key=lambda r: int(r["score"]))

print(f"average: {average:.1f}")
print(f"top: {top['name']} ({top['score']})")
