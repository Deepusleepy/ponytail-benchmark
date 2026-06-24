export const meta = {
  name: 'ponybench',
  description: 'Benchmark ponytail skill: 12 tasks built with/without it (blind A/B), token-measured, then judged',
  phases: [
    { title: 'Build', detail: 'sequential baseline+ponytail builds per task, token-measured' },
    { title: 'Judge', detail: '2 perspective-diverse blind judges per task' },
  ],
}

// ---- The ponytail skill content (full intensity), injected verbatim into the "with" arm ----
const PONYTAIL = `# Ponytail

You are a lazy senior developer. Lazy means efficient, not careless. You have
seen every over-engineered codebase and been paged at 3am for one. The best
code is the code never written.

## Persistence
ACTIVE EVERY RESPONSE. No drift back to over-building. Still active if unsure. Default: full.

## The ladder
Stop at the first rung that holds:
1. Does this need to exist at all? Speculative need = skip it, say so in one line. (YAGNI)
2. Stdlib does it? Use it.
3. Native platform feature covers it? <input type="date"> over a picker lib, CSS over JS, DB constraint over app code.
4. Already-installed dependency solves it? Use it. Never add a new one for what a few lines can do.
5. Can it be one line? One line.
6. Only then: the minimum code that works.
The ladder is a reflex, not a research project. Two rungs work -> take the higher one and move on.

## Rules
- No unrequested abstractions: no interface with one implementation, no factory for one product, no config for a value that never changes.
- No boilerplate, no scaffolding "for later".
- Deletion over addition. Boring over clever. Fewest files possible. Shortest working diff wins.
- Complex request? Ship the lazy version and question it in the same response.
- Two stdlib options, same size? Take the one that's correct on edge cases. Lazy means writing less code, not picking the flimsier algorithm.
- Mark deliberate simplifications with a ponytail: comment. Shortcut with a known ceiling? The comment names the ceiling and the upgrade path.

## Output
Code first. Then at most three short lines: what was skipped, when to add it. No essays, no feature tours, no design notes.

## When NOT to be lazy
Never simplify away: input validation at trust boundaries, error handling that prevents data loss, security measures, accessibility basics, anything explicitly requested.
Lazy code without its check is unfinished. Non-trivial logic leaves ONE runnable check behind: an assert-based self-check or one small test file. Trivial one-liners need no test.

The shortest path to done is the right path.`

// ---- Tasks (identical spec given to both arms) ----
const BASE = './builds'
const TASKS = [
  { id:'task-01', title:'Health & time JSON API', domain:'Backend', difficulty:'Easy', lang:'node',
    spec:`Write a single Node.js file server.js using ONLY the built-in http module (no external dependencies). It must serve: GET /health -> JSON {"status":"ok","uptime": <process uptime seconds, number>}; GET /time -> JSON {"now": <current ISO 8601 timestamp string>}; any other path -> 404 JSON {"error":"not found"}. Listen on port 3000. Set Content-Type application/json on all responses.` },
  { id:'task-02', title:'In-memory Todo REST API', domain:'Backend', difficulty:'Medium', lang:'node',
    spec:`Write a single Node.js file server.js (built-in http module only, no external deps) implementing an in-memory Todo REST API on port 3000. Endpoints: GET /todos -> array; POST /todos with JSON body {"title":string} -> create {id,title,done:false}, status 201; GET /todos/:id -> one or 404; PUT /todos/:id with JSON body {title?,done?} -> update, 404 if missing; DELETE /todos/:id -> 204, 404 if missing. Validate input (reject missing/empty title with 400). Correct HTTP status codes and JSON responses throughout.` },
  { id:'task-03', title:'Token-bucket rate limiter', domain:'Backend', difficulty:'Complex', lang:'node',
    spec:`Write a single Node.js file limiter.js (built-in modules only) implementing a token-bucket rate limiter as HTTP middleware for the built-in http server. Per-client-IP buckets with configurable capacity and refill rate (tokens/sec). When no token is available, respond 429 with a Retry-After header (seconds until next token) and JSON {"error":"rate limited"}. Export the middleware factory. Include a runnable self-check in if (require.main === module) that simulates rapid requests from one IP and asserts the limiter allows up to capacity then blocks, and that it refills over time.` },
  { id:'task-04', title:'Responsive pricing section', domain:'Frontend', difficulty:'Easy', lang:'html',
    spec:`Write a single self-contained index.html (inline CSS, no external resources or frameworks) with a responsive pricing section of exactly 3 plan cards: Starter ($9/mo), Pro ($29/mo), Enterprise ($99/mo). Each card shows plan name, price, a list of 4 features, and a CTA button. Visually highlight the middle (Pro) card as recommended. Responsive: 3 columns on desktop, stacking to 1 column on narrow screens.` },
  { id:'task-05', title:'Todo app with localStorage', domain:'Frontend', difficulty:'Medium', lang:'html',
    spec:`Write a single self-contained index.html (inline CSS + vanilla JS, no frameworks or external resources) implementing a Todo app: input to add a todo; each item can be toggled complete (visual strike-through) and deleted; filter buttons All / Active / Completed; a counter showing remaining active items; persist all todos to localStorage so they survive reload. Clean, usable UI.` },
  { id:'task-06', title:'Sales dashboard (no chart lib)', domain:'Frontend', difficulty:'Complex', lang:'html',
    spec:`Write a single self-contained index.html (inline CSS + vanilla JS, NO charting library, no external resources). Embed this dataset in the script: [{"month":"Jan","revenue":42000,"users":1200},{"month":"Feb","revenue":38500,"users":1100},{"month":"Mar","revenue":51200,"users":1450},{"month":"Apr","revenue":47800,"users":1380},{"month":"May","revenue":61000,"users":1720},{"month":"Jun","revenue":58300,"users":1650}]. Render: (1) a bar chart of monthly revenue, (2) a line chart of monthly users, (3) three KPI stat cards: total revenue, average monthly users, best month by revenue. Draw charts yourself with SVG or canvas. Make it look like a clean dashboard.` },
  { id:'task-07', title:'slugify()', domain:'Algorithm', difficulty:'Easy', lang:'python',
    spec:`Write a Python file slugify.py with slugify(text: str) -> str: lowercase; spaces and underscores become single hyphens; remove chars not a-z, 0-9, or hyphen; collapse consecutive hyphens; strip leading/trailing hyphens. Example: "  Hello, World!  " -> "hello-world". Include assert-based self-checks under if __name__ == '__main__': covering normal, punctuation, and edge cases (empty string, all-symbols). python slugify.py must exit 0 when correct.` },
  { id:'task-08', title:'O(1) LRU cache', domain:'Algorithm', difficulty:'Medium', lang:'python',
    spec:`Write a Python file lru.py implementing class LRUCache(capacity: int) with get(key) (value or None) and put(key, value), both O(1), evicting the least-recently-used item when capacity is exceeded. get or put counts as a use. Include assert-based self-checks under if __name__ == '__main__': covering eviction order, updating existing keys, and capacity limits. python lru.py must exit 0 when correct.` },
  { id:'task-09', title:'Expression evaluator (no eval)', domain:'Algorithm', difficulty:'Complex', lang:'python',
    spec:`Write a Python file calc.py with evaluate(expr: str) -> float that parses and evaluates arithmetic expressions with + - * / parentheses and integer/decimal numbers, honoring standard precedence and associativity. Do NOT use eval() or exec(). Handle whitespace. Raise a clear exception on malformed input or division by zero. Include assert-based self-checks under if __name__ == '__main__': covering precedence, parentheses, decimals, and error cases. python calc.py must exit 0 when correct.` },
  { id:'task-10', title:'CSV->JSON CLI', domain:'CLI / Data', difficulty:'Medium', lang:'python',
    spec:`Write a Python CLI csv2json.py (stdlib only) converting CSV to JSON. Usage: python csv2json.py [file.csv] prints a JSON array of objects (one per row, keyed by header). With no file argument, read CSV from stdin. Support a --pretty flag for indented output. Handle a missing file with a clear error message and non-zero exit. Include a --selfcheck flag that runs assert-based tests on a small in-memory CSV and exits 0 on success.` },
  { id:'task-11', title:'Sales aggregation toolkit', domain:'CLI / Data', difficulty:'Medium', lang:'python',
    spec:`Write a Python file sales.py (stdlib only) operating on a list of sales records, each a dict like {"date":"2026-01-15","product":"Widget","amount":19.99}. Provide: total_revenue(records)->float; revenue_by_product(records)->dict product->total; top_products(records,n)->list of (product,total) descending; monthly_revenue(records)->dict 'YYYY-MM'->total. Include assert-based self-checks under if __name__ == '__main__': with a small sample dataset. python sales.py must exit 0 when correct.` },
  { id:'task-12', title:'Refactor over-engineered code', domain:'Refactor', difficulty:'Complex', lang:'python',
    spec:`Refactor the following Python into the simplest correct code that preserves the PUBLIC functions add(a, b) and average(numbers). Required behavior: add(a,b) returns a+b; average(numbers) returns the arithmetic mean of ALL the numbers (sum of all divided by count). The given code has a bug in average. Write the result to solution.py with assert-based self-checks under if __name__ == '__main__': (e.g. add(2,3)==5, average([1,2,3,4])==2.5). python solution.py must exit 0 when correct.

GIVEN CODE:

class OperationStrategy:
    def execute(self, a, b):
        raise NotImplementedError

class AddStrategy(OperationStrategy):
    def execute(self, a, b):
        return a + b

class OperationFactory:
    def __init__(self):
        self._registry = {}
    def register(self, name, strat):
        self._registry[name] = strat
    def create(self, name):
        return self._registry[name]

_factory = OperationFactory()
_factory.register('add', AddStrategy())

def add(a, b):
    strat = _factory.create('add')
    return strat.execute(a, b)

class AverageCalculator:
    def __init__(self, numbers):
        self.numbers = numbers
    def compute(self):
        total = 0
        for i in range(len(self.numbers) - 1):
            total += self.numbers[i]
        return total / len(self.numbers)

def average(numbers):
    return AverageCalculator(numbers).compute()` },
]

const BUILD_SCHEMA = {
  type:'object', additionalProperties:false,
  required:['filesCreated','primaryFile','runCommand','notes'],
  properties:{
    filesCreated:{ type:'array', items:{type:'string'} },
    primaryFile:{ type:'string' },
    runCommand:{ type:'string', description:'exact command to run the self-check or start the app, run from inside the build dir; empty if none' },
    notes:{ type:'string', description:'<=3 short lines on approach / what was skipped' },
  },
}

const SCORES = {
  type:'object', additionalProperties:false,
  required:['code_quality','readability','functionality','instruction_following','production_readiness','maintainability','robustness'],
  properties:{
    code_quality:{type:'integer',minimum:1,maximum:10},
    readability:{type:'integer',minimum:1,maximum:10},
    functionality:{type:'integer',minimum:1,maximum:10},
    instruction_following:{type:'integer',minimum:1,maximum:10},
    production_readiness:{type:'integer',minimum:1,maximum:10},
    maintainability:{type:'integer',minimum:1,maximum:10},
    robustness:{type:'integer',minimum:1,maximum:10},
  },
}
const WHO = { enum:['A','B','tie'] }
const JUDGE_SCHEMA = {
  type:'object', additionalProperties:false,
  required:['A','B','bugs_A','bugs_B','overall_winner','more_production_ready','better_instruction_following','summary'],
  properties:{
    A: SCORES, B: SCORES,
    bugs_A:{type:'array',items:{type:'string'}},
    bugs_B:{type:'array',items:{type:'string'}},
    overall_winner: WHO,
    more_production_ready: WHO,
    better_instruction_following: WHO,
    summary:{type:'string', description:'2-4 sentence head-to-head rationale'},
  },
}

function buildPrompt(task, dir, withPony){
  const body = `You are a senior software engineer. Implement the task below completely and correctly.

TASK ID: ${task.id} — ${task.title} (${task.domain}, ${task.difficulty})

TASK:
${task.spec}

OUTPUT RULES (follow exactly):
- Write ALL files into EXACTLY this directory using absolute paths: ${dir}
- Do NOT create, read, modify, or delete anything outside that directory. Do not init git, do not run package installers.
- Produce complete, working code that fully satisfies the task. No placeholders, no TODOs.
- Then return the structured summary: files created, the primary file, the exact runCommand to verify it from inside that directory, and brief notes.`
  if (!withPony) return body
  return `${PONYTAIL}

----
The Ponytail skill above is ACTIVE at FULL intensity for this task. Apply it throughout.

${body}`
}

// ============ PHASE 1: BUILD (sequential, token-measured) ============
phase('Build')
const spent = () => { try { return budget.spent() || 0 } catch { return 0 } }
const builds = []
for (let i=0; i<TASKS.length; i++){
  const t = TASKS[i]
  // blind mapping: alternate which physical folder (A/B) holds which arm
  const aIsBaseline = (i % 2 === 0)
  const dirA = `${BASE}/${t.id}/A`
  const dirB = `${BASE}/${t.id}/B`
  const baselineDir = aIsBaseline ? dirA : dirB
  const ponytailDir = aIsBaseline ? dirB : dirA

  const b0 = spent()
  const baseRes = await agent(buildPrompt(t, baselineDir, false),
    { label:`build:${t.id}:baseline`, phase:'Build', schema: BUILD_SCHEMA, agentType:'general-purpose' })
  const baseTok = Math.max(0, spent() - b0)

  const p0 = spent()
  const ponyRes = await agent(buildPrompt(t, ponytailDir, true),
    { label:`build:${t.id}:ponytail`, phase:'Build', schema: BUILD_SCHEMA, agentType:'general-purpose' })
  const ponyTok = Math.max(0, spent() - p0)

  builds.push({
    id:t.id, title:t.title, domain:t.domain, difficulty:t.difficulty, lang:t.lang,
    aIsBaseline, dirA, dirB, baselineDir, ponytailDir,
    baselineTokens: baseTok, ponytailTokens: ponyTok,
    baselineSummary: baseRes, ponytailSummary: ponyRes,
  })
  log(`${t.id} built — baseline ${baseTok} tok, ponytail ${ponyTok} tok`)
}

// ============ PHASE 2: JUDGE (parallel; 2 blind perspective-diverse judges per task) ============
phase('Judge')
const JUDGES = [
  { key:'reviewer', persona:'You are a meticulous staff software engineer doing a rigorous code review. Weight correctness, robustness, error handling, security, and production-readiness heavily. Reward code that actually works on edge cases.' },
  { key:'lead',     persona:'You are a pragmatic tech lead. Weight simplicity, readability, maintainability, value-per-line, and how faithfully each submission followed the exact instructions. Penalize over-engineering and unrequested bloat, but also penalize anything broken or unsafe.' },
]

function judgePrompt(task, persona){
  const dirA = `${BASE}/${task.id}/A`
  const dirB = `${BASE}/${task.id}/B`
  return `${persona}

Two engineers independently solved the SAME task. You will compare them BLIND — folder names A and B are random labels and carry NO meaning; judge only the code.

THE TASK THEY WERE BOTH GIVEN:
${task.spec}

SUBMISSION A is in: ${dirA}
SUBMISSION B is in: ${dirB}

Steps:
1. Use Bash (ls / find) to list files in BOTH directories, then READ every source file in full in both. Do not modify any file.
2. If there is a self-check / runnable command, you MAY run it read-only to verify functionality (e.g. python the file, or node --check). Do not start long-running servers; for those, reason about correctness from the code.
3. Score EACH submission 1-10 (10=best) on every criterion: code_quality, readability, functionality (correctness vs the exact spec), instruction_following, production_readiness, maintainability, robustness (error handling / edge cases).
4. List concrete bugs or spec violations you found in each (empty array if none).
5. Decide overall_winner, more_production_ready, better_instruction_following as 'A', 'B', or 'tie'.
6. Give a 2-4 sentence head-to-head summary citing specifics.

Be discriminating: do not give identical scores unless the work is genuinely equal. Return the structured result.`
}

const judgments = await parallel(TASKS.map((t) => async () => {
  const results = await parallel(JUDGES.map(j => () =>
    agent(judgePrompt(t, j.persona),
      { label:`judge:${t.id}:${j.key}`, phase:'Judge', schema: JUDGE_SCHEMA, agentType:'general-purpose' })
      .then(r => r ? ({ judge:j.key, ...r }) : null)
  ))
  return { id:t.id, raw: results.filter(Boolean) }
}))

return { builds, judgments }
