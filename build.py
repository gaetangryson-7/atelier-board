s = open('original.html', encoding='utf-8').read()
def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)
rep("""        el.classList.remove('editing');
        textEl.contentEditable = 'false';
      });""", """        el.classList.remove('editing');
        textEl.contentEditable = 'false';
        window.__sync && __sync.upsert(el);
      });
      textEl.addEventListener('input', () => window.__sync && __sync.upsertThrottled(el));""")
rep("el.dataset.color = next;\n", "el.dataset.color = next;\n        window.__sync && __sync.upsert(el);\n")
rep("        el.remove();\n        showToast('Post-it supprimé');", "        window.__sync && __sync.remove(el.dataset.id);\n        el.remove();\n        showToast('Post-it supprimé');")
rep("el.style.top = `${Math.round(dragStartPos.y + dy)}px`;\n", "el.style.top = `${Math.round(dragStartPos.y + dy)}px`;\n        window.__sync && __sync.upsertThrottled(el);\n")
rep("        isDraggingSticky = false;\n        el.classList.remove('dragging');", "        isDraggingSticky = false;\n        el.classList.remove('dragging');\n        window.__sync && __sync.upsert(el);")
rep("      stickyLayer.appendChild(el);\n      return el;", "      stickyLayer.appendChild(el);\n      if (window.__sync && !__sync.applying) __sync.upsert(el);\n      return el;")
client = r"""
  <script>
  /* === SYNC TEMPS REEL (WebSocket) === */
  (() => {
    const badge = document.createElement('div');
    badge.style.cssText = 'position:fixed;right:14px;bottom:14px;z-index:9999;background:#233742;color:#fff;font:600 12px Montserrat,sans-serif;padding:6px 12px;border-radius:12px 18px 12px 12px;opacity:.9';
    badge.textContent = 'Connexion…'; document.body.appendChild(badge);
    const sync = window.__sync = { applying: false, ws: null, timers: {} };
    const ser = el => ({ id: el.dataset.id, x: parseFloat(el.style.left)||0, y: parseFloat(el.style.top)||0,
      w: parseFloat(el.style.width)||240, h: parseFloat(el.style.minHeight)||110, color: el.dataset.color,
      text: el.querySelector('.sticky-text').textContent });
    const send = o => { if (sync.ws && sync.ws.readyState === 1) sync.ws.send(JSON.stringify(o)); };
    sync.upsert = el => send({ type: 'upsert', s: ser(el) });
    sync.upsertThrottled = el => { if (sync.timers[el.dataset.id]) return;
      sync.timers[el.dataset.id] = setTimeout(() => { delete sync.timers[el.dataset.id]; sync.upsert(el); }, 60); };
    sync.remove = id => send({ type: 'remove', id });
    const find = id => [...document.querySelectorAll('#sticky-layer .sticky-note')].find(e => e.dataset.id === id);
    const apply = s => {
      sync.applying = true;
      let el = find(s.id);
      if (!el) createStickyElement(s);
      else {
        if (!el.classList.contains('dragging')) { el.style.left = s.x + 'px'; el.style.top = s.y + 'px'; }
        el.style.width = s.w + 'px'; el.style.minHeight = s.h + 'px';
        if (el.dataset.color !== s.color) { el.classList.remove('sticky-' + el.dataset.color); el.classList.add('sticky-' + s.color); el.dataset.color = s.color; }
        const t = el.querySelector('.sticky-text');
        if (!el.classList.contains('editing') && t.textContent !== s.text) t.textContent = s.text;
      }
      sync.applying = false;
    };
    function connect() {
      const ws = sync.ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws');
      ws.onclose = () => { badge.textContent = 'Déconnecté — reconnexion…'; setTimeout(connect, 1500); };
      ws.onmessage = ev => {
        const m = JSON.parse(ev.data);
        if (m.type === 'state') {
          if (!m.seeded) { send({ type: 'seed', stickies: [...document.querySelectorAll('#sticky-layer .sticky-note')].map(ser) }); return; }
          const ids = new Set(m.stickies.map(s => s.id));
          document.querySelectorAll('#sticky-layer .sticky-note').forEach(e => { if (!ids.has(e.dataset.id)) e.remove(); });
          m.stickies.forEach(apply);
        } else if (m.type === 'upsert') apply(m.s);
        else if (m.type === 'remove') { const e = find(m.id); if (e) e.remove(); }
        else if (m.type === 'presence') badge.textContent = '● ' + m.n + ' connecté' + (m.n > 1 ? 's' : '');
      };
    }
    connect();
  })();
  </script>
</body>"""
assert s.count('</body>') == 1
s = s.replace('</body>', client)
open('index.html', 'w', encoding='utf-8').write(s)
