const http = require('http'), fs = require('fs'), path = require('path');
const { WebSocketServer } = require('ws');
const PORT = process.env.PORT || 3000;
const STATE_FILE = path.join(__dirname, 'state.json');
let state = null; // {id: sticky}
try { state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); } catch {}
let t = null;
const save = () => { clearTimeout(t); t = setTimeout(() => fs.writeFileSync(STATE_FILE, JSON.stringify(state)), 500); };
const server = http.createServer((req, res) => {
  if (req.url === '/' || req.url.startsWith('/?')) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    return res.end(fs.readFileSync(path.join(__dirname, 'index.html')));
  }
  res.writeHead(404); res.end();
});
const wss = new WebSocketServer({ server, path: '/ws' });
const count = () => JSON.stringify({ type: 'presence', n: wss.clients.size });
const broadcast = (msg, except) => wss.clients.forEach(c => { if (c !== except && c.readyState === 1) c.send(msg); });
wss.on('connection', ws => {
  ws.send(JSON.stringify({ type: 'state', seeded: state !== null, stickies: state ? Object.values(state) : [] }));
  broadcast(count()); ws.send(count());
  ws.on('message', raw => {
    let m; try { m = JSON.parse(raw); } catch { return; }
    if (m.type === 'seed' && state === null) { state = {}; m.stickies.forEach(s => state[s.id] = s); save(); broadcast(JSON.stringify({ type: 'state', seeded: true, stickies: Object.values(state) })); }
    else if (m.type === 'upsert' && state && m.s && m.s.id) { state[m.s.id] = m.s; save(); broadcast(JSON.stringify(m), ws); }
    else if (m.type === 'remove' && state) { delete state[m.id]; save(); broadcast(JSON.stringify(m), ws); }
  });
  ws.on('close', () => broadcast(count()));
});
server.listen(PORT, '0.0.0.0', () => console.log('Atelier board sur http://0.0.0.0:' + PORT));
