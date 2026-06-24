const fs = require("fs");

const wanted = process.argv[2];
const text = fs.readFileSync(0, "utf8");

const lines = text.split(/\r?\n/).filter((l) => l.length > 0);
if (lines.length === 0) {
  // nothing piped in -> nothing to print
  process.exit(0);
}

const header = lines[0].split(",").map((h) => h.trim());
const idx = header.indexOf(wanted);
if (idx === -1) {
  // the requested column isn't in this file -> say so, don't print garbage
  process.stderr.write(`column not found: ${wanted}\n`);
  process.exit(1);
}

for (const line of lines.slice(1)) {
  const cells = line.split(",");
  // a short row simply has no value in that column -> print blank, don't crash
  const cell = idx < cells.length ? cells[idx].trim() : "";
  console.log(cell);
}
