'use strict';
// Self-check: boots the server, hits every endpoint, asserts status + shape.
const assert = require('assert');
const server = require('./server');

function req(method, path, body) {
  return new Promise((resolve, reject) => {
    const data = body === undefined ? null : JSON.stringify(body);
    const r = require('http').request(
      { method, host: 'localhost', port: 3000, path,
        headers: data ? { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } : {} },
      (res) => {
        let buf = '';
        res.on('data', (c) => (buf += c));
        res.on('end', () => resolve({ status: res.statusCode, body: buf ? JSON.parse(buf) : undefined }));
      }
    );
    r.on('error', reject);
    if (data) r.write(data);
    r.end();
  });
}

(async () => {
  await new Promise((ok) => server.listen(3000, ok));
  try {
    let r = await req('GET', '/todos');
    assert.strictEqual(r.status, 200); assert.deepStrictEqual(r.body, []);

    r = await req('POST', '/todos', { title: 'buy milk' });
    assert.strictEqual(r.status, 201);
    assert.deepStrictEqual(r.body, { id: 1, title: 'buy milk', done: false });
    const id = r.body.id;

    r = await req('POST', '/todos', { title: '' });
    assert.strictEqual(r.status, 400);
    r = await req('POST', '/todos', {});
    assert.strictEqual(r.status, 400);
    r = await req('POST', '/todos', { title: 42 });
    assert.strictEqual(r.status, 400);

    r = await req('GET', '/todos');
    assert.strictEqual(r.status, 200); assert.strictEqual(r.body.length, 1);

    r = await req('GET', `/todos/${id}`);
    assert.strictEqual(r.status, 200); assert.strictEqual(r.body.title, 'buy milk');
    r = await req('GET', '/todos/9999');
    assert.strictEqual(r.status, 404);

    r = await req('PUT', `/todos/${id}`, { done: true });
    assert.strictEqual(r.status, 200); assert.strictEqual(r.body.done, true);
    r = await req('PUT', `/todos/${id}`, { title: 'buy oat milk' });
    assert.strictEqual(r.status, 200); assert.strictEqual(r.body.title, 'buy oat milk');
    r = await req('PUT', `/todos/${id}`, { title: '' });
    assert.strictEqual(r.status, 400);
    r = await req('PUT', `/todos/${id}`, { done: 'yes' });
    assert.strictEqual(r.status, 400);
    r = await req('PUT', '/todos/9999', { done: true });
    assert.strictEqual(r.status, 404);

    r = await req('DELETE', `/todos/${id}`);
    assert.strictEqual(r.status, 204); assert.strictEqual(r.body, undefined);
    r = await req('DELETE', `/todos/${id}`);
    assert.strictEqual(r.status, 404);
    r = await req('GET', `/todos/${id}`);
    assert.strictEqual(r.status, 404);

    r = await req('POST', '/todos', 'not json');
    assert.strictEqual(r.status, 400);

    console.log('All checks passed.');
  } finally {
    server.close();
  }
})().catch((e) => { console.error(e); process.exit(1); });
