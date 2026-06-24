# Independent benchmark of the ponytail skill (Opus 4.8, 12 tasks)

This is an independent with-versus-without test of [ponytail](https://github.com/DietrichGebert/ponytail). It mostly confirms the headline efficiency numbers, and it surfaces one quality finding worth a closer look.

Summary up front: ponytail (full intensity) wrote 53.1% less code for 48.7% fewer generation tokens than the same agent with no skill. A blind judge panel still preferred the no-skill baseline on quality in 21 of 24 head-to-head verdicts, scoring ponytail about one point lower on average. The gap sits almost entirely in robustness and production-readiness.

## Method, and how it differs from yours

This does not use the promptfoo or correctness-gate setup from the ponytail repo. It is a separate harness, so read it as a cross-check rather than a reproduction.

Twelve tasks, ordered simple to complex, spread across backend, frontend, algorithms, CLI and data work, and one refactor. Each task was built twice from an identical prompt, once with the full SKILL.md injected and once with no skill. Builds went into blind A and B folders, with the A/B mapping flipped per task, and two judges with different emphases scored each pair without knowing which was which. Token cost was sampled from the run's live budget around each build, so these are measured output tokens. Every Python and Node build was executed, the servers were hit with real HTTP calls, and the web pages were rendered in headless Chrome. Model was Claude Opus 4.8 for both building and judging. One run, full intensity only.

## Headline results

| Metric | Baseline (no skill) | Ponytail (full) | Change | Your claim |
|---|--:|--:|--:|---|
| Code lines, non-blank and non-comment | 2,040 | 957 | -53.1% | 54%, matches |
| Generation output tokens | 55,882 | 28,675 | -48.7% | 20%, exceeded |
| Quality composite, out of 10 | 8.86 | 7.82 | -1.04 | n/a |
| Overall winner, 24 blind verdicts | 21 | 2 | tie 1 | n/a |
| More production-ready | 21 | 1 | tie 2 | n/a |
| Followed instructions better | 10 | 2 | tie 12 | n/a |

The code reduction lands almost exactly on your stated 54%. The token reduction came out far higher than the stated 20%, partly because ponytail also writes shorter explanations, not just shorter code.

## Score by criterion

Averaged across all tasks and both judges.

| Criterion | Baseline | Ponytail | Change |
|---|--:|--:|--:|
| Code quality | 8.71 | 7.96 | -0.75 |
| Readability | 8.67 | 8.62 | -0.05 |
| Functionality | 9.38 | 8.58 | -0.80 |
| Instruction following | 9.46 | 8.83 | -0.63 |
| Production readiness | 8.62 | 6.79 | -1.83 |
| Maintainability | 8.54 | 7.67 | -0.87 |
| Robustness | 8.67 | 6.29 | -2.38 |

Readability barely moved. The ponytail code is just as clear to read, there is simply less of it. The damage is concentrated in robustness and production-readiness, which is where minimalism tends to cut into edge-case handling.

## By domain

| Domain | Code saved | Tokens saved | Quality, baseline to ponytail |
|---|--:|--:|--:|
| Frontend | -60.0% | -44.1% | 8.64 to 7.93 |
| Algorithm | -54.7% | -40.8% | 9.05 to 8.07 |
| CLI and data | -56.3% | -57.8% | 9.18 to 7.11 |
| Backend | -35.3% | -54.9% | 8.69 to 7.64 |
| Refactor | -9.1% | -8.9% | 8.86 to 8.71 |

Frontend is where ponytail looks best: the biggest code cut with the smallest quality hit. On the refactor task both arms converged on nearly the same two-line answer and both fixed the planted bug, so the skill barely changed anything when the minimal answer was already obvious. The CLI and data tasks took the largest quality hit, from cut edge cases.

## The finding worth your attention

The skill explicitly says not to skimp on input validation at trust boundaries. Under it, the agent sometimes still did.

On the in-memory Todo REST API, the ponytail build crashed the whole process on a POST with JSON body `null`, an uncaught TypeError that becomes an unhandled rejection and takes the server down. A single malformed request is a remote denial of service. The baseline rejected null and non-object bodies with a 400 and stayed up. Both judges reproduced it.

On the token-bucket rate limiter, the ponytail version had no bucket eviction, so its per-IP map grows without bound under IP churn, and it had no injectable clock, which made its refill test depend on a real timer. The baseline added both.

On the CSV to JSON tool, the ponytail version produced malformed output on ragged rows. On the sales toolkit, its `total_revenue` returned an int against a documented `-> float` contract and its self-checks leaned on exact float equality.

A few outputs also leaked a literal `ponytail:` comment marker into the delivered code, which reads as a small polish issue.

None of this argues against the idea. These are cases where the pressure to write less beat the skill's own safety carve-out. It might be worth making that carve-out louder.

## Caveats

Different harness, no correctness gate, and LLM-judge scoring carries noise, which I reduced by averaging two judges. The sample is 12 tasks on one model in a single run, so the magnitudes are directional. "Tokens" means generation output tokens, and I could not measure wall-clock time per build, so I cannot speak to the 27% faster claim either way.

Full data, the source of all 24 builds, and an interactive dashboard are in this repo. Happy to answer questions or share more detail.
