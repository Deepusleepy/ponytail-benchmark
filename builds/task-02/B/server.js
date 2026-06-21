'use strict';

const http = require('http');

const PORT = 3000;

// In-memory store
const todos = [];
let nextId = 1;

/**
 * Send a JSON response.
 */
function sendJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(body),
  });
  res.end(body);
}

/**
 * Send an empty response (used for 204 No Content).
 */
function sendEmpty(res, statusCode) {
  res.writeHead(statusCode);
  res.end();
}

/**
 * Read and parse a JSON request body.
 * Resolves with { ok: true, value } or { ok: false, error }.
 */
function readJsonBody(req) {
  return new Promise((resolve) => {
    const chunks = [];
    let size = 0;
    const MAX_BYTES = 1e6; // 1MB safety limit

    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_BYTES) {
        // Stop accumulating; will error out on end.
        req.destroy();
        resolve({ ok: false, error: 'Request body too large' });
        return;
      }
      chunks.push(chunk);
    });

    req.on('end', () => {
      const raw = Buffer.concat(chunks).toString('utf8').trim();
      if (raw === '') {
        // Empty body -> treat as empty object.
        resolve({ ok: true, value: {} });
        return;
      }
      try {
        const parsed = JSON.parse(raw);
        if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
          resolve({ ok: false, error: 'Request body must be a JSON object' });
          return;
        }
        resolve({ ok: true, value: parsed });
      } catch (e) {
        resolve({ ok: false, error: 'Invalid JSON in request body' });
      }
    });

    req.on('error', () => {
      resolve({ ok: false, error: 'Error reading request body' });
    });
  });
}

/**
 * Find a todo and its index by id (numeric).
 */
function findTodo(id) {
  const index = todos.findIndex((t) => t.id === id);
  if (index === -1) {
    return { todo: null, index: -1 };
  }
  return { todo: todos[index], index };
}

/**
 * Parse an id segment into a positive integer, or null if invalid.
 */
function parseId(segment) {
  if (!/^\d+$/.test(segment)) {
    return null;
  }
  const id = Number(segment);
  return Number.isSafeInteger(id) ? id : null;
}

const server = http.createServer(async (req, res) => {
  const method = req.method;
  // Strip query string and trailing slash (but keep root "/").
  let pathname;
  try {
    pathname = decodeURIComponent(new URL(req.url, `http://localhost:${PORT}`).pathname);
  } catch (e) {
    sendJson(res, 400, { error: 'Invalid URL' });
    return;
  }
  if (pathname.length > 1 && pathname.endsWith('/')) {
    pathname = pathname.slice(0, -1);
  }

  const segments = pathname.split('/').filter((s) => s.length > 0);

  // Collection routes: /todos
  if (segments.length === 1 && segments[0] === 'todos') {
    if (method === 'GET') {
      sendJson(res, 200, todos);
      return;
    }

    if (method === 'POST') {
      const parsed = await readJsonBody(req);
      if (!parsed.ok) {
        sendJson(res, 400, { error: parsed.error });
        return;
      }
      const { title } = parsed.value;
      if (typeof title !== 'string' || title.trim() === '') {
        sendJson(res, 400, { error: 'Field "title" is required and must be a non-empty string' });
        return;
      }
      const todo = { id: nextId++, title: title.trim(), done: false };
      todos.push(todo);
      sendJson(res, 201, todo);
      return;
    }

    sendJson(res, 405, { error: `Method ${method} not allowed on /todos` });
    return;
  }

  // Item routes: /todos/:id
  if (segments.length === 2 && segments[0] === 'todos') {
    const id = parseId(segments[1]);
    if (id === null) {
      sendJson(res, 400, { error: 'Invalid id; must be a positive integer' });
      return;
    }

    if (method === 'GET') {
      const { todo } = findTodo(id);
      if (!todo) {
        sendJson(res, 404, { error: 'Todo not found' });
        return;
      }
      sendJson(res, 200, todo);
      return;
    }

    if (method === 'PUT') {
      const { todo } = findTodo(id);
      if (!todo) {
        sendJson(res, 404, { error: 'Todo not found' });
        return;
      }
      const parsed = await readJsonBody(req);
      if (!parsed.ok) {
        sendJson(res, 400, { error: parsed.error });
        return;
      }
      const body = parsed.value;

      if (Object.prototype.hasOwnProperty.call(body, 'title')) {
        if (typeof body.title !== 'string' || body.title.trim() === '') {
          sendJson(res, 400, { error: 'Field "title" must be a non-empty string' });
          return;
        }
        todo.title = body.title.trim();
      }

      if (Object.prototype.hasOwnProperty.call(body, 'done')) {
        if (typeof body.done !== 'boolean') {
          sendJson(res, 400, { error: 'Field "done" must be a boolean' });
          return;
        }
        todo.done = body.done;
      }

      sendJson(res, 200, todo);
      return;
    }

    if (method === 'DELETE') {
      const { index } = findTodo(id);
      if (index === -1) {
        sendJson(res, 404, { error: 'Todo not found' });
        return;
      }
      todos.splice(index, 1);
      sendEmpty(res, 204);
      return;
    }

    sendJson(res, 405, { error: `Method ${method} not allowed on /todos/:id` });
    return;
  }

  // Anything else.
  sendJson(res, 404, { error: 'Not found' });
});

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Todo API listening on http://localhost:${PORT}`);
});

module.exports = server;
