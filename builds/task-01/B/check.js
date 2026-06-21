const assert = require('assert');
const http = require('http');
const server = require('./server');

const get = (path) => new Promise((resolve, reject) => {
  http.get({ port: 3000, path }, (res) => {
    let data = '';
    res.on('data', (c) => (data += c));
    res.on('end', () => resolve({ res, body: JSON.parse(data) }));
  }).on('error', reject);
});

server.listen(3000, async () => {
  try {
    const h = await get('/health');
    assert.strictEqual(h.res.statusCode, 200);
    assert.strictEqual(h.res.headers['content-type'], 'application/json');
    assert.strictEqual(h.body.status, 'ok');
    assert.strictEqual(typeof h.body.uptime, 'number');

    const t = await get('/time');
    assert.strictEqual(t.res.statusCode, 200);
    assert.strictEqual(new Date(t.body.now).toISOString(), t.body.now);

    const nf = await get('/nope');
    assert.strictEqual(nf.res.statusCode, 404);
    assert.strictEqual(nf.body.error, 'not found');

    console.log('OK: all checks passed');
    server.close();
  } catch (e) {
    console.error('FAIL:', e.message);
    server.close();
    process.exit(1);
  }
});
