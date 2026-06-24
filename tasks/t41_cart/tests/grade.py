"""Brownfield grader. CORE = applying a discount code reduces the amount owed by that
percentage. IMPLICIT = the pre-existing cart (add items by name/price/quantity, then
total) still works with no discount applied (regression check). The antiref adds the
discount feature but refactors add() to take an object, breaking the existing
add(name, price, quantity) callers -- it passes CORE and fails IMPLICIT. Driven
black-box by requiring the produced module from a node driver.
"""
import glob, json, os, subprocess, sys

soldir = os.path.abspath(sys.argv[1])
# Brownfield: require the model's EDITED module. The entry point is the seed file
# cart.js; target it explicitly so a sibling cart.test.js / spec can't be picked first.
all_js = sorted(glob.glob(os.path.join(soldir, "*.js")) + glob.glob(os.path.join(soldir, "*.mjs"))
                + glob.glob(os.path.join(soldir, "*.cjs")))
non_test = [p for p in all_js if not (".test." in os.path.basename(p) or ".spec." in os.path.basename(p))]
named = [p for p in all_js if os.path.basename(p) in ("cart.js", "cart.mjs", "cart.cjs")]
jss = named or non_test or all_js
subs = []

if not jss:
    print(json.dumps({"subcases": [{"name": "produced_module", "tier": "core", "ok": False}]}))
    sys.exit(0)

modpath = jss[0].replace("\\", "\\\\")

# A node driver that exercises the cart and prints one JSON result per scenario.
# (The module path is substituted via __MODPATH__ to avoid %-format escaping issues
# with the literal "%" signs in the comments below.)
#
# The prompt only asks to "apply a code that takes a percentage off"; it never pins the
# METHOD NAME or its return value. So we DISCOVER the discount-applying method on the
# Cart instance instead of hardcoding applyDiscount(): we try a list of plausible names
# (applyDiscount/applyCode/applyDiscountCode/...), and if none exists we probe every
# 1-arg method to find the one that, given a known code, actually changes the total.
# The known codes (SAVE10/SAVE25/HALFOFF) ship in the seed, so a correct solution keeps
# them. total() is read as a number, tolerating a numeric-string return ("90", "90.00").
driver = r"""
const path = "__MODPATH__";
const mod = require(path);
const Cart = mod.Cart || mod.default || mod;
function make() { return new Cart(); }
const out = {};

function num(v) {
  if (typeof v === "number") return v;
  if (typeof v === "string") { const n = Number(v.replace(/[^0-9.\-]/g, "")); return isNaN(n) ? null : n; }
  if (v && typeof v === "object") {
    for (const k of ["total", "amount", "due", "value", "owed", "grandTotal"]) {
      if (typeof v[k] === "number") return v[k];
    }
  }
  return null;
}

function totalOf(c) {
  if (typeof c.total === "function") return num(c.total());
  if (typeof c.getTotal === "function") return num(c.getTotal());
  if (typeof c.total === "number") return num(c.total);
  if (typeof c.amountDue === "function") return num(c.amountDue());
  return null;
}

const CANDIDATES = [
  "applyDiscount", "applyCode", "applyDiscountCode", "applyPromo", "applyPromoCode",
  "applyCoupon", "discount", "setDiscount", "addDiscount", "useCode", "redeem", "apply",
];

// Find a method name that, applied with a known code, reduces the total. Discover it
// once on a throwaway cart so each scenario can call it directly.
function findDiscountMethod() {
  const proto = Object.getPrototypeOf(make());
  const names = new Set([
    ...CANDIDATES,
    ...Object.getOwnPropertyNames(proto),
  ]);
  for (const name of names) {
    try {
      const c = make();
      if (typeof c[name] !== "function") continue;
      // A 100.00 order with SAVE10 must owe 90.00 after the method runs. Compare to the
      // known expected value (not to a "before" snapshot, which can be NaN in a broken
      // cart whose total() assumes a discount is always set).
      c.add("probe", 100, 1);
      c[name]("SAVE10");
      const after = totalOf(c);
      if (after !== null && Number.isFinite(after) && Math.abs(after - 90) < 1e-6) return name;
    } catch (e) { /* try next */ }
  }
  return null;
}

const DM = findDiscountMethod();
out._method = DM;

function applyAndTotal(items, code) {
  const c = make();
  for (const [n, p, q] of items) c.add(n, p, q);
  if (DM) c[DM](code);
  return totalOf(c);
}

// CORE: 10% off a 100.00 order -> 90.00
try { out.core_save10 = applyAndTotal([["widget", 50, 2]], "SAVE10"); }
catch (e) { out.core_save10 = "ERR:" + e.message; }

// CORE: 25% off an 80.00 order -> 60.00
try { out.core_save25 = applyAndTotal([["a", 40, 1], ["b", 40, 1]], "SAVE25"); }
catch (e) { out.core_save25 = "ERR:" + e.message; }

// CORE: 50% off a 100.00 order -> 50.00
try { out.core_half = applyAndTotal([["x", 10, 10]], "HALFOFF"); }
catch (e) { out.core_half = "ERR:" + e.message; }

// IMPLICIT: existing add + total, no discount
try {
  const c = make();
  c.add("apple", 1.5, 2);
  c.add("bread", 3, 1);
  out.impl_total = totalOf(c);
} catch (e) { out.impl_total = "ERR:" + e.message; }

// IMPLICIT: existing add + total, integer-priced order, no discount
try {
  const c = make();
  c.add("pen", 2, 3);
  c.add("pad", 5, 4);
  out.impl_total2 = totalOf(c);
} catch (e) { out.impl_total2 = "ERR:" + e.message; }

console.log(JSON.stringify(out));
""".replace("__MODPATH__", modpath)

driverpath = os.path.join(os.getcwd(), "_cart_driver.js")
with open(driverpath, "w", encoding="utf-8") as f:
    f.write(driver)

cp = subprocess.run(["node", driverpath], capture_output=True, text=True, timeout=20)
data = None
for line in reversed(cp.stdout.strip().splitlines()):
    try:
        data = json.loads(line)
        break
    except Exception:
        continue
if data is None:
    data = {}


def close(v, exp):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v - exp) < 1e-6


subs.append({"name": "discount_save10", "tier": "core", "ok": close(data.get("core_save10"), 90.0)})
subs.append({"name": "discount_save25", "tier": "core", "ok": close(data.get("core_save25"), 60.0)})
subs.append({"name": "discount_halfoff", "tier": "core", "ok": close(data.get("core_half"), 50.0)})
subs.append({"name": "existing_total_fractional", "tier": "implicit", "ok": close(data.get("impl_total"), 6.0)})
subs.append({"name": "existing_total_integer", "tier": "implicit", "ok": close(data.get("impl_total2"), 26.0)})

print(json.dumps({"subcases": subs}))
