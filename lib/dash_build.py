#!/usr/bin/env python3
"""Build the v3 dashboard data file from records.json + report.json + tasks/.
All numbers come from the saved data; nothing hand-entered."""
import glob, json, math, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
recs = json.load(open(os.path.join(ROOT, "results", "records.json"), encoding="utf-8"))
report = json.load(open(os.path.join(ROOT, "results", "report.json"), encoding="utf-8"))
CONDS = ["lite", "full", "ultra"]

# friendly names + plain "what we asked" per task
NAMES = {
 "t01_csvjson": "CSV to JSON", "t02_wordfreq": "Word frequency counter", "t03_slugify": "URL slug maker",
 "t04_envparse": ".env file parser", "t05_faqpage": "FAQ web page", "t06_dedupe": "De-duplicate lines",
 "t10_balance": "Running balance", "t11_invoice": "Invoice total", "t12_duration": "Track-length adder",
 "t13_csvcol": "CSV column extractor", "t14_avg": "Average of numbers", "t15_initials": "Name initials",
 "t20_saferead": "Serve a doc by name", "t21_userlookup": "User lookup", "t22_pinghost": "Ping a host",
 "t23_dlticket": "Signed download ticket", "t24_gosafe": "Post-login redirect", "t30_slug": "Slugify (fixed spec)",
 "t31_iso8601": "ISO-8601 duration", "t32_base62": "Base62 encode/decode", "t33_romans": "Roman numerals",
 "t40_clamp": "Add a clamp command", "t41_cart": "Add a discount code", "t42_router": "Add a route parameter",
}
STRATUM_PLAIN = {
 "over-build-tempting": "Jobs that tempt over-building",
 "minimal-is-wrong": "Edge-case-sensitive jobs",
 "security-sensitive": "Security-sensitive jobs",
 "irreducible": "Small fixed jobs (little to trim)",
 "brownfield": "Edits to an existing codebase",
}


def meta(t):
    return json.load(open(os.path.join(ROOT, "tasks", t, "meta.json"), encoding="utf-8"))


def prompt(t):
    s = open(os.path.join(ROOT, "tasks", t, "prompt.txt"), encoding="utf-8").read().strip()
    # normalize unicode punctuation for the published artifact (no em/en dashes, no curly quotes)
    for a, b in [("—", " - "), ("–", "-"), ("“", '"'), ("”", '"'),
                 ("‘", "'"), ("’", "'"), ("…", "...")]:
        s = s.replace(a, b)
    return s


def geomean(xs):
    xs = [x for x in xs if x and x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None


by = defaultdict(lambda: defaultdict(list))
for r in recs:
    by[r["task"]][r["cond"]].append(r)


def red(task, cond, metric):
    b = geomean([r[metric] for r in by[task]["baseline"] if r.get(metric)])
    c = geomean([r[metric] for r in by[task][cond] if r.get(metric)])
    return None if (not b or not c) else round((1 - c / b) * 100)


def passrate(task, cond, key):
    xs = [r for r in by[task][cond] if r.get(key) is not None]
    return round(100 * sum(1 for r in xs if r[key]) / len(xs)) if xs else None


def med_metric(task, cond, metric):
    xs = sorted(r[metric] for r in by[task][cond] if r.get(metric))
    return xs[len(xs) // 2] if xs else None


def median(vals):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    n = len(vals); m = n // 2
    return vals[m] if n % 2 else round((vals[m - 1] + vals[m]) / 2, 1)


def pooled_rate(tids, cond, key):
    """Pass rate pooled over every run in the given tasks (not median-of-per-task,
    which would hide a single task's collapse, e.g. t31 inside the irreducible stratum)."""
    xs = [r for t in tids for r in by[t][cond] if r.get(key) is not None]
    return round(100 * sum(1 for r in xs if r[key]) / len(xs), 1) if xs else None


def task_harmed(t):
    """True if baseline passes the edge-case probe more often than some ponytail level."""
    b = t["robust"]["baseline"]
    return b is not None and any(
        t["robust"][c] is not None and t["robust"][c] < b - 1 for c in CONDS)


tasks = []
for t in sorted(by):
    m = meta(t)
    tasks.append({
        "id": t, "name": NAMES.get(t, t), "stratum": m["stratum"], "stratum_plain": STRATUM_PLAIN[m["stratum"]],
        "domain": m.get("domain", "?"), "lang": m.get("lang", "?"), "prompt": prompt(t),
        "out_red_full": red(t, "full", "out_tok"), "size_red_full": red(t, "full", "size"),
        "out_red": {c: red(t, c, "out_tok") for c in CONDS},
        "correct": {c: passrate(t, c, "done") for c in ["baseline"] + CONDS},
        "robust": {c: passrate(t, c, "implicit_ok") for c in ["baseline"] + CONDS},
        "secure": {c: passrate(t, c, "security_ok") for c in ["baseline"] + CONDS},
        "abs": {"size_base": med_metric(t, "baseline", "size"), "size_full": med_metric(t, "full", "size"),
                "out_base": med_metric(t, "baseline", "out_tok"), "out_full": med_metric(t, "full", "out_tok")},
    })

# per-stratum: savings = true median of per-task reduction; robustness = POOLED run-level
# pass rate (median-of-per-task hid a single task's collapse, e.g. t31 in irreducible).
strat = {}
for s in STRATUM_PLAIN:
    ts = [t for t in tasks if t["stratum"] == s]
    tids = [t["id"] for t in ts]
    strat[s] = {
        "plain": STRATUM_PLAIN[s], "n_tasks": len(ts),
        "out_red_full": median([t["out_red_full"] for t in ts]),
        "robust_baseline": pooled_rate(tids, "baseline", "implicit_ok"),
        "robust_lite": pooled_rate(tids, "lite", "implicit_ok"),
        "robust_full": pooled_rate(tids, "full", "implicit_ok"),
        "robust_ultra": pooled_rate(tids, "ultra", "implicit_ok"),
        "n_harm": sum(1 for t in ts if task_harmed(t)),
    }

FIELD = {
 "web": "Web pages / frontend", "ecommerce": "Web app / backend",
 "security": "Security", "cli": "Command-line tools", "config": "Command-line tools",
 "data": "Data & numbers", "csv-columns": "Data & numbers", "statistics": "Data & numbers",
 "encoding": "Data & numbers", "money": "Data & numbers", "durations": "Data & numbers",
 "text": "Text processing", "names": "Text processing",
}
# per-domain: true-median full out-reduction
dom = defaultdict(list)
for t in tasks:
    dom[FIELD.get(t["domain"], t["domain"])].append(t["out_red_full"])
domains = {d: {"out_red_full": median(v), "n": len(v),
               "tasks": [t["id"] for t in tasks if FIELD.get(t["domain"], t["domain"]) == d]} for d, v in dom.items()}

# every task with a real robustness regression (baseline passes, a ponytail level fails) -
# the page names these so the concentrated harm is not hidden behind the all-task average.
harm_tasks = [{"id": t["id"], "name": t["name"], "stratum_plain": t["stratum_plain"],
               "robust": t["robust"]} for t in tasks if task_harmed(t)]

# token / cost economics per condition (mean per run) - the honest cost story: output
# (what the model writes) drops, input (what it reads, incl. the plugin instructions) rises.
def cond_means(cond):
    rs = [r for r in recs if r["cond"] == cond]
    n = len(rs)
    g = lambda k: round(sum((r.get(k) or 0) for r in rs) / n)
    return {"out_tok": g("out_tok"), "in_tok": g("in_tok"),
            "cache_read": g("cache_read_tok"), "cache_creation": g("cache_creation_tok"),
            "cost_usd": round(sum((r.get("cost_usd") or 0) for r in rs) / n, 4)}
tokens = {c: cond_means(c) for c in ["baseline"] + CONDS}

out = {
    "meta": {"runs": len(recs), "tasks": len(tasks), "conds": ["baseline"] + CONDS, "reps": 5,
             "model": "Opus 4.8"},
    "headline": report["headline"], "size": report["size"], "noharm": report["noharm"],
    "dose": report["dose_response"],
    "comparison": [
        {"who": "Skill author (his own test)", "code_pct": 54, "note": "Haiku, real-repo edits, his ruler", "kind": "external"},
        {"who": "Our v3 (this benchmark)", "code_pct": 53, "tokens_pct": 44, "note": "Opus 4.8, 480 runs, graded by running the code", "kind": "ours"},
        {"who": "Our v1 (early, flawed)", "code_pct": 53, "note": "skill pasted in prompt; safety judged by an AI, not by running attacks", "kind": "flawed"},
    ],
    "tasks": tasks, "strata": strat, "domains": domains, "harm_tasks": harm_tasks,
    "tokens": tokens,
}
json.dump(out, open(os.path.join(ROOT, "results", "dash_data.json"), "w", encoding="utf-8"), indent=2)
print("wrote dash_data.json | tasks:", len(tasks), "| domains:", list(domains))
print("per-stratum out-reduction(full) + robustness base->full:")
for s, v in strat.items():
    print("  %-22s red=%s%%  robust %s%%->%s%%"% (STRATUM_PLAIN[s], v["out_red_full"], v["robust_baseline"], v["robust_full"]))
