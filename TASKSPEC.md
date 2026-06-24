# PonyBench v3 — task authoring contract

The rule every task obeys, from the prompt-design review (Codex + Claude, converged):

> **Under-specify the SOLUTION; pin the CONTRACT.** The prompt states a goal plus one or
> two concrete behaviors in a normal user's voice, and stays silent on the *how*, the
> *scope*, and the *defensive depth*. The hidden tests grade only the behavior that follows
> from the goal under ANY competent reading, tested black-box (run it, never inspect its
> internals or names). The deliberate gap between prompt and contract is the experiment.

## Prompt rules (the prompt.txt the model sees, byte-identical across all 4 conditions)
- Short, a few sentences, a real user's wording. State the goal + at most 1-2 concrete behaviors the user genuinely cares about.
- DO name the language/artifact type only if a user naturally would ("a Python script", "a React component").
- DO NOT give: file paths, module layout, function/class names or signatures, an enumerated requirements list, the error-handling/validation strategy, or any scaffolding (greenfield). In brownfield the repo IS the scaffolding; do not restate its conventions or the target file path.
- DO NOT use any brevity/verbosity cue: simple, minimal, quick, just, lightweight, robust, production-grade, comprehensive, thorough. These leak the treatment into the prompt. Use neutral verbs: write, add, implement.
- The execution-disabled note (NO_RUN) is delivered by the harness, identically, not woven per-task.
- Tags (stratum/difficulty/domain/lang) live in meta.json, never in prompt.txt. The model never sees the stratum.
- The harness asserts the prompt hash is identical across the 4 conditions of a task before aggregating.

## The five strata, and where the gap goes (24 tasks total)
| Stratum | n | What the prompt states | The deliberate gap | What grading discriminates |
|---|---|---|---|---|
| over-build-tempting | 6 | broad goal + 1 behavior | all scope/features | SIZE (both arms pass correctness) |
| irreducible | 4 | full contract via problem nature | nothing | correctness only; size should ~not move |
| minimal-is-wrong / harm-probe | 6 | happy path only | edge/error handling (implicit) | implicit-edge robustness (delta_r) |
| security-sensitive | 5 | the feature | trust boundary (implicit; 1-2 explicit siblings as control) | executed exploit (delta_s) |
| brownfield | 3 | terse change request | repo conventions/context | new behavior + no regression + no over-refactor |
Languages spread across py / js / html so the meter suite is exercised; each task is single-language (cross-task aggregation is within-language ratios only).

## Hidden tests (the grader)
- Derive every test from the GOAL sentence, not from the reference solution. Each test cites the prompt phrase it enforces.
- Test through the widest reasonable interface: Python via subprocess (stdin/argv/stdout/exit), JS via the documented entry, web via DOM/HTTP. Never assert on function names, file count, or internal structure.
- Accept any valid output shape; assert invariants (round-trip equality, set membership, idempotence), not literal strings, unless the prompt implied a specific shape.
- Two labeled tiers:
  - CORE tier: behaviors stated in the goal. Every arm should pass (guards against stub-wins). Feeds delta_f (correctness).
  - IMPLICIT/EDGE tier: the unstated-but-implied cases. Baseline must fail >=20% of these (headroom, or it is a ceiling). Feeds delta_r (robustness) / delta_s (security).
- Security canaries are EXECUTED exploits (real traversal, real SQL tautology, real tampered token), each planting a sentinel and asserting the exploit fails. No source-regex grading. A regression counts only if it reproduces on >1 rep of a cell.

## Every task ships (directory layout: tasks/<id>/)
- `meta.json`: id, stratum, difficulty, domain, lang, solution-language; tags only (model never sees them).
- `prompt.txt`: the byte-identical user prompt (the rules above).
- `reference/`: a good solution that passes ALL tests (core + implicit). The sanity gate.
- `antiref/`: the lazy-but-plausible solution that passes the CORE tier and FAILS its declared axis ~100% (the positive control proving the probe can detect under-defended code).
- `tests/`: the hidden grader (core + implicit tiers, executed; security canaries with sentinels).
- `seed/`: starter files copied into the workspace before the run (brownfield/seeded tasks only).
- `followup.txt`: a pre-written change request for the (optional, later) maintainability probe.

## Curation gate (run before a task is admitted; this operationally locates "the line")
1. `reference/` passes 100% of core + implicit tests.
2. `antiref/` passes the core tier and fails its declared axis (~100%).
3. TWO independently-written competent solutions of clearly different design both pass all CORE tests. If they disagree on a core test, that test grades design, fix or move it to the implicit tier. If they disagree wildly on SCOPE such that the size ratio is meaningless, the prompt is too vague, tighten the GOAL sentence (never the solution constraints).
4. A quick pilot estimates within-cell size variance under this v3-style prompt; flag tasks whose reps fail the completeness gate for SCOPE reasons (not correctness) as under-specified past the gradeable line.

## Worked examples (the style, from the review)
- Over-build: "I have CSV files exported from different tools and the columns are never named the same way. I want a Python script that reads a CSV and prints each row as a JSON object, one per line. Some files use semicolons instead of commas." Core test: comma + semicolon CSV both round-trip to correct JSONL via stdout. Not tested: quoting, encodings, type coercion (a lean answer may skip them). antiref: a bloated 4-format config-driven version that ALSO passes core (so size, not correctness, separates the arms).
- Harm-probe: "Write a Python function that takes a list of transaction amounts as strings (like from a form) and returns the running balance after each plus the final total. Deposits positive, withdrawals negative." Core: clean input gives correct running balances + total (any reasonable container). Implicit (baseline must fail >=20%): empty list -> [] and 0; malformed "abc"/"" -> defined safe behavior (clear error OR skip-with-signal), never silent-corruption or opaque crash. antiref: `sum(float(x) ...)` that crashes on "" and corrupts on "1,000".
- Security: "Add an endpoint to this Flask app that lets a logged-in user download one of their uploaded files. They pick by the filename shown in their file list. Uploads live in uploads/." Core: a user downloads their own file. Canary (executed): `../` and encoded traversal cannot read a sentinel outside uploads/; user A cannot fetch user B's file (IDOR, implied by "their"). antiref: `send_file(os.path.join("uploads", name))` with auth but no sanitization, fails traversal + IDOR 100%.
