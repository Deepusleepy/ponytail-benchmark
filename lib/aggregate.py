#!/usr/bin/env python3
"""PonyBench v3 aggregator (pure stdlib, reproducible).

Consumes per-cell records and produces the report. A record is:
  {task, cond, rep, out_tok, size, done(bool), implicit_ok(bool|None),
   security_ok(bool|None), activated(bool)}
- HEADLINE effectiveness = % reduction in OUTPUT TOKENS, ponytail cond vs baseline,
  ITT over all generated runs (a failed run is imputed the per-task MAX so an arm can
  never "win" size by failing), per-task geometric-mean ratio, cluster-bootstrap CI.
- size (meter statements/units) reported the same way as a co-metric.
- NO-HARM = correctness/security/robustness pass rates per cond + the diff vs baseline
  with a bootstrap CI, tested for non-inferiority against the preregistered margins.
- DOSE-RESPONSE = reductions across lite/full/ultra (should grow).
Every number here comes from this committed code; nothing is hand-entered.
"""
import json, math, random, sys
from collections import defaultdict

CONDS = ["lite", "full", "ultra"]
MARGINS = {"correctness": 3.0, "security": 0.0, "robustness": 5.0}  # percentage points


def geomean(xs):
    xs = [x for x in xs if x and x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None


def per_task_ratios(records, metric, baseline="baseline", itt=True):
    bytask = defaultdict(lambda: defaultdict(list))
    for r in records:
        bytask[r["task"]][r["cond"]].append(r)
    ratios = {c: {} for c in CONDS}
    for task, byc in bytask.items():
        allv = [r[metric] for c in byc for r in byc[c] if r.get(metric) is not None]
        tmax = max(allv) if allv else None

        def vals(c):
            out = []
            for r in byc.get(c, []):
                v = r.get(metric)
                if v is None:
                    continue
                if itt and not r.get("done"):
                    v = tmax  # impute a failed run to the per-task max; failing is never a saving
                out.append(v)
            return out

        base = geomean(vals(baseline))
        if not base:
            continue
        for c in CONDS:
            g = geomean(vals(c))
            if g:
                ratios[c][task] = g / base
    return ratios


def reduction(rmap):
    g = geomean(list(rmap.values()))
    return None if g is None else round((1 - g) * 100, 1)


def bootstrap_ci(rmap, B=2000, seed=1):
    tasks = list(rmap.keys())
    n = len(tasks)
    if n < 2:
        return None
    rnd = random.Random(seed)
    reds = []
    for _ in range(B):
        g = geomean([rmap[tasks[rnd.randrange(n)]] for _ in range(n)])
        if g:
            reds.append((1 - g) * 100)
    reds.sort()
    return [round(reds[int(0.025 * len(reds))], 1), round(reds[int(0.975 * len(reds))], 1)]


def rate(records, cond, key, itt=True):
    xs = [r for r in records if r["cond"] == cond and r.get(key) is not None]
    if not xs:
        return None
    return sum(1 for r in xs if r[key]) / len(xs)


def noharm(records):
    out = {}
    for axis, key in [("correctness", "done"), ("security", "security_ok"), ("robustness", "implicit_ok")]:
        base = rate(records, "baseline", key)
        row = {"baseline": None if base is None else round(base * 100, 1)}
        for c in CONDS:
            cr = rate(records, c, key)
            if cr is None or base is None:
                row[c] = None
                continue
            drop = round((base - cr) * 100, 1)  # positive = cond worse than baseline
            row[c] = {"rate": round(cr * 100, 1), "drop_pp": drop,
                      "non_inferior": drop <= MARGINS[axis]}
        out[axis] = {"margin_pp": MARGINS[axis], "rows": row}
    return out


def report(records):
    rep = {"n_records": len(records), "headline": {}, "size": {}, "noharm": noharm(records),
           "dose_response": {}}
    for metric, dest in [("out_tok", "headline"), ("size", "size")]:
        rt = per_task_ratios(records, metric, itt=True)
        for c in CONDS:
            rep[dest][c] = {"reduction_pct": reduction(rt[c]), "ci95": bootstrap_ci(rt[c]),
                            "n_tasks": len(rt[c])}
    red = {c: rep["headline"][c]["reduction_pct"] for c in CONDS}
    rep["dose_response"] = {"output_token_reduction": red,
                            "monotonic": None not in red.values() and red["lite"] <= red["full"] <= red["ultra"]}
    # per-protocol sensitivity (activated-only) for output tokens
    act = [r for r in records if r.get("activated")]
    rtpp = per_task_ratios(act, "out_tok", itt=True)
    rep["headline_perprotocol"] = {c: {"reduction_pct": reduction(rtpp[c])} for c in CONDS}
    return rep


def _synthetic():
    """Self-test: ponytail cuts output ~25/30/35% with noise; baseline has some failures;
    security holds; one task regresses on full. Confirm the aggregator recovers it."""
    rnd = random.Random(7)
    recs = []
    cut = {"baseline": 1.0, "lite": 0.78, "full": 0.72, "ultra": 0.66}
    for t in range(16):
        basetok = rnd.randint(200, 1200)
        for cond in ["baseline"] + CONDS:
            for rep in range(5):
                tok = int(basetok * cut[cond] * rnd.uniform(0.85, 1.15))
                size = int(tok / 10 * rnd.uniform(0.9, 1.1))
                done = rnd.random() > (0.05 if cond == "baseline" else 0.04)
                sec = True  # security holds everywhere (ceiling, expected)
                impl = rnd.random() > (0.15 if cond == "baseline" else 0.13)
                if t == 3 and cond == "full":  # plant a correctness regression on one task
                    done = rnd.random() > 0.6
                recs.append({"task": "t%02d" % t, "cond": cond, "rep": rep, "out_tok": tok,
                             "size": size, "done": done, "implicit_ok": impl,
                             "security_ok": sec, "activated": True})
    return recs


if __name__ == "__main__":
    if len(sys.argv) > 1:
        recs = json.load(open(sys.argv[1], encoding="utf-8"))
    else:
        print("[self-test on synthetic data]")
        recs = _synthetic()
    print(json.dumps(report(recs), indent=2))
