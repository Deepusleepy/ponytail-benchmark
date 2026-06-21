'use strict';

const http = require('http');

const PORT = 3000;

const server = http.createServer((req, res) => {
  // Parse the path portion of the URL, ignoring any query string.
  const path = (req.url || '').split('?')[0];

  if (req.method === 'GET' && path === '/health') {
    const body = JSON.stringify({ status: 'ok', uptime: process.uptime() });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(body);
    return;
  }

  if (req.method === 'GET' && path === '/time') {
    const body = JSON.stringify({ now: new Date().toISOString() });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(body);
    return;
  }

  const body = JSON.stringify({ error: 'not found' });
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(body);
});

server.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});

module.exports = server;
