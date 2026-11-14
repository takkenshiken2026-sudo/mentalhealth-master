/* Service Worker（自動生成: tools/build_pwa.py）
 * 方針: 同一オリジンGETのみ対象。HTMLはネットワーク優先、静的はSWR。
 * 別オリジン(広告/解析/フォント/Supabase)には介入しない。
 */
const CACHE = 'mhm-pwa-v1';
const CORE = ["/", "/index.html", "/site-pages.css", "/site-theme.css", "/seo-editorial.css", "/site-q-index.js", "/site-config.js", "/exam-site-data-past.js", "/exam-site-data-practice.js", "/exam-site-data-ichimondou.js", "/assets/brand/icon-192.png"];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil((async () => {
    const c = await caches.open(CACHE);
    // 1件でも失敗してinstallを止めないよう個別に追加する
    await Promise.allSettled(CORE.map((u) => c.add(new Request(u, { cache: 'reload' }))));
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  let url;
  try { url = new URL(req.url); } catch (e) { return; }
  // 同一オリジンのみ介入（広告・解析・フォント・外部APIはネットワークに委ねる）
  if (url.origin !== self.location.origin) return;

  // HTMLナビゲーション: ネットワーク優先・失敗時のみキャッシュ（古い内容に固定しない）
  if (req.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const net = await fetch(req);
        try { const c = await caches.open(CACHE); c.put(req, net.clone()); } catch (e) {}
        return net;
      } catch (e) {
        const cached = (await caches.match(req)) || (await caches.match('/index.html')) || (await caches.match('/'));
        return cached || Response.error();
      }
    })());
    return;
  }

  // 静的アセット: stale-while-revalidate（即表示＋裏で更新）
  event.respondWith((async () => {
    const cached = await caches.match(req);
    const fetchP = fetch(req).then((net) => {
      if (net && net.status === 200 && net.type === 'basic') {
        caches.open(CACHE).then((c) => c.put(req, net.clone())).catch(() => {});
      }
      return net;
    }).catch(() => null);
    return cached || (await fetchP) || Response.error();
  })());
});
