const fs = require("fs");

const wanted = process.argv[2];
const text = fs.readFileSync(0, "utf8");

const lines = text.trim().split("\n");
const header = lines[0].split(",");
const idx = header.indexOf(wanted);

for (const line of lines.slice(1)) {
  const cells = line.split(",");
  console.log(cells[idx].trim());
}
