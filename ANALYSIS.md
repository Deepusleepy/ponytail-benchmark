# v3 benchmark: analysis of what went wrong in v1, v2, and the author's benchmarks

This is the design-of-record input. Every issue listed here must be either fixed by v3 or explicitly accepted as a stated limitation. Nothing gets ignored.

## The question we are actually trying to answer

Does the ponytail skill (an instruction to the model to write less code, levels off / lite / full / ultra) cause the model to write **less code** without hurting **correctness**, **security**, or **quality**, and at what **cost**? We want a causal, fair, un-gameable, honestly-reported answer that generalizes as far as the evidence allows and no further.

## v1 problems (the first attempt)

- Skill was pasted into the prompt, not run as the real plugin. Different (stronger) signal than real use.
- Safety judged by an LLM judge, which reads lean code as risky. Produced a false "less safe" headline.
- One blended line count (no separation of logic vs comments vs tests).
- 12 self-contained tasks, one model, one level (full), pooled non-comment lines.
- Headline -53% code was inflated by the pasted-skill setup and the pooled ruler.

## v2 problems (verified against data and confirmed by three independent Codex reviews)

### A. Measurement (the line-counting metric, lib/metrics.py)
1. **Self-test leak (high).** A self-test the model adds is only recognized if it is named test/check/selfcheck or sits in `if __name__=="__main__"`. A self-test named `demo()` (asserts, called from __main__) is counted as **core logic**. Confirmed on t22, t33, t06, t07. Because the skill ADDS self-tests, this inflates skill-arm core and **understates** the reduction. Fixing it moved the Python strict number from ~15% to ~24%.
2. **JS self-check runs to end-of-file (high).** Once `require.main===module` is seen, every later line is tagged self-test, including exports placed after. Order-sensitive: identical JS scores differently by reordering.
3. **HTML decomposition is crude (high/bias).** HTML uses `core = total - comments`, no self-test detection, inline JS/CSS comments not caught. Frontend tasks (the biggest reductions) are measured on a different footing than Python/JS.
4. **Python `class Test...` and top-level asserts outside __main__ counted as core (medium).**
5. **JS inline comments counted as core; cyclomatic complexity regex counts keywords inside strings/comments (medium).**
6. **"Core logic" excludes exactly what the skill changes** (it strips comments and adds a self-test), so core-only is not a neutral ruler for this specific treatment.

### B. Experimental design / fairness
7. **No placebo control (high confound).** baseline = no plugin loaded; skill arms = plugin loaded + mode set (lib/run_one.sh). So it measures "plugin on" vs "no plugin," not pure instruction intensity. Any plugin side effect (hooks, context injection) is confounded with the brevity instruction. Needs an inert/placebo-plugin arm and ideally a "plugin loaded, mode off" arm.
8. **Author-selected tasks with a favorable tilt (high for generalization).** Tasks authored by us, not neutral; several tagged "favorable." Self-contained greenfield only, not brownfield. One model. Headless single-shot.

### C. Statistics / aggregation (lib/aggregate.py vs PREREG.md)
9. **Analysis deviates from the preregistered plan (high).** PREREG says geometric mean across tasks, task as unit, bootstrap CIs, primary outcome = subcase pass-rate + efficiency among DONE runs. The code uses median-of-ratios (not geometric mean), no DONE filter, and computes no CIs in-pipeline.
10. **Activation filtering not actually enforced (high for credibility).** The report says non-activated runs were discarded; aggregate.py never filters by `activated`. t01_slug/lite (activated 0.8) is still in the numbers.
11. **Pooled numbers are not preregistered and are outlier-driven (medium).** The 45-55% pooled figures are driven ~68% by two large tasks (t30_pricing, t20_todoapi). Dropping those two takes pooled full from ~38% to ~21%.
12. **Underpowered for "no harm" (medium-high).** Correctness and security are near 100% on both arms (ceiling), so the study cannot detect modest regressions, only confirm none were caught by these tests. 5 repeats is thin for noisy per-task effects (the strict full CI brushes 0%).

### D. Overstated claims (verified against master_v2.json)
13. **Correctness was NOT 100%.** Macro func = 0.998. t08_calc regressed on the skill arms (baseline done 0.8 -> lite/full done 0). "Nothing broke" is false.
14. **Cost is not flat.** A full run is ~11% more pooled (~21% per task), a few cents more, not "about the same." Output-only tokens do drop ~24-32%.
15. **Some "security" tests are not executed exploits.** HMAC constant-time is a source/regex check; the concurrency race test is scheduler-dependent. "Executed attacks / keeps every safety guard" is too strong.
16. **No measure of code QUALITY/readability/maintainability at all** — only quantity (lines/tokens) and pass/fail. "Less code without losing quality" is asserted, not measured.

## The author's benchmarks (to be refined by the deep-dive agent)
- Single-shot promptfoo benchmark: headline -80 to -94%, later walked back.
- Agentic benchmark: real plugin via `claude -p`, Haiku 4.5, n=4, headline -54% code, ruler = git-diff added lines including comments excluding tests, executed-attack safety on ~6 tasks.
- Author caveats: 54% is an average (up to 94% on over-build traps, near 0% on irreducible code); cost/speed win is Claude-specific and reverses on OpenAI reasoning models; safety is a floor on 6 tasks; one model (Haiku) for the headline; n=4.
- Lesson: the author's own ruler (lines incl comments, excl tests) is itself non-neutral for this treatment (counts removed comments as savings, ignores added tests).

## What a correct v3 must therefore do (high level, expanded in DESIGN.md)
- Add proper control arms to isolate the instruction from the plugin machinery.
- Measure with a robust, language-correct, hard-to-game tool; pick a primary ruler that is neutral to the treatment (lean toward total non-blank LOC and directly-measured output tokens; report core and author-ruler as secondary).
- Measure code QUALITY, not just quantity.
- Preregister the full statistical plan and follow it exactly (unit = task, geometric mean, bootstrap CIs, DONE filtering, activation filtering enforced in code).
- Choose tasks neutrally, freeze them before any results, stratify, include brownfield, enough tasks and repeats for power, more than one model.
- Make correctness/security discriminating (avoid ceilings) and only call "executed" what is actually executed.
- Report honestly: primary number with CI, no cherry-picking aggregation, state every limitation.
