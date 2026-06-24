#!/usr/bin/env python3
"""PonyBench v3 runner -- produce ONE solution for one (task, condition, rep) cell.

Grounded in the verified working invocation (author agentic harness + v2 level control):
  claude -p "<prompt>" --model claude-opus-4-8 --permission-mode bypassPermissions
          --output-format json --setting-sources project,local --strict-mcp-config
          --disallowedTools Bash [--plugin-dir <ponytail>] --append-system-prompt "<NO_RUN>"
with PONYTAIL_DEFAULT_MODE=<level> for the ponytail conditions, and an isolated
CLAUDE_CONFIG_DIR that holds copied credentials + a dummy statusLine (kills the
ponytail statusline-nudge confound). Activation/level is verified from the plugin's
own .ponytail-active flag file, NOT the model's self-report (which is unreliable).

NOTE on sampling: the CLI exposes no --temperature/--seed, so runs use the CLI's
default sampling; variance is characterized by repeats, not a pinned temp=0.

Usage:
  python run_one.py --task <task_dir> --cond <baseline|lite|full|ultra> --rep N --out <dir> [--dry-run]
"""
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path

# Path to the ponytail plugin checkout. Override with PONYTAIL_DIR; defaults to a
# sibling "ponytail" folder next to this repo.
_REPO = Path(__file__).resolve().parent.parent
PONYTAIL = os.environ.get("PONYTAIL_DIR", str(_REPO.parent / "ponytail"))
MODEL = "claude-opus-4-8"
CELL_TIMEOUT = 300
NO_RUN = ("Write the implementation (include tests if you normally would for a change like this). "
          "Do not run a dev server, install dependencies, run a database, or open a browser to verify -- "
          "just write the code and stop. Only the code you write is measured, not its execution.")
HARNESS_FILES = {"run.json", "run.err", "result.json", ".ponytail-active"}


def setup_cfg(cfg: Path):
    cfg.mkdir(parents=True, exist_ok=True)
    cred = Path.home() / ".claude" / ".credentials.json"
    if cred.exists():
        shutil.copy(cred, cfg / ".credentials.json")
    else:
        print("WARN: no ~/.claude/.credentials.json -- headless auth may fail", file=sys.stderr)
    acct = Path.home() / ".claude.json"   # account/config; auth needs this too, not just creds
    if acct.exists():
        shutil.copy(acct, cfg / ".claude.json")
    # dummy statusLine so the ponytail SessionStart 'statusline setup needed' nudge never fires
    (cfg / "settings.json").write_text('{"statusLine":{"type":"command","command":"echo bench"}}', encoding="utf-8")


def build_cmd(prompt: str, cond: str):
    cmd = ["claude", "-p", prompt, "--model", MODEL,
           "--permission-mode", "bypassPermissions", "--output-format", "json",
           "--setting-sources", "project,local", "--strict-mcp-config",
           "--disallowedTools", "Bash"]
    if cond != "baseline":
        cmd += ["--plugin-dir", PONYTAIL]
    cmd += ["--append-system-prompt", NO_RUN]
    return cmd


def parse_run_json(path: Path):
    try:
        d = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        return {"telemetry_error": str(e)}
    u = d.get("usage", {}) or {}
    return {
        "is_error": d.get("is_error"),
        "num_turns": d.get("num_turns"),
        "duration_ms": d.get("duration_ms"),
        "cost_usd": d.get("total_cost_usd"),
        "out_tok": u.get("output_tokens"),
        "in_tok": u.get("input_tokens"),
        "cache_read_tok": u.get("cache_read_input_tokens"),
        "cache_creation_tok": u.get("cache_creation_input_tokens"),
        "permission_denials": len(d.get("permission_denials", []) or []),
        "result_text": (d.get("result") or "")[:2000],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--cond", required=True, choices=["baseline", "lite", "full", "ultra"])
    ap.add_argument("--rep", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    task = Path(a.task)
    meta = json.loads((task / "meta.json").read_text(encoding="utf-8")) if (task / "meta.json").exists() else {}
    prompt = (task / "prompt.txt").read_text(encoding="utf-8").strip()  # byte-identical across conditions

    wd = Path(a.out); wd.mkdir(parents=True, exist_ok=True)
    cfg = (wd / "_cfg").resolve()  # MUST be absolute: the child runs with cwd=wd
    cmd = build_cmd(prompt, a.cond)
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(cfg))
    if a.cond != "baseline":
        env["PONYTAIL_DEFAULT_MODE"] = a.cond

    if a.dry_run:
        print(json.dumps({
            "task": meta.get("id", task.name), "cond": a.cond, "rep": a.rep,
            "PONYTAIL_DEFAULT_MODE": env.get("PONYTAIL_DEFAULT_MODE", "(unset)"),
            "CLAUDE_CONFIG_DIR": str(cfg),
            "cmd": cmd,
        }, indent=2))
        return

    setup_cfg(cfg)
    # seed files (brownfield/seeded tasks) copied into the workspace before the run
    seed = task / "seed"
    if seed.is_dir():
        for f in seed.iterdir():
            if f.is_file():
                shutil.copy(f, wd / f.name)
    flag = cfg / ".ponytail-active"
    if flag.exists():
        flag.unlink()  # clear activation flag before the run

    t0 = time.time()
    with open(wd / "run.json", "w") as so, open(wd / "run.err", "w") as se:
        proc = subprocess.Popen(cmd, cwd=str(wd), env=env, stdout=so, stderr=se)
        try:
            proc.wait(timeout=CELL_TIMEOUT)
            status = "ok"
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            status = "timeout"
    elapsed = round(time.time() - t0, 1)

    # activation proof from the flag file (NOT the model's self-report)
    active = flag.read_text(encoding="utf-8").strip() if flag.exists() else "none"
    expected = "none" if a.cond == "baseline" else a.cond
    activated = (active == expected)

    # collect produced solution files (exclude seeds + harness files)
    seed_names = {f.name for f in seed.iterdir()} if seed.is_dir() else set()
    sol = wd / "solution"; shutil.rmtree(sol, ignore_errors=True); sol.mkdir()
    produced = []
    for f in wd.iterdir():
        if f.is_file() and f.name not in HARNESS_FILES and f.suffix.lower() in (
                ".py", ".js", ".mjs", ".ts", ".jsx", ".tsx", ".html", ".htm", ".css", ".json"):
            shutil.copy(f, sol / f.name); produced.append(f.name)

    res = {"task": meta.get("id", task.name), "cond": a.cond, "rep": a.rep,
           "status": status, "elapsed_s": elapsed,
           "activation_flag": active, "expected": expected, "activated": activated,
           "produced_files": sorted(produced)}
    res.update(parse_run_json(wd / "run.json"))
    (wd / "result.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("task", "cond", "rep", "status", "activated",
                                          "out_tok", "cost_usd", "produced_files")}))


if __name__ == "__main__":
    main()
