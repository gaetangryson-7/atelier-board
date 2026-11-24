s = open('index.html', encoding='utf-8').read()
i = s.index("  <script>\n  /* === SYNC TEMPS REEL")
head = s[:i]
for pre in ('user-s-', 'matrix-s-'):
    old = "`" + pre + "${stickyCounter}`"
    assert head.count(old) == 1, old
    head = head.replace(old, "`" + pre + "${stickyCounter}-${Math.random().toString(36).slice(2,7)}`")
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
    const ME = localStorage.getItem('atelier_uid') || ('u' + Math.random().toString(36).slice(2, 10));
    localStorage.setItem('atelier_uid', ME);
    let privateMode = false;
    const refreshVisibility = () => {
      document.querySelectorAll('#sticky-layer .sticky-note').forEach(el => {
        const a = el.dataset.author;
        el.style.display = (privateMode && a && a !== 'seed' && a !== ME) ? 'none' : '';
      });
    };
    const ser = el => ({ id: el.dataset.id, x: parseFloat(el.style.left)||0, y: parseFloat(el.style.top)||0,
      w: parseFloat(el.style.width)||240, h: parseFloat(el.style.minHeight)||110, color: el.dataset.color,
      text: el.querySelector('.sticky-text').textContent,
      author: (el.dataset.author = el.dataset.author || ME) });
    sync.upsert = el => root.child('stickies/' + el.dataset.id).set(ser(el));
    sync.upsertThrottled = el => { if (sync.timers[el.dataset.id]) return;
      sync.timers[el.dataset.id] = setTimeout(() => { delete sync.timers[el.dataset.id]; sync.upsert(el); }, 80); };
    sync.remove = id => root.child('stickies/' + id).remove();
    const find = id => [...document.querySelectorAll('#sticky-layer .sticky-note')].find(e => e.dataset.id === id);
    const apply = s => {
      if (!s) return;
      sync.applying = true;
      const el = find(s.id);
      if (!el) { createStickyElement(s); const n = find(s.id); if (n && s.author) n.dataset.author = s.author; }
      else {
        if (!el.classList.contains('dragging')) { el.style.left = s.x + 'px'; el.style.top = s.y + 'px'; }
        el.style.width = s.w + 'px'; el.style.minHeight = s.h + 'px';
        if (el.dataset.color !== s.color) { el.classList.remove('sticky-' + el.dataset.color); el.classList.add('sticky-' + s.color); el.dataset.color = s.color; }
        const t = el.querySelector('.sticky-text');
        if (!el.classList.contains('editing') && t.textContent !== s.text) t.textContent = s.text;
      }
      const cur = find(s.id); if (cur && s.author) cur.dataset.author = s.author;
      refreshVisibility();
      sync.applying = false;
    };
    // Retire les post-its de la maquette locale : la base fait foi
    document.querySelectorAll('#sticky-layer .sticky-note').forEach(e => e.dataset.author = 'seed');
    const local = [...document.querySelectorAll('#sticky-layer .sticky-note')].map(ser);
    document.querySelectorAll('#sticky-layer .sticky-note').forEach(e => e.remove());
    // Seed unique (transaction) si la room est vide
    root.child('seeded').transaction(v => v ? undefined : true, (err, committed) => {
      if (committed) { const o = {}; local.forEach(s => o[s.id] = s); root.child('stickies').update(o); }
    });
    root.child('stickies').on('child_added', sn => apply(sn.val()));
    root.child('stickies').on('child_changed', sn => apply(sn.val()));
    root.child('stickies').on('child_removed', sn => { const e = find(sn.key); if (e) e.remove(); });
    // Mode privé (partagé) : piloté par l'animateur (?animateur=1)
    const modeRef = root.child('mode/private');
    modeRef.on('value', sn => { privateMode = !!sn.val(); refreshVisibility(); renderMode(); });
    const isHost = new URLSearchParams(location.search).has('animateur');
    const bar = document.createElement('div');
    bar.style.cssText = 'position:fixed;left:50%;transform:translateX(-50%);bottom:14px;z-index:9999;font:700 13px Montserrat,sans-serif;display:flex;gap:10px;align-items:center';
    document.body.appendChild(bar);
    function renderMode() {
      bar.innerHTML = '';
      if (privateMode) {
        const t = document.createElement('div');
        t.style.cssText = 'background:#C0392B;color:#fff;padding:8px 16px;border-radius:12px 22px 12px 12px';
        t.textContent = '🔒 Mode privé : vous ne voyez que vos post-its';
        bar.appendChild(t);
      }
      if (isHost) {
        const b = document.createElement('button');
        b.style.cssText = 'background:' + (privateMode ? '#1D8A9B' : '#233742') + ';color:#fff;padding:8px 16px;border-radius:12px 22px 12px 12px;cursor:pointer;border:0;font:inherit';
        b.textContent = privateMode ? '👁 Révéler tous les post-its' : '🔒 Activer le mode privé';
        b.onclick = () => modeRef.set(!privateMode);
        bar.appendChild(b);
      }
    }
    renderMode();
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
