// plausible-but-wrong: additive only, no subtractive forms (4 -> "IIII", and
// decode just sums every symbol so "IV" reads as 6)
const TABLE = [
  [1000, "M"], [500, "D"], [100, "C"], [50, "L"], [10, "X"], [5, "V"], [1, "I"],
];

function toRoman(n) {
  let out = "";
  for (const [value, sym] of TABLE) {
    while (n >= value) {
      out += sym;
      n -= value;
    }
  }
  return out;
}

function toNumber(s) {
  const map = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
  let total = 0;
  for (const ch of s) total += map[ch];
  return total;
}

const arg = process.argv[2];
if (/^\d+$/.test(arg)) {
  console.log(toRoman(parseInt(arg, 10)));
} else {
  console.log(toNumber(arg.toUpperCase()));
}
