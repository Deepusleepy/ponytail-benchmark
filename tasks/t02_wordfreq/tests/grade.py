"""Over-build task grader (word frequency). Correctness is a FLOOR both lean and
bloated solutions pass; the size meter (in the gate) discriminates. Core tier only.

Core behaviors from the prompt goal:
  - "reads text on standard input and prints the ten most frequent words along with
     how many times each appears, most frequent first"
  - "Treat words case-insensitively"
Output shape is left open, so we parse each line for a word token and an integer count
and assert invariants (membership, counts, ordering, top-10 cutoff), not literal strings.
"""
import glob, json, os, re, subprocess, sys


def _is_test_file(path):
    base = os.path.basename(path).lower()
    stem = os.path.splitext(base)[0]
    return (stem.startswith("test_") or stem.startswith("test-") or stem.endswith("_test")
            or stem.endswith("-test") or ".test." in base or ".spec." in base
            or stem in ("conftest", "setup", "__init__"))


def pick_sources(soldir, exts):
    """Return runnable source files, putting the real entry point first.

    A model may legitimately ship its own unit-test file next to the solution
    (e.g. test_wordfreq.py). The grader must drive the actual script, not the
    test module, regardless of alphabetical order. We drop obvious test files;
    if that empties the list (only a test file was produced) we keep them.
    """
    files = []
    for ext in exts:
        files += glob.glob(os.path.join(soldir, "*" + ext))
    files = sorted(set(files))
    non_test = [f for f in files if not _is_test_file(f)]
    return non_test or files


soldir = sys.argv[1]
pys = pick_sources(soldir, [".py"])
subs = []


def run(text):
    cp = subprocess.run([sys.executable, pys[0]], input=text,
                        capture_output=True, text=True, timeout=15)
    return cp.stdout


def parse_pairs(out):
    """Return list of (word_lower, count) in the order produced.
    Tolerant of formats and of WORD/COUNT ordering on the line, e.g.:
        'the 9', 'the,9', 'the   9', 'the: 9', 'the\t9'   (word first)
        '9 the', '9\tthe', '9,the'                        (count first)
        JSON objects, CSV/table rows, "9. the", "the - 9", etc.
    The prompt fixes only that each line carries a word and its count; it does NOT
    fix which comes first or the separator. So we identify the two roles by KIND,
    not position: the count is the standalone integer token; the word is the token
    that contains at least one letter (words may also contain digits, e.g. "w01",
    "2024", or apostrophes, e.g. "don't").
    """
    pairs = []
    for line in out.splitlines():
        s = line.strip()
        if not s:
            continue
        # skip an obvious header row like "word,count" / "word count" / "count,word"
        if re.match(r"^[\"']?(word|count|rank|#)[\"']?\s*[,:|\t ]+\s*[\"']?(word|count)\b", s, re.I):
            continue
        # JSON-object form first, order-independent: {"word": "the", "count": 9}
        mw = re.search(r'"?word"?\s*[:=]\s*"([^"]+)"', s, re.I)
        mc = re.search(r'"?count"?\s*[:=]\s*(\d+)', s, re.I)
        if mw and mc:
            pairs.append((mw.group(1).lower(), int(mc.group(1))))
            continue
        # General case: split into word-ish tokens, then assign roles by kind.
        toks = re.findall(r"[A-Za-z0-9']+", s)
        if not toks:
            continue
        # the word: first token containing a letter (handles "w01", "don't", "2024 hits"...)
        word = next((t for t in toks if re.search(r"[A-Za-z]", t)), None)
        # the count: an all-digit token that is not the chosen word token.
        # take the last all-digit token to be robust to a leading rank/index column.
        digit_toks = [t for t in toks if re.fullmatch(r"\d+", t)]
        if word is None or not digit_toks:
            continue
        pairs.append((word.lower(), int(digit_toks[-1])))
    return pairs


def as_dict(pairs):
    return {w: c for w, c in pairs}


if not pys:
    print(json.dumps({"subcases": [{"name": "produced_script", "tier": "core", "ok": False}]}))
    sys.exit(0)

# --- Case 1: basic frequency + ordering ---------------------------------------
# apple x4, banana x3, cherry x2, date x1
text1 = ("apple apple apple apple banana banana banana "
         "cherry cherry date\n")
pairs1 = parse_pairs(run(text1))
d1 = as_dict(pairs1)
ok_counts = (d1.get("apple") == 4 and d1.get("banana") == 3 and
             d1.get("cherry") == 2 and d1.get("date") == 1)
subs.append({"name": "counts_correct", "tier": "core", "ok": ok_counts})

# most frequent first: apple before banana before cherry
order = [w for w, _ in pairs1]
def before(a, b):
    return a in order and b in order and order.index(a) < order.index(b)
ok_order = before("apple", "banana") and before("banana", "cherry")
subs.append({"name": "most_frequent_first", "tier": "core", "ok": ok_order})

# --- Case 2: case-insensitive folding -----------------------------------------
text2 = "The the THE dog Dog cat\n"
d2 = as_dict(parse_pairs(run(text2)))
# "the" appears 3x regardless of case, "dog" 2x, "cat" 1x
ok_ci = (d2.get("the") == 3 and d2.get("dog") == 2 and d2.get("cat") == 1)
subs.append({"name": "case_insensitive", "tier": "core", "ok": ok_ci})

# --- Case 3: only the top ten are shown ---------------------------------------
# 15 distinct words with strictly descending frequencies w01..w15
parts = []
for i in range(1, 16):
    parts.extend(["w%02d" % i] * (16 - i))  # w01 x15 ... w15 x1
text3 = " ".join(parts) + "\n"
pairs3 = parse_pairs(run(text3))
d3 = as_dict(pairs3)
top_ten = ["w%02d" % i for i in range(1, 11)]
excluded = ["w%02d" % i for i in range(11, 16)]
ok_topn = (len(pairs3) == 10 and
           all(d3.get(w) == (16 - int(w[1:])) for w in top_ten) and
           all(w not in d3 for w in excluded))
subs.append({"name": "top_ten_only", "tier": "core", "ok": ok_topn})

print(json.dumps({"subcases": subs}))
