"""Over-build task grader (FAQ page). Correctness is a FLOOR both lean and bloated
solutions pass; the size meter (in the gate) discriminates. Core tier only.

Core behaviors from the prompt goal:
  - the page shows the three named questions and their three named answers
  - "Each answer should start hidden and show when someone clicks its question"
    => there is an interactive disclosure mechanism and answers are not shown by default.

The produced .html is graded by parsing the DOM (stdlib html.parser), never by string
templates: we check that the question and answer texts are present, that there are at
least three clickable disclosure controls, and that the answers begin collapsed.
"""
import glob, json, os, re, sys
from html.parser import HTMLParser

soldir = sys.argv[1]
htmls = sorted(glob.glob(os.path.join(soldir, "*.html")) + glob.glob(os.path.join(soldir, "*.htm")))
subs = []

QUESTIONS = [
    "How do I cancel?",
    "When do you ship?",
    "Where do you deliver?",
]
ANSWERS = [
    "Email us anytime and we'll stop your next shipment.",
    "We roast and ship every Monday.",
    "We currently deliver within the United States.",
]


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text_parts = []
        self.details_total = 0
        self.details_open = 0
        self.controls = 0  # clickable disclosure-ish controls

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        if tag == "details":
            self.details_total += 1
            if "open" in ad:
                self.details_open += 1
        if tag in ("summary", "button"):
            self.controls += 1
        if "onclick" in ad:
            self.controls += 1
        role = (ad.get("role") or "").lower()
        if role == "button":
            self.controls += 1

    def handle_data(self, data):
        self.text_parts.append(data)

    @property
    def text(self):
        return re.sub(r"\s+", " ", " ".join(self.text_parts)).strip()


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


if not htmls:
    print(json.dumps({"subcases": [{"name": "produced_page", "tier": "core", "ok": False}]}))
    sys.exit(0)

with open(htmls[0], encoding="utf-8", errors="replace") as f:
    src = f.read()

parser = Collector()
parser.feed(src)
visible_text = parser.text

# --- Core 1: all question texts present --------------------------------------
q_ok = all(norm(q) in visible_text for q in QUESTIONS)
subs.append({"name": "questions_present", "tier": "core", "ok": q_ok})

# --- Core 2: all answer texts present ----------------------------------------
a_ok = all(norm(a) in visible_text for a in ANSWERS)
subs.append({"name": "answers_present", "tier": "core", "ok": a_ok})

# --- Core 3: an interactive disclosure mechanism exists ----------------------
# accept native <details> widgets, or >=3 clickable controls (summary/button/onclick/role)
disclosure_ok = parser.details_total >= 3 or parser.controls >= 3
subs.append({"name": "clickable_disclosure", "tier": "core", "ok": disclosure_ok})

# --- Core 4: answers start hidden (not shown by default) ---------------------
# For native <details>, "hidden" means not initially open. Otherwise look for a
# hiding mechanism in the markup/styles (hidden attr, display:none, a collapsed class).
if parser.details_total >= 3:
    hidden_ok = parser.details_open == 0
else:
    low = src.lower()
    hidden_ok = ("display:none" in low.replace(" ", "")
                 or " hidden" in low
                 or "aria-hidden" in low
                 or "collaps" in low
                 or "max-height:0" in low.replace(" ", ""))
subs.append({"name": "answers_start_hidden", "tier": "core", "ok": hidden_ok})

print(json.dumps({"subcases": subs}))
