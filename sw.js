// 由 tools/build-sw.py 產生，請不要手改。
const VERSION = "b8541b665d";
const CACHE = "tokyo2026-" + VERSION;
const ASSETS = [
  "./",
  "index.html",
  "shops.html",
  "shops.json",
  "update.js",
  "manifest.webmanifest",
  "icons/icon-180.png",
  "icons/icon-192.png",
  "icons/icon-512.png"
];

// 內容檔走 network-first：有網路一定看到最新版，沒網路才退回快取。
// 圖片、icon、manifest 走 cache-first（很少變，而且要快）。
const FRESH = /(\.html|\.json|\.js|\/)$/;

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("message", e => {
  if (e.data === "VERSION") {
    e.source && e.source.postMessage({ type: "VERSION", version: VERSION });
  }
  if (e.data === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("fetch", e => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;

  const fresh = req.mode === "navigate" || FRESH.test(url.pathname);

  if (fresh) {
    e.respondWith(
      fetch(req)
        .then(res => {
          if (res.ok && res.type === "basic") {
            const copy = res.clone();
            caches.open(CACHE).then(c => c.put(req, copy));
          }
          return res;
        })
        .catch(() => caches.match(req, { ignoreSearch: true })
          .then(hit => hit || caches.match("./")))
    );
    return;
  }

  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(hit => hit || fetch(req).then(res => {
      if (res.ok && res.type === "basic") {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
      }
      return res;
    }))
  );
});
