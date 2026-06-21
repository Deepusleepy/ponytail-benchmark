'use strict';
const http = require('http');

// In-memory store. Lost on restart by design (task says in-memory).
const todos = new Map();
let nextId = 1;

function send(res, status, body) {
  if (body === undefined) return res.writeHead(status).end();
  const json = JSON.stringify(body);
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(json);
}

// Read body, parse JSON. Returns {} for empty body so PUT-with-nothing is a no-op.
function readJson(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    let tooBig = false;
    req.on('data', (c) => {
      data += c;
      if (data.length > 1e6) { tooBig = true; req.destroy(); } // ponytail: 1MB cap, plenty for a todo
    });
    req.on('end', () => {
      if (tooBig) return reject(new Error('payload too large'));
      if (data.trim() === '') return resolve({});
      try { resolve(JSON.parse(data)); } catch { reject(new Error('invalid JSON')); }
    });
    req.on('error', reject);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const path = url.pathname.replace(/\/+$/, '') || '/';
  const m = path.match(/^\/todos(?:\/(\d+))?$/);

  if (!m) return send(res, 404, { error: 'not found' });
  const id = m[1] ? Number(m[1]) : null;

  // Collection: /todos
  if (id === null) {
    if (req.method === 'GET') return send(res, 200, [...todos.values()]);
    if (req.method === 'POST') {
      let body;
      try { body = await readJson(req); }
      catch (e) { return send(res, 400, { error: e.message }); }
      if (typeof body.title !== 'string' || body.title.trim() === '')
        return send(res, 400, { error: 'title is required and must be a non-empty string' });
      const todo = { id: nextId++, title: body.title, done: false };
      todos.set(todo.id, todo);
      return send(res, 201, todo);
    }
    return send(res, 405, { error: 'method not allowed' });
  }

  // Item: /todos/:id
  if (req.method === 'GET') {
    const todo = todos.get(id);
    return todo ? send(res, 200, todo) : send(res, 404, { error: 'not found' });
  }
  if (req.method === 'PUT') {
    const todo = todos.get(id);
    if (!todo) return send(res, 404, { error: 'not found' });
    let body;
    try { body = await readJson(req); }
    catch (e) { return send(res, 400, { error: e.message }); }
    if (body.title !== undefined) {
      if (typeof body.title !== 'string' || body.title.trim() === '')
        return send(res, 400, { error: 'title must be a non-empty string' });
      todo.title = body.title;
    }
    if (body.done !== undefined) {
      if (typeof body.done !== 'boolean')
        return send(res, 400, { error: 'done must be a boolean' });
      todo.done = body.done;
    }
    return send(res, 200, todo);
  }
  if (req.method === 'DELETE') {
    return todos.delete(id) ? send(res, 204) : send(res, 404, { error: 'not found' });
  }
  return send(res, 405, { error: 'method not allowed' });
});

// Don't listen when required by the test harness.
if (require.main === module) {
  server.listen(3000, () => console.log('Todo API on http://localhost:3000'));
}

module.exports = server;
