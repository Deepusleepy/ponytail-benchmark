'use strict';

// Token-bucket rate limiter as middleware for the built-in http server.
// Per-client-IP buckets. Built-in modules only.

/**
 * @param {object} opts
 * @param {number} opts.capacity   max tokens a bucket holds (burst size)
 * @param {number} opts.refillRate tokens added per second
 * @returns {(req, res, next) => void} middleware; calls next() when allowed
 */
function rateLimiter({ capacity, refillRate } = {}) {
  if (!(capacity > 0) || !(refillRate > 0)) {
    throw new Error('rateLimiter: capacity and refillRate must be positive numbers');
  }

  const buckets = new Map(); // ip -> { tokens, last }

  function take(ip, now) {
    let b = buckets.get(ip);
    if (!b) {
      b = { tokens: capacity, last: now };
      buckets.set(ip, b);
    }
    // Refill based on elapsed time, capped at capacity.
    const elapsedSec = (now - b.last) / 1000;
    b.tokens = Math.min(capacity, b.tokens + elapsedSec * refillRate);
    b.last = now;

    if (b.tokens >= 1) {
      b.tokens -= 1;
      return { allowed: true };
    }
    // Seconds until the bucket holds one whole token. Round up so Retry-After
    // never tells the client to retry too early.
    const retryAfter = Math.ceil((1 - b.tokens) / refillRate);
    return { allowed: false, retryAfter };
  }

  return function middleware(req, res, next) {
    // req.socket.remoteAddress is the trust boundary here. Behind a proxy you'd
    // parse X-Forwarded-For instead.
    // ponytail: trusts the direct socket IP. Ceiling: spoofable behind a proxy;
    // upgrade path = read the leftmost trusted X-Forwarded-For hop.
    const ip = (req.socket && req.socket.remoteAddress) || 'unknown';
    const { allowed, retryAfter } = take(ip, Date.now());

    if (allowed) {
      if (typeof next === 'function') next();
      return;
    }

    res.writeHead(429, {
      'Content-Type': 'application/json',
      'Retry-After': String(retryAfter),
    });
    res.end(JSON.stringify({ error: 'rate limited' }));
  };
}

module.exports = rateLimiter;

// ---- Self-check ----
if (require.main === module) {
  const assert = require('assert');

  // Fake req/res just enough for the middleware.
  function fakeReq(ip) {
    return { socket: { remoteAddress: ip } };
  }
  function fakeRes() {
    return {
      statusCode: 0,
      headers: null,
      body: '',
      writeHead(code, headers) { this.statusCode = code; this.headers = headers; },
      end(body) { this.body = body || ''; },
    };
  }
  // Runs the middleware once; returns { passed, res }.
  function hit(mw, ip) {
    let passed = false;
    const res = fakeRes();
    mw(fakeReq(ip), res, () => { passed = true; });
    return { passed, res };
  }

  // 1) Allow up to capacity, then block.
  {
    const capacity = 5;
    const mw = rateLimiter({ capacity, refillRate: 1 });
    const ip = '10.0.0.1';

    for (let i = 0; i < capacity; i++) {
      assert.strictEqual(hit(mw, ip).passed, true, `request ${i + 1} should pass`);
    }
    const blocked = hit(mw, ip);
    assert.strictEqual(blocked.passed, false, 'request over capacity should block');
    assert.strictEqual(blocked.res.statusCode, 429);
    assert.deepStrictEqual(JSON.parse(blocked.res.body), { error: 'rate limited' });
    const ra = Number(blocked.res.headers['Retry-After']);
    assert.ok(ra >= 1, 'Retry-After should be >= 1 second');
    console.log('ok 1 - allows capacity then blocks (Retry-After=%d)', ra);
  }

  // 2) Independent buckets per IP.
  {
    const mw = rateLimiter({ capacity: 1, refillRate: 1 });
    assert.strictEqual(hit(mw, '1.1.1.1').passed, true);
    assert.strictEqual(hit(mw, '1.1.1.1').passed, false, 'same IP exhausted');
    assert.strictEqual(hit(mw, '2.2.2.2').passed, true, 'different IP unaffected');
    console.log('ok 2 - buckets are per-IP');
  }

  // 3) Refills over time.
  {
    // High refill rate so the test is fast: 20 tokens/sec -> 1 token in 50ms.
    const mw = rateLimiter({ capacity: 1, refillRate: 20 });
    const ip = '3.3.3.3';
    assert.strictEqual(hit(mw, ip).passed, true, 'first token spent');
    assert.strictEqual(hit(mw, ip).passed, false, 'bucket empty');

    setTimeout(() => {
      assert.strictEqual(hit(mw, ip).passed, true, 'should refill after waiting');
      console.log('ok 3 - refills over time');
      console.log('all self-checks passed');
    }, 120); // > 50ms needed for one token, with margin
  }
}
