const TABLE = [
  [1000, "M"], [900, "CM"], [500, "D"], [400, "CD"],
  [100, "C"], [90, "XC"], [50, "L"], [40, "XL"],
  [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"],
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
  for (let i = 0; i < s.length; i++) {
    const cur = map[s[i]];
    const next = map[s[i + 1]];
    if (next && cur < next) total -= cur;
    else total += cur;
  }
  return total;
}

const arg = process.argv[2];
if (/^\d+$/.test(arg)) {
  console.log(toRoman(parseInt(arg, 10)));
} else {
  console.log(toNumber(arg.toUpperCase()));
}
