const http = require('http');

const json = (res, code, body) => {
  res.writeHead(code, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(body));
};

const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/health') {
    json(res, 200, { status: 'ok', uptime: process.uptime() });
  } else if (req.method === 'GET' && req.url === '/time') {
    json(res, 200, { now: new Date().toISOString() });
  } else {
    json(res, 404, { error: 'not found' });
  }
});

// ponytail: export when required (for the self-check), else listen.
if (require.main === module) {
  server.listen(3000, () => console.log('listening on 3000'));
}
module.exports = server;
