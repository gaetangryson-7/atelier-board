s = open('original.html', encoding='utf-8').read()
def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)

# --- Correctifs taille / redimensionnement ---
rep("    .sticky-actions {\n      opacity: 0;\n      transition: opacity 0.15s ease;\n    }",
"""    .sticky-actions {
      opacity: 0;
      transition: opacity 0.15s ease;
      position: absolute;
      left: 10px; right: 22px; bottom: 3px;
      margin: 0 !important; padding-top: 0 !important; border-top: 0 !important;
    }
    .sticky-note { padding: 10px 12px 22px !important; overflow: hidden; }
    .sticky-note.compact { font-size: 12px; line-height: 1.25; padding: 6px 8px 18px !important; }
    .sticky-note.compact .sticky-actions span { display: none; }
    .sticky-resize {
      position: absolute; right: 0; bottom: 0; width: 20px; height: 20px; cursor: nwse-resize;
      background: linear-gradient(135deg, transparent 50%, rgba(35,55,66,.45) 50%);
      border-radius: 0 0 4px 0; z-index: 5; touch-action: none;
    }""")
rep("      const textEl = el.querySelector('.sticky-text');\n",
"""      const textEl = el.querySelector('.sticky-text');
      if ((data.w || 240) < 200) el.classList.add('compact');
      const rz = document.createElement('div');
      rz.className = 'sticky-resize'; rz.title = 'Redimensionner';
      el.appendChild(rz);
      rz.addEventListener('mousedown', (e) => {
        e.stopPropagation(); e.preventDefault();
        const sx = e.clientX, sy = e.clientY;
        const sw = el.offsetWidth, sh = el.offsetHeight;
        const mv = (ev) => {
          const nw = Math.max(90, Math.round(sw + (ev.clientX - sx) / camera.scale));
          const nh = Math.max(50, Math.round(sh + (ev.clientY - sy) / camera.scale));
          el.style.width = nw + 'px'; el.style.minHeight = nh + 'px';
          el.classList.toggle('compact', nw < 200);
          window.__sync && __sync.upsertThrottled(el);
        };
        const up = () => { window.removeEventListener('mousemove', mv); window.removeEventListener('mouseup', up); window.__sync && __sync.upsert(el); };
        window.addEventListener('mousemove', mv); window.addEventListener('mouseup', up);
      });
""")
rep("if (e.target.closest('button') || el.classList.contains('editing')) return;\n        e.stopPropagation();\n        startDrag(e.clientX, e.clientY);",
    "if (e.target.closest('button') || e.target.closest('.sticky-resize') || el.classList.contains('editing')) return;\n        e.stopPropagation();\n        startDrag(e.clientX, e.clientY);")
# cases de la matrice : le post-it épouse exactement la case
rep("w: Math.max(140, Math.round(worldW)),\n          h: Math.max(76, Math.round(worldH)),",
    "w: Math.round(worldW),\n          h: Math.round(worldH),")
# exemples pré-remplis alignés sur la case de la ligne 1
rep("{ id: 's25', x: 4045, y: 345, w: 215, h: 86,", "{ id: 's25', x: 4043, y: 370, w: 220, h: 100,")
rep("{ id: 's26', x: 4278, y: 345, w: 145, h: 86,", "{ id: 's26', x: 4276, y: 370, w: 142, h: 100,")

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
