# PonyBench v3 — design / preregistration (v2 draft, post-review)

Status: DRAFT v2, revised after three adversarial reviews (one Codex, two Claude: one statistics-focused, one practicality-focused). Nothing is executed yet. The four issues the reviewers called disqualifying in draft v1 are addressed here: (1) the size number was conditioned on a collider; (2) the primary hypothesis had no margin; (3) power was asserted not computed; (4) the specificity control was hand-wavy (since dropped entirely by scope choice; see section 3). Each fix is below and tagged [FIX].

Scope decision (this revision): single model (Opus 4.8); conditions are no-ponytail vs ponytail levels (lite/full/ultra) only, with no placebo or generic-nudge control (this is a product question, not a mechanism question); ~480 runs. See sections 3, 11, 14, and the accepted limitation in 15.

Build stance: this is **fork + harden, not build-fresh.** The author's public agentic harness (`benchmarks/agentic/`, MIT) already provides per-arm plugin isolation, the flag-file activation mechanism, a brownfield pinned repo, executed safety scorers with good/bad self-tests, and two temp-0 self-validated LLM judges (completeness, over-engineering). v3 forks that and adds only three genuinely new pieces: (a) a parser-based, arm-neutral size ruler with structural self-test bucketing; (b) the placebo/control arms; (c) a real statistics layer (mixed-effects + cluster bootstrap + estimand definitions + frozen analysis code). We credit the author's prior work explicitly and do not present reused machinery as our own.

The hard rule: every number in the final writeup is produced by committed code in `lib/`, run on placeholder data before the paid run so confirmatory-vs-exploratory is enforced by git history, never typed by hand (v2's confidence intervals were hand-typed).

---

## 1. The question

Does the ponytail skill (a real Claude Code plugin that tells the model to write less code) **cause** the model to produce **less, more concise output**, **without** loss of correctness / security / robustness, and does the effect **scale with the level** (lite -> full -> ultra)? Sub-questions, kept separate:
- Q1 effectiveness: does it reduce what the model writes, measured **output-side** (the skill only touches output).
- Q2 no-harm (the PRIMARY concern): correctness / security / robustness hold.
- Q3 dose-response: does the effect grow as the level is cranked.
- Q4 cost (secondary, billing reality): what a run actually costs cold vs warm. This is dominated by fixed, mostly-cached input the skill does not touch, so it is NOT the measure of effectiveness.

---

## 2. Hypotheses, margins, and the confirmatory family [FIX 2, 5]

Confirmatory family (preregistered, alpha split by Holm at family alpha = 0.05):
- **H1 (no-harm, primary, non-inferiority).** Each ponytail level is non-inferior to baseline on: functional correctness with margin delta_f = 3 percentage points; executed security canaries with margin delta_s = 0 tolerated regressions (any executed-exploit regression fails H1); input-robustness with margin delta_r = 5 pp. Tested as one-sided TOST / lower CI bound vs the margin. All three sub-gates must hold. Margins justified: 3 pp is below the run-to-run correctness noise a user would plausibly notice; delta_s = 0 because any reproducible exploit regression is a real security harm, not a tolerance band; delta_r = 5 pp reflects that implied-edge-case handling is a softer boundary than an executed exploit.
- **H2 (size).** ponytail-full writes less code than baseline on the primary size metric (section 6), superiority test; each level vs baseline is also reported.
- **H3 (dose-response).** Code size decreases across levels (lite >= full >= ultra in size), each step a real reduction. A consistent dose-response is strong causal evidence that ponytail itself drives the effect; it replaces the dropped specificity control.

Everything else (per-stratum, per-domain, cost framings, maintainability, readability) is exploratory and reported with Benjamini-Hochberg FDR across the declared exploratory family. The writeup labels confirmatory vs exploratory automatically from the frozen analysis code; we do not bury H2/H3 in the exploratory bucket and we do not promote an exploratory result to a headline.

Margins are justified in absolute user-relevant terms and the power analysis (section 10) is run **against these specific margins** before n is frozen.

---

## 3. Conditions — ponytail intensity levels vs no ponytail

We test what ponytail does to the model's first autonomous solution: plain Opus 4.8 against ponytail at each real intensity level. Scope, stated honestly: this is unattended, single-turn use via `claude -p`, not an interactive chat where a human steers over many turns (see the limitation and its direction in section 15). The placebo and generic-nudge controls are intentionally NOT run, because the question is "does ponytail help," not "is it the plugin or the instruction." What stands in for that control is the dose-response across levels: if code shrinks steadily as the level is cranked, that is itself strong evidence ponytail is causing it.

| Condition | What it is | Role |
|---|---|---|
| baseline | plain Opus 4.8, no plugin | the "not ponytail" reference |
| lite | ponytail, gentlest level | dose step 1 |
| full | ponytail, default level | product as shipped (primary contrast vs baseline) |
| ultra | ponytail, strongest level | dose step 3 |

The task prompt is byte-identical across conditions; only the plugin/level differs. The v2 in-prompt arm canary (`PT:<mode>`) is removed, so the model is not told which condition it is in; activation and level are verified out of band from the plugin flag file. Honest scope note: dropping the placebo/generic controls means we cannot separate "the ponytail instruction" from "the ponytail plugin machinery," nor claim ponytail beats a generic be-concise nudge. Both are accepted as out of scope; the dose-response across levels is the causal backbone instead.

---

## 4. Activation, handled as the post-treatment variable it is [FIX 13]

Activation is verified out of band from the plugin flag file, per arm. But excluding non-activated runs is itself conditioning on a post-treatment variable, so:
- Report per-arm activation rate.
- Primary analysis is intention-to-treat: a run is kept under its assigned arm regardless of activation; non-activation is a property of the treatment.
- Per-protocol (activated-only) is a pre-registered sensitivity analysis, reported beside ITT.
- An arm whose activation rate falls below a pre-registered threshold is reported as "non-compliant," not silently filtered.

---

## 5. Tasks — neutral frame, calibrated harm probes, frozen before results [FIX harm-power, sourcing]

- **Sampling frame frozen before any run.** Tasks drawn from or adapted from pre-existing public sources (the author's public fixture repo, real PRs, SWE-bench-style edits, public exercises). Curated by someone other than whoever tunes the analysis. Every rejected candidate and the reason is logged. An independent rater tags each task's expected reducibility BEFORE runs, so the prior split cannot be back-fit.
- **Strata (fixed split):** over-build-tempting, irreducible, **minimal-is-wrong / harm-probe**, brownfield-edit, security-sensitive.
- **Harm probes must have headroom [FIX 12].** Pre-registered calibration target: the baseline (no-ponytail) must FAIL at least 20% of the harm-probe and robustness checks (and each task's `antiref` lazy-but-plausible solution must fail ~100% of its declared-axis checks, as the positive control proving the probe can detect under-defended code). If baseline aces them, the probe is a ceiling and is reported as "could not detect harm here," not as evidence of no harm. This is what makes H1 falsifiable.
- **Security explicit AND implicit.** Some tasks state the trust boundary; others (like the author's design) leave the safety requirement implicit and score it adversarially. Pre-registered which is which. Every security subcase is an executed behavioral canary traced to a spec clause; no source-regex grading (v2's HMAC constant-time check is dropped or replaced by a real statistical timing harness, otherwise reported as "wrote the idiom," not "secure").
- **Brownfield is constrained.** Real-repo edits use the author's pinned fixture repo at a fixed commit, scoped to small features, to bound complexity (it is the main source of harness fragility).
- **Each task ships:** byte-identical prompt across arms; difficulty/prior/domain/lang tags; `reference/` (passes all) and `antiref/` (passes happy path, fails its declared axis); executed hidden correctness tests; executed behavioral security canaries; input-perturbation robustness checks with their own good/bad gate; a pre-written follow-up change request (maintainability); deterministic acceptance/DOM/API checks where feasible (LLM completeness judge only as secondary adjudication). Fixtures are created in an isolated sandbox, never the deliverable dir, so the model's own self-check files cannot pollute counts or grading.
- Count: minimum tier ~24-30 tasks with harm/security oversampled; full tier ~40-50. Final n set by the power analysis (section 10), not pre-committed.

---

## 6. Size: estimand and metric [FIX 1, 6]

**Estimand [FIX 1].** The primary size effect is **intention-to-treat over all generated runs**, NOT conditioned on DONE. Failed/incomplete runs are not silently dropped (that conditions on a collider the treatment affects, e.g. v2 t08_calc where the skill drove DONE from 0.8 to 0). Handling (pre-registered, since this rule can move H2/H3): a run that fails the completeness/correctness gate is imputed the per-task MAXIMUM deliverable size observed across all arms (a failed attempt can never count as a size saving), and the failure rate is reported as a competing outcome beside the size number. Pre-registered sensitivity sweep over the imputation rule {per-task max (primary), baseline-arm median, 2x per-task median, and a principal-stratum drop}; if the sign or significance of H2/H3 flips across these, that flip is the headline caveat. We additionally report: (a) a principal-stratum estimate restricted to tasks that are DONE under *both* arms (always-DONE), and (b) a per-protocol DONE-only number, both clearly labeled secondary, plus a check that DONE-rate is statistically indistinguishable across the contrasted arms before any conditional number is shown.

**Metric [FIX 6].** The headline EFFECTIVENESS metric is **percent reduction in directly-measured output tokens vs baseline** (intention-to-treat, within-task log-ratio, interpretable only when the no-harm gate passes), shown with the AST logical-statement count of the **total emitted deliverable (self-test included)** as its structural companion. We headline output-side because the skill only shapes output, and total cost cannot show the skill working (output is ~1% of an agentic run's tokens), so cost is a secondary billing panel (section 9), never the effectiveness claim. Output tokens are not a pure restatement of code size: they also capture explanatory prose and tool-call round-trips, so when the output-token and AST reductions diverge, that divergence is itself a reported finding, and we attribute the output delta into code vs prose vs tool-turns. Counting the total deliverable (self-test included) matters because the user reads and pays for the self-test the skill adds; v1's "core only, self-test excluded" flattered the skill on exactly the axis v2 was criticized for (v2's all-lines number could cross into *more* code). So:
- Primary pair: directly-measured **output tokens** (the headline effectiveness number) and **AST logical statements** of the total deliverable (the structural anchor), both as within-task ratios vs baseline, no-harm-gated; comments and the self-test are bucketed separately but counted.
- Secondary panel: core-only (self-test excluded), comment count, AST node count, dependency/API surface, formatter-normalized bytes. These are a sensitivity panel, never a "pick the flattering one" menu; the primary is fixed.

**Measurement integrity [FIX 9].** Counts come from real parsers (Python `ast`, JS/TS tree-sitter, HTML/CSS real parsers), not physical lines or regex. Self-test detection is structural (top-level code reachable only from `__main__`, functions whose body is only assertions/prints with no externally used return), excluded identically across arms. The bucketer is validated on a hand-labeled held-out set and we report its **confusion matrix by arm**; if arm-asymmetric misclassification exceeds 2% of counted statements, the metric is void and the parser/bucketer is fixed before any run. We do NOT pool a raw statement count across languages; all cross-task aggregation is on within-task, within-language ratios.

---

## 7. No-harm: correctness, security, robustness [FIX harm-power]

- Correctness: executed hidden tests; completeness via deterministic acceptance checks where feasible, plus a temp-0 self-validated LLM completeness judge (reuse author's `complete.py`) as secondary, to kill stub-wins.
- Security: executed behavioral canaries only (real path traversal, real SQL tautology, real tampered-token rejection, real malformed input, implicit and explicit tasks), each with an `antiref` positive control proving the canary can catch under-defended code.
- Robustness (distinct from mutation testing, which v1 conflated): input-perturbation against boundary/edge inputs the spec implies but does not enumerate, with its own good/bad gate so we can prove the probe detects under-defended code. This is where the no-harm test gets its statistical headroom.

---

## 8. Quality [FIX maintainability, completeness]

- Maintainability: each solution gets a pre-written follow-up change request implemented by **>=2 follow-up models of different families** (avoids same-family bias the author was dinged for), reported per-model; primary outcome is the continuous change-size, plus deterministic pass of the follow-up's own tests; binary success and failure categories reported too. Stated as a proxy for human maintainability, not a substitute.
- Readability (full tier, exploratory): auto-formatted, arm-stripped, >=2 cross-vendor temp-0 judges with published rubric and mandatory citation; inter-rater agreement reported; walled off as opinion.

---

## 9. Cost — a secondary billing panel, NOT the effectiveness claim [FIX cost-lens]

Effectiveness is measured output-side (section 6). Cost is a separate, secondary "what does a run actually cost" question, reported honestly but never headlined as whether the skill works: in an agentic `claude -p` run the bill is dominated by fixed, mostly-cached input (system prompt, tool defs, the skill's own ruleset, prior context), and output is ~1% of tokens, so total cost mostly measures cache plumbing, not ponytail.

Two distinct claims, kept apart:
- Effectiveness claim (section 6): output got smaller without harm. The skill's own input overhead is NOT charged here, because the skill's mechanism is output shaping.
- Economic claim (this panel): the bill, with the skill's prompt overhead charged, separately for cold and warm cache.

The billing panel reports, per condition vs baseline:
- Marginal output cost (the cleanest cost consequence of the effectiveness result).
- Cold-cache total session cost, with the skill's added ruleset charged at first-read (cache-creation) price; on a cold one-shot the skill can be net MORE expensive (it pays for its ruleset to save a little output).
- Warm-cache total session cost, only when cache hits are PROVEN from recorded cache_read tokens; warm, the ruleset is cheap and the output savings show.
- A token breakdown table: fresh input / cache-creation / cache-read / output, so the reader sees output is ~1% and why total barely moves.

Cold and warm are reported separately, never blended; if the sign of the net cost effect flips between cold and warm, that flip is the stated caveat, not a footnote. We never headline a "total cost reduction." Caching hazard: Anthropic prompt caching is opt-in and may never fire, so a warm number requires explicitly setting cache_control and recording cache_read per run to prove the hit. Scope: Opus 4.8 only; cost is Claude-specific.

---

## 10. Statistics [FIX 2, 3, 7, 8, weighting]

- **Primary inferential object = a hierarchical mixed-effects model** of log-size: fixed arm effect, random effects for task and rep-within-cell, model and temp as specified factors. This handles clustering and unequal surviving-rep counts and partial-pools more stably than a 24-40-cluster bootstrap. [FIX 7/8]
- **No-harm endpoints (correctness, security, robustness) are modeled separately** as a mixed-effects logistic regression (binomial GLMM): pass/fail per run, fixed arm effect, random intercept for task (rep nested in cell), unit = run. Non-inferiority = the lower bound of the arm-minus-baseline risk-difference CI versus the margin. For the zero-tolerance security margin (delta_s = 0), a canary regression counts only if it REPRODUCES (fails on more than one rep of a cell), to separate a true regression from sampling flakiness.
- Output tokens (the headline effectiveness metric) are modeled with the SAME log-ratio mixed-effects machinery as deliverable size. Cost-panel numbers (section 9) are descriptive, not modeled as confirmatory.
- **Robustness checks:** paired analysis on per-task contrasts (ratio of cell geometric means, not arbitrary rep pairing), and a **cluster bootstrap** (resample tasks, then reps-within-task) with BCa and a recorded seed; we verify CI stability across two seeds/B values and report if it is not stable (a signal n is too small). [FIX 7]
- **Weighting:** equal task weight for the primary; equal stratum weight with equal task weight inside strata for stratified summaries. No per-task weight cap (equal weighting already removes v2's pooled concentration). [FIX 20]
- **Power, computed before freezing n [FIX 3]:** simulate from v2's per-task ratio variance (we have it) for the size effect (run-to-run variance is real since temperature is not pinned), and compute the runs needed to rule out each H1 margin (delta_f, delta_s, delta_r) at alpha/power. The no-harm test, near a ceiling, needs many runs per task family; if the required n is infeasible, we state H1 as a reported equivalence bound ("we can rule out harm larger than Z"), not a clean "no harm." n (tasks and reps) is then set from these curves, not pre-committed.
- **Multiple comparisons:** Holm within the confirmatory family; BH-FDR across the declared exploratory family; the families are listed explicitly in the frozen analysis code.
- **Zeros/failures/missing:** explicit handling pre-registered (log-size needs a floor; failures enter the ITT size estimand via the conservative score; activation handled per section 4).

---

## 11. Model

Opus 4.8 only, by choice. The result is scoped to Opus 4.8 and makes no cross-model generalization claim (the author's headline was likewise single-model). No cross-study triangulation with the author's number.

---

## 12. Harness & provenance [FIX feasibility, provenance]

- Fork the author's `benchmarks/agentic/` harness: per-arm plugin isolation via `--plugin-dir --setting-sources project,local`, flag-file activation, brownfield fixture repo, executed safety scorers with good/bad gates, `judge.py`/`complete.py` (temp-0, self-validated). Add the three new pieces (size ruler, control arms, stats layer).
- No execution during generation (`--disallowedTools Bash`, identical NO_RUN note). Evaluate afterward in a sandbox.
- Sampling: the `claude -p` CLI exposes NO temperature/seed flag (verified via `claude --help`), so when ponytail runs as a real plugin we CANNOT pin temp=0; runs use the CLI's default sampling. We therefore do not claim a temp=0 reproducibility anchor; instead we characterize run-to-run variance with the repeats and report it (the within-cell spread is a reported quantity, not assumed away). If a settings.json-based temperature override turns out to work it is a bonus, not relied upon.
- Every run records: model id, temperature, hash of injected instruction text, hash of task spec, harness commit, CLI version. The aggregator refuses to blend runs whose hashes do not match the current task/skill. Workspaces preserved for offline re-score.

---

## 13. Reporting integrity
One pre-registered primary effectiveness metric (output-side, section 6); alternates are a labeled sensitivity panel. No total-cost number is ever promoted to the effectiveness claim, and a size/output reduction is interpretable only when the no-harm gate passes (reported struck-through otherwise, never as a win). Scope stated exactly (Opus 4.8, the temps, the task corpus, greenfield+brownfield). Confirmatory vs exploratory marked from the frozen code. Every reported number links to the script + commit that produced it.

---

## 14. Scale (locked)

- Conditions: baseline + lite + full + ultra (4). Model: Opus 4.8 only. Tasks: ~24, with the harm-probe and security strata oversampled. Reps: 5 (the target; the power simulation in section 10 confirms or nudges it), at the CLI's default sampling (temperature is not settable via the plugin CLI, so no temp=0 subset; variance comes from the reps).
- Generation count: 4 conditions x 24 tasks x 5 reps = **480 runs** (no temp=0 subset; the CLI can't pin temperature). Plus cheap completeness-judge calls only where no deterministic check exists. No maintainability or readability battery in this version (optional later).
- Optional later expansion (only if the 480-run result is clean and worth it): more tasks, the quality battery, a second model, or a small scripted single-turn follow-up probe (~300 runs, one fixed follow-up identical across arms, to bound the interactive-use gap). Not committed now.

## 15. Residual threats even in v3
- Not double-blind (the model reads the brevity instruction); we estimate the effect of the instruction, not a placebo-controlled drug trial.
- Temperature is not settable through the plugin CLI, so runs are at default sampling and are not bit-reproducible; we report within-cell variance rather than claim a temp=0 anchor.
- Security and robustness remain coverage, not proof; reported as "no regression on this adversarial suite that baseline demonstrably can fail."
- Maintainability-by-model is a proxy.
- Cost is Claude-specific and caching-sensitive; the non-Claude numbers are portability simulations.
- Generalization bounded by the corpus and the models run; stated as such.
- No placebo or generic-nudge control is run, so we cannot separate the ponytail instruction from the plugin machinery, nor claim ponytail beats a generic "be concise" nudge. Accepted scope; the dose-response across levels is the causal evidence instead.
- Generation is autonomous, single-turn, execution-disabled (`claude -p`); we measure the FIRST written artifact, not a tested-and-iterated interactive solution. Direction of this gap, stated openly: in a real chat a human runs the code and fixes under-built or edge-case failures, repairing exactly what the harm probes detect, so interactive use would likely show LESS harm than we report (our no-harm result is therefore conservative); and a human might trim some bloat themselves, making the measured size benefit an upper bound on the marginal interactive benefit. The reported number is the autonomous first-draft causal effect.
- LLM judges (completeness, readability) remain partly subjective even with cross-vendor temp-0 panels and self-validation.

---

## 16. Issue -> fix traceability (v1 draft review findings folded in)
- collider DONE-conditioning -> 6 (ITT size estimand + principal stratum + sensitivity).
- undefined non-inferiority margin -> 2 (delta_f/delta_s/delta_r named).
- power asserted not computed -> 10 (power-first, equivalence bound if infeasible).
- temp=0 regime infeasible (CLI has no temperature flag, verified) -> 12,14,15 (default sampling, variance from reps, stated limitation).
- specificity/placebo controls -> dropped by scope choice (product question); dose-response across levels (H3) is the causal substitute; residual plugin-vs-instruction confound accepted in 15.
- core-only flatters skill -> 6 (total incl self-test primary, core secondary).
- total cost masks effectiveness -> 1,6,9 (output-side headline gated by no-harm; total cost demoted to a secondary billing panel, the skill's input overhead charged in the economic claim only, cold/warm separated).
- bootstrap unstable at small n / wrong primary -> 10 (mixed-effects primary, cluster bootstrap robustness).
- harm test is a ceiling -> 5,7 (calibrated probes, baseline must fail, antiref positive controls).
- self-test exclusion asymmetry / metric gaming -> 6 (structural bucketer, arm confusion matrix, include self-test in primary).
- completeness via LLM only -> 7 (deterministic acceptance + judge secondary).
- maintainability circularity -> 8 (>=2 families, continuous change-size).
- cost caching artifact -> 9 (cold/warm billing panel, prove warm via recorded cache_read; Opus-only).
- model scope -> 11 (Opus 4.8 only, no cross-model claim).
- activation as post-treatment filter -> 4 (ITT primary, per-protocol sensitivity).
- task sourcing gameable -> 5 (frozen frame, logged rejects, independent reducibility rating).
- too large to run / under-credited reuse -> 12,14 (fork author harness, locked pilot + escalation).
- all v2 measurement/stats/arm/claim issues from ANALYSIS.md -> sections 3,4,6,10,12 as mapped previously.
