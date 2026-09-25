#!/usr/bin/env node
// Local preview server: serves the repo root as static files (open
// http://localhost:3737/site/index.html) and runs netlify/functions/* for
// /api/* requests, mirroring netlify.toml's redirect. Reads KEY=value lines
// from .env into process.env. Node standard library only.
//
// Usage: node scripts/dev-server.js [port]

const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const PORT = Number(process.argv[2]) || 3737;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.pdf': 'application/pdf',
  '.xml': 'application/xml',
  '.txt': 'text/plain; charset=utf-8',
  '.mp4': 'video/mp4',
};

function loadEnv() {
  const file = path.join(ROOT, '.env');
  if (!fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/i);
    if (m && !line.trim().startsWith('#')) process.env[m[1]] = m[2].replace(/^(['"])(.*)\1$/, '$2');
  }
}

async function runFunction(name, req, res) {
  const file = path.join(ROOT, 'netlify', 'functions', `${name}.js`);
  if (!/^[\w-]+$/.test(name) || !fs.existsSync(file)) {
    res.writeHead(404).end('Function not found');
    return;
  }
  let body = '';
  for await (const chunk of req) body += chunk;
  delete require.cache[require.resolve(file)]; // pick up edits without restarting
  try {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const result = await require(file).handler({
      httpMethod: req.method,
      headers: req.headers,
      body,
      path: url.pathname,
      queryStringParameters: Object.fromEntries(url.searchParams),
    });
    res.writeHead(result.statusCode || 200, result.headers || {}).end(result.body || '');
  } catch (err) {
    console.error(err);
    res.writeHead(500).end('Function error');
  }
}

function serveStatic(req, res) {
  const pathname = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  let file = path.join(ROOT, pathname);
  if (!file.startsWith(ROOT)) return res.writeHead(403).end();
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  fs.readFile(file, (err, data) => {
    if (err) return res.writeHead(404).end('Not found');
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream' });
    res.end(data);
  });
}

loadEnv();
http.createServer((req, res) => {
  const m = req.url.match(/^\/(?:api|\.netlify\/functions)\/([^/?]+)/);
  if (m) return runFunction(m[1], req, res);
  serveStatic(req, res);
}).listen(PORT, () => {
  console.log(`Reboot Camp dev server: http://localhost:${PORT}/site/index.html`);
  if (!process.env.BEEHIIV_API_KEY) console.log('(no BEEHIIV_API_KEY in .env: signup form will return an error)');
});
