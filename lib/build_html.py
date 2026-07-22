#!/usr/bin/env python3
"""Build the published index.html from the template: inject the data JSON and two
embedded FAQ preview images (base64). Single self-contained output file."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tpl = open(os.path.join(ROOT, "dashboard_template.html"), encoding="utf-8").read()
data = open(os.path.join(ROOT, "results", "dash_data.json"), encoding="utf-8").read()


def b64(name):
    p = os.path.join(ROOT, name)
    return open(p, encoding="utf-8").read().strip() if os.path.exists(p) else ""


out = tpl.replace("/*__DATA__*/", data)
out = out.replace("/*__FAQ_BASE__*/", "data:image/png;base64," + b64("_faq_base.b64"))
out = out.replace("/*__FAQ_FULL__*/", "data:image/png;base64," + b64("_faq_full.b64"))

# Punctuation guard for authored copy (embedded base64 images are exempt).
bad = {"em dash": "—", "en dash": "–", "curly ldq": "“",
       "curly rdq": "”", "curly lsq": "‘", "curly rsq": "’"}
# strip base64 blobs before checking punctuation (images are binary, not prose)
import re
check = re.sub(r'data:image/png;base64,[A-Za-z0-9+/=]+', '', out)
for nm, ch in bad.items():
    if ch in check:
        print("WARN authored copy contains", nm, "x", check.count(ch))

open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out)
print("built index.html:", len(out), "bytes | placeholders left:",
      out.count("/*__"), "| imgs embedded:", out.count("data:image/png;base64,"))
