'use strict';

/**
 * Token-bucket rate limiter as HTTP middleware for Node's built-in http server.
 *
 * Built-in modules only.
 *
 * Per-client-IP buckets. Each bucket holds up to `capacity` tokens and refills
 * continuously at `refillRate` tokens/second. Every request consumes one token.
 * When no token is available, the middleware responds 429 with a `Retry-After`
 * header (seconds until the next token is available) and JSON {"error":"rate limited"}.
 */

/**
 * A single token bucket. Tokens are tracked as a fractional amount and refilled
 * lazily based on elapsed time, so no timers are required per bucket.
 */
class TokenBucket {
  /**
   * @param {number} capacity   Maximum number of tokens the bucket can hold.
   * @param {number} refillRate Tokens added per second.
   * @param {() => number} now  Clock function returning milliseconds.
   */
  constructor(capacity, refillRate, now) {
    this.capacity = capacity;
    this.refillRate = refillRate;
    this.now = now;
    this.tokens = capacity; // start full
    this.last = now();
  }

  /**
   * Refill the bucket based on time elapsed since the last update.
   */
  _refill() {
    const t = this.now();
    const elapsedSec = (t - this.last) / 1000;
    if (elapsedSec > 0) {
      this.tokens = Math.min(this.capacity, this.tokens + elapsedSec * this.refillRate);
      this.last = t;
    }
  }

  /**
   * Attempt to consume a single token.
   * @returns {{ allowed: boolean, retryAfterSec: number }}
   *   allowed: whether a token was consumed.
   *   retryAfterSec: when not allowed, whole seconds until the next token (>= 1);
   *                  0 when allowed.
   */
  tryRemove() {
    this._refill();
    if (this.tokens >= 1) {
      this.tokens -= 1;
      return { allowed: true, retryAfterSec: 0 };
    }
    // Time (in seconds) until we accumulate the remaining fraction of a token.
    const needed = 1 - this.tokens;
    let waitSec = this.refillRate > 0 ? needed / this.refillRate : Infinity;
    // Retry-After must be a non-negative integer number of seconds. Round up so
    // the client does not retry before a token is actually available.
    let retryAfterSec = Number.isFinite(waitSec) ? Math.ceil(waitSec) : Number.MAX_SAFE_INTEGER;
    if (retryAfterSec < 1) retryAfterSec = 1;
    return { allowed: false, retryAfterSec };
  }
}

/**
 * Extract a client IP from the request.
 * @param {import('http').IncomingMessage} req
 * @returns {string}
 */
function clientIp(req) {
  // socket may be undefined in unusual cases; fall back to a stable key.
  const sock = req.socket || req.connection;
  return (sock && (sock.remoteAddress || '')) || 'unknown';
}

/**
 * Create a token-bucket rate limiting middleware.
 *
 * @param {object} [options]
 * @param {number} [options.capacity=10]       Max tokens (burst size) per IP.
 * @param {number} [options.refillRate=1]      Tokens refilled per second per IP.
 * @param {(req: import('http').IncomingMessage) => string} [options.keyGenerator]
 *        Function deriving the bucket key from a request (defaults to client IP).
 * @param {number} [options.cleanupIntervalMs=60000]
 *        How often idle/full buckets are garbage-collected. Set to 0 to disable.
 * @param {() => number} [options.now=Date.now] Clock (ms); injectable for tests.
 *
 * @returns {Function} middleware(req, res, next?) — Connect/Express-style.
 *          The returned function also exposes:
 *            - .buckets : Map<string, TokenBucket>
 *            - .stop()  : clears the internal cleanup timer.
 */
function createRateLimiter(options = {}) {
  const capacity = options.capacity != null ? options.capacity : 10;
  const refillRate = options.refillRate != null ? options.refillRate : 1;
  const now = options.now || Date.now;
  const keyGenerator = options.keyGenerator || clientIp;
  const cleanupIntervalMs =
    options.cleanupIntervalMs != null ? options.cleanupIntervalMs : 60000;

  if (!(capacity > 0)) {
    throw new TypeError('capacity must be a positive number');
  }
  if (!(refillRate > 0)) {
    throw new TypeError('refillRate must be a positive number');
  }

  /** @type {Map<string, TokenBucket>} */
  const buckets = new Map();

  function getBucket(key) {
    let b = buckets.get(key);
    if (!b) {
      b = new TokenBucket(capacity, refillRate, now);
      buckets.set(key, b);
    }
    return b;
  }

  // Periodically drop buckets that have refilled back to capacity (i.e. the
  // client has been idle long enough), to avoid unbounded memory growth.
  let timer = null;
  if (cleanupIntervalMs > 0) {
    timer = setInterval(() => {
      for (const [key, bucket] of buckets) {
        bucket._refill();
        if (bucket.tokens >= bucket.capacity) {
          buckets.delete(key);
        }
      }
    }, cleanupIntervalMs);
    // Do not keep the event loop alive solely for cleanup.
    if (timer && typeof timer.unref === 'function') timer.unref();
  }

  /**
   * @param {import('http').IncomingMessage} req
   * @param {import('http').ServerResponse} res
   * @param {Function} [next]
   */
  function middleware(req, res, next) {
    const key = keyGenerator(req);
    const bucket = getBucket(key);
    const { allowed, retryAfterSec } = bucket.tryRemove();

    if (allowed) {
      if (typeof next === 'function') return next();
      return true;
    }

    // Rate limited.
    res.statusCode = 429;
    res.setHeader('Retry-After', String(retryAfterSec));
    res.setHeader('Content-Type', 'application/json');
    const body = JSON.stringify({ error: 'rate limited' });
    res.end(body);
    return false;
  }

  middleware.buckets = buckets;
  middleware.stop = function stop() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  };

  return middleware;
}

module.exports = createRateLimiter;
module.exports.createRateLimiter = createRateLimiter;
module.exports.TokenBucket = TokenBucket;

// ---------------------------------------------------------------------------
// Runnable self-check
// ---------------------------------------------------------------------------
if (require.main === module) {
  const assert = require('assert');
  const http = require('http');

  // A controllable clock so the time-based assertions are deterministic.
  let fakeNow = 1000000;
  const now = () => fakeNow;

  /**
   * Minimal stand-ins for http req/res so we can drive the middleware without
   * opening sockets in the unit-style checks.
   */
  function makeReq(ip) {
    return { socket: { remoteAddress: ip } };
  }
  function makeRes() {
    return {
      statusCode: 200,
      headers: {},
      ended: false,
      body: undefined,
      setHeader(name, value) {
        this.headers[name.toLowerCase()] = value;
      },
      getHeader(name) {
        return this.headers[name.toLowerCase()];
      },
      end(body) {
        this.ended = true;
        this.body = body;
      },
    };
  }

  function call(limiter, ip) {
    const req = makeReq(ip);
    const res = makeRes();
    const allowed = limiter(req, res); // no next() -> returns boolean
    return { allowed, res };
  }

  console.log('Running self-check...');

  // --- Test 1: allows up to capacity, then blocks ------------------------
  {
    const capacity = 5;
    const refillRate = 1; // 1 token/sec
    const limiter = createRateLimiter({ capacity, refillRate, now });
    const ip = '203.0.113.7';

    // First `capacity` rapid requests (no time passes) should be allowed.
    for (let i = 0; i < capacity; i++) {
      const { allowed, res } = call(limiter, ip);
      assert.strictEqual(allowed, true, `request ${i + 1} should be allowed`);
      assert.strictEqual(res.statusCode, 200, `request ${i + 1} status`);
    }

    // The next request has no tokens left -> 429.
    const blocked = call(limiter, ip);
    assert.strictEqual(blocked.allowed, false, 'request over capacity should be blocked');
    assert.strictEqual(blocked.res.statusCode, 429, 'blocked status should be 429');
    assert.strictEqual(
      blocked.res.getHeader('Content-Type'),
      'application/json',
      'blocked Content-Type'
    );
    assert.deepStrictEqual(
      JSON.parse(blocked.res.body),
      { error: 'rate limited' },
      'blocked body JSON'
    );

    // Retry-After should be a positive integer (seconds until next token).
    const retryAfter = Number(blocked.res.getHeader('Retry-After'));
    assert.ok(Number.isInteger(retryAfter) && retryAfter >= 1, 'Retry-After >= 1');
    // With refillRate=1 token/sec and an empty bucket, next token is ~1s away.
    assert.strictEqual(retryAfter, 1, 'Retry-After should be 1s at 1 token/sec');

    limiter.stop();
    console.log('  [pass] allows up to capacity then blocks (429 + Retry-After + JSON)');
  }

  // --- Test 2: refills over time -----------------------------------------
  {
    const capacity = 3;
    const refillRate = 2; // 2 tokens/sec -> 1 token every 500ms
    const limiter = createRateLimiter({ capacity, refillRate, now });
    const ip = '198.51.100.42';

    // Drain the bucket.
    for (let i = 0; i < capacity; i++) {
      assert.strictEqual(call(limiter, ip).allowed, true, `drain ${i + 1}`);
    }
    // Now blocked.
    assert.strictEqual(call(limiter, ip).allowed, false, 'blocked after drain');

    // Advance < 500ms: still no full token.
    fakeNow += 400;
    assert.strictEqual(call(limiter, ip).allowed, false, 'still blocked after 400ms');

    // Advance to cross the 500ms boundary (total 600ms -> 1.2 tokens available).
    fakeNow += 200;
    assert.strictEqual(call(limiter, ip).allowed, true, 'allowed after refill (~600ms)');

    // That consumed the refilled token; immediately blocked again.
    assert.strictEqual(call(limiter, ip).allowed, false, 'blocked again after consuming refill');

    // Advance well beyond capacity-worth of refill; should cap at capacity.
    fakeNow += 10000;
    for (let i = 0; i < capacity; i++) {
      assert.strictEqual(call(limiter, ip).allowed, true, `post-refill burst ${i + 1}`);
    }
    assert.strictEqual(call(limiter, ip).allowed, false, 'capped at capacity after long idle');

    limiter.stop();
    console.log('  [pass] refills over time and caps at capacity');
  }

  // --- Test 3: buckets are per-IP ----------------------------------------
  {
    const limiter = createRateLimiter({ capacity: 1, refillRate: 1, now });
    const a = call(limiter, '10.0.0.1');
    const b = call(limiter, '10.0.0.2');
    assert.strictEqual(a.allowed, true, 'IP A first request allowed');
    assert.strictEqual(b.allowed, true, 'IP B first request allowed (independent bucket)');
    // Each is now exhausted independently.
    assert.strictEqual(call(limiter, '10.0.0.1').allowed, false, 'IP A second blocked');
    assert.strictEqual(call(limiter, '10.0.0.2').allowed, false, 'IP B second blocked');
    limiter.stop();
    console.log('  [pass] buckets are isolated per client IP');
  }

  // --- Test 4: end-to-end over a real http server ------------------------
  {
    const limiter = createRateLimiter({ capacity: 2, refillRate: 1 }); // real Date.now
    const server = http.createServer((req, res) => {
      limiter(req, res, () => {
        res.statusCode = 200;
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({ ok: true }));
      });
    });

    function request(port) {
      return new Promise((resolve, reject) => {
        const req = http.request(
          { host: '127.0.0.1', port, path: '/', method: 'GET' },
          (res) => {
            let data = '';
            res.on('data', (c) => (data += c));
            res.on('end', () =>
              resolve({
                status: res.statusCode,
                retryAfter: res.headers['retry-after'],
                body: data,
              })
            );
          }
        );
        req.on('error', reject);
        req.end();
      });
    }

    server.listen(0, '127.0.0.1', async () => {
      try {
        const port = server.address().port;
        const r1 = await request(port);
        const r2 = await request(port);
        const r3 = await request(port);

        assert.strictEqual(r1.status, 200, 'e2e request 1 allowed');
        assert.strictEqual(r2.status, 200, 'e2e request 2 allowed');
        assert.strictEqual(r3.status, 429, 'e2e request 3 rate limited');
        assert.strictEqual(JSON.parse(r3.body).error, 'rate limited', 'e2e 429 body');
        assert.ok(Number(r3.retryAfter) >= 1, 'e2e Retry-After present');

        console.log('  [pass] end-to-end over real http server (200,200,429)');
        console.log('All self-checks passed.');
      } catch (err) {
        console.error('Self-check FAILED:', err && err.message ? err.message : err);
        process.exitCode = 1;
      } finally {
        limiter.stop();
        server.close();
      }
    });
  }
}
