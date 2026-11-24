s = open('index.html', encoding='utf-8').read()
i = s.index("  <script>\n  /* === SYNC TEMPS REEL")
head = s[:i]
client = r"""  <script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-database-compat.js"></script>
  <script>
  /* === SYNC TEMPS REEL (Firebase Realtime Database) === */
  const FIREBASE_CONFIG = {
    apiKey: "AIzaSyA580Vs_tvQ8kA_wGf0cYJUi0ChrEMm4Ys",
    authDomain: "atelier-board-pm.firebaseapp.com",
    databaseURL: "https://atelier-board-pm-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "atelier-board-pm"
  };
  const ROOM = new URLSearchParams(location.search).get('room') || 'atelier';
  (() => {
    const badge = document.createElement('div');
    badge.style.cssText = 'position:fixed;right:14px;bottom:14px;z-index:9999;background:#233742;color:#fff;font:600 12px Montserrat,sans-serif;padding:6px 12px;border-radius:12px 18px 12px 12px;opacity:.9';
    badge.textContent = 'Connexion…'; document.body.appendChild(badge);
    if (false) { badge.textContent = 'Mode local (Firebase non configuré)'; return; }
    firebase.initializeApp(FIREBASE_CONFIG);
    const db = firebase.database();
    const root = db.ref('rooms/' + ROOM);
    const sync = window.__sync = { applying: false, timers: {} };
    const ser = el => ({ id: el.dataset.id, x: parseFloat(el.style.left)||0, y: parseFloat(el.style.top)||0,
      w: parseFloat(el.style.width)||240, h: parseFloat(el.style.minHeight)||110, color: el.dataset.color,
      text: el.querySelector('.sticky-text').textContent });
    sync.upsert = el => root.child('stickies/' + el.dataset.id).set(ser(el));
    sync.upsertThrottled = el => { if (sync.timers[el.dataset.id]) return;
      sync.timers[el.dataset.id] = setTimeout(() => { delete sync.timers[el.dataset.id]; sync.upsert(el); }, 80); };
    sync.remove = id => root.child('stickies/' + id).remove();
    const find = id => [...document.querySelectorAll('#sticky-layer .sticky-note')].find(e => e.dataset.id === id);
    const apply = s => {
      if (!s) return;
      sync.applying = true;
      const el = find(s.id);
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
    // Retire les post-its de la maquette locale : la base fait foi
    const local = [...document.querySelectorAll('#sticky-layer .sticky-note')].map(ser);
    document.querySelectorAll('#sticky-layer .sticky-note').forEach(e => e.remove());
    // Seed unique (transaction) si la room est vide
    root.child('seeded').transaction(v => v ? undefined : true, (err, committed) => {
      if (committed) { const o = {}; local.forEach(s => o[s.id] = s); root.child('stickies').update(o); }
    });
    root.child('stickies').on('child_added', sn => apply(sn.val()));
    root.child('stickies').on('child_changed', sn => apply(sn.val()));
    root.child('stickies').on('child_removed', sn => { const e = find(sn.key); if (e) e.remove(); });
    // Présence
    const me = db.ref('rooms/' + ROOM + '/presence').push();
    db.ref('.info/connected').on('value', sn => { if (sn.val()) { me.onDisconnect().remove(); me.set(true); } });
    root.child('presence').on('value', sn => { const n = sn.numChildren();
      badge.textContent = '● ' + n + ' connecté' + (n > 1 ? 's' : ''); });
  })();
  </script>
</body>
</html>
"""
import os; os.makedirs('docs', exist_ok=True)
open('docs/index.html', 'w', encoding='utf-8').write(head + client)
