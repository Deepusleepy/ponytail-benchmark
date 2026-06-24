# Ponytail Benchmark (v3)

An independent benchmark of the [ponytail](https://github.com/DietrichGebert/ponytail) skill, a Claude Code plugin that tells the model to write less code. It runs the real plugin through the command-line tool, builds the same jobs with and without it, and grades every result by running the code, not by asking an AI to judge it.

**[See the full results dashboard.](https://kuldeepb19.github.io/ponytail-benchmark/)**

## What we found

We gave Opus 4.8 twenty-four normal coding jobs, built each one four ways (no plugin, then ponytail at Lite, Full, and Ultra), five times each. That is 480 builds.

- **It writes about 44% less code** at the default Full level (40% at Lite, 46% at Ultra), and about 53% fewer logical statements. The savings are real and hold across most kinds of work.
- **Correctness held.** No measurable loss against the no-plugin baseline (99% pass both ways).
- **No attack got through.** Every working build blocked the same real attacks (path traversal, SQL injection, forged signed tokens). The one job that read below 100% was an output-capture artifact, not a breach.
- **The real cost is robustness.** When a job leaves an edge case unstated, ponytail tends to strip the defensive handling, and the leaner code breaks on bad input. This hit 5 of the 24 jobs; on those, handling of bad input often fell from near-perfect to near-zero, and turning the skill up made it worse, not better. On the other 19 jobs there was no such cost at any level.

The honest one-line version: ponytail makes the model write a lot less code with no loss of correctness or security, but on jobs with hidden edge cases the leaner code gets noticeably more fragile, and the strongest setting is the most fragile.

This robustness cost is the finding no earlier test caught, because earlier tests only asked "did it write less code?" and judged quality by reading, not by running.

## How it is measured

- **Real plugin, real CLI.** The skill runs as the installed plugin through the command-line tool, switched on per run with the level set by environment variable, and activation is verified from a flag file (not the model's self-report, which is unreliable).
- **Graded by execution.** Correctness runs the code against hidden tests. Security fires real attacks and checks what leaks. Robustness probes edge cases the prompt left unstated.
- **Arm-neutral size ruler.** Code size is counted as logical statements by a real parser (Python `ast`, JavaScript via `acorn`, HTML via `node-html-parser` + `postcss`), so reformatting or comments cannot game the number. Self-test scaffolding is detected structurally and excluded.
- **Honest statistics.** Effect on the output side (output tokens), intention-to-treat handling of failed runs, cluster bootstrap confidence intervals, and non-inferiority checks against preset margins for correctness, security, and robustness.

## Reproduce

```
npm install                 # JS/HTML size meters (acorn, node-html-parser, postcss)
python lib/run_all.py --workers N      # runs all cells (needs Claude Code CLI + a ponytail checkout)
python lib/postproc.py runs results/records.json
python lib/aggregate.py results/records.json results/report.json
python lib/dash_build.py    # builds results/dash_data.json
python lib/build_html.py    # builds index.html from the template + data
```

Point `PONYTAIL_DIR` at your ponytail checkout. The build needs Node for the meters.

The aggregated data is in `results/` (`records.json` is all 480 cells, `report.json` the stats, `dash_data.json` what the dashboard reads). The raw per-run transcripts are **not** in this repo: they were generated in throwaway config dirs that held copied login credentials, so they are gitignored. Everything in the dashboard is recomputed from `results/`.

The design of record is in `DESIGN.md`, the issue inventory in `ANALYSIS.md`, and the task-authoring contract in `TASKSPEC.md`.

## About v1

The original version of this benchmark is archived in [`/v1`](v1/). It has been superseded: its method had real flaws (the skill was pasted into the prompt by hand instead of run as the installed plugin, and "safety" was judged by another AI reading the code rather than by running attacks). v3 was rebuilt from scratch to fix those. The `/v1` folder is kept for transparency, not as a current result.

## License

MIT, see [LICENSE](LICENSE).
