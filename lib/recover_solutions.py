#!/usr/bin/env python3
"""Recover solutions for cells where the model PRINTED code in its reply instead of
writing a file (a harness-capture artifact, biased toward ponytail arms). The full
reply is preserved in run.json, so we extract the fenced code block(s) and write them
into solution/. This is fair: the model did produce the code; only the file-capture
missed it. Idempotent and re-derivable; run.json (raw) is never modified.

Usage: python recover_solutions.py <runs_dir> [tasks_dir]
"""
import glob, json, os, re, sys

LANG_EXT = {"python": "py", "py": "py", "javascript": "js", "js": "js", "node": "js",
            "jsx": "jsx", "typescript": "ts", "ts": "ts", "html": "html", "htm": "html",
            "css": "css", "json": "json", "bash": "sh", "sh": "sh"}


def fenced_blocks(text):
    return re.findall(r"```([A-Za-z0-9]*)\n(.*?)```", text, re.DOTALL)


def main(runs, tasks_dir="tasks"):
    recovered = 0
    for rj in glob.glob(os.path.join(runs, "*", "*", "*", "result.json")):
        d = json.load(open(rj, encoding="utf-8"))
        soldir = os.path.join(os.path.dirname(rj), "solution")
        if [f for f in glob.glob(os.path.join(soldir, "*")) if os.path.isfile(f)]:
            continue  # already has a captured solution
        run = os.path.join(os.path.dirname(rj), "run.json")
        try:
            txt = json.load(open(run, encoding="utf-8")).get("result") or ""
        except Exception:
            continue
        blocks = fenced_blocks(txt)
        if not blocks:
            continue
        meta = {}
        mp = os.path.join(tasks_dir, d["task"], "meta.json")
        if os.path.exists(mp):
            meta = json.load(open(mp, encoding="utf-8"))
        deflang = meta.get("lang", "py")
        # the solution is the largest fenced code block (ignore tiny usage snippets)
        lang, code = max(blocks, key=lambda b: len(b[1]))
        ext = LANG_EXT.get(lang.lower(), deflang)
        os.makedirs(soldir, exist_ok=True)
        open(os.path.join(soldir, "recovered.%s" % ext), "w", encoding="utf-8").write(code.rstrip() + "\n")
        d["recovered_from_text"] = True
        d["produced_files"] = ["recovered.%s" % ext]
        json.dump(d, open(rj, "w", encoding="utf-8"), indent=2)
        recovered += 1
    print("recovered %d cells from printed code" % recovered)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "tasks")
