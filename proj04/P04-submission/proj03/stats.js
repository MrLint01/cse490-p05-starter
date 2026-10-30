// Reads scores.csv and prints the class average and the top scorer.
const fs = require("fs");

const lines = fs.readFileSync("scores.csv", "utf-8").split(/\r?\n/).filter((l) => l.trim() !== "");
const header = lines[0].split(",");
const rows = lines.slice(1).map((line) => {
  const values = line.split(",");
  const row = {};
  header.forEach((key, i) => {
    row[key] = values[i];
  });
  return row;
});

const scores = rows.map((r) => parseInt(r.score, 10));
const total = scores.reduce((a, b) => a + b, 0);
const average = total / scores.length;

// Keep the first row with the highest score, matching Python's max().
let top = rows[0];
for (const r of rows) {
  if (parseInt(r.score, 10) > parseInt(top.score, 10)) {
    top = r;
  }
}

console.log(`average: ${average.toFixed(1)}`);
console.log(`top: ${top.name} (${top.score})`);
