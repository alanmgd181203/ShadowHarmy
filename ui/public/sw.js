/* Service Worker — Pergamino Cascada (React).
   La foto viva (/data/) nunca se cachea. */
const CACHE = "shadow-army-cascada-v19";

self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.pathname.startsWith("/data/")) {
    event.respondWith(fetch(req));
    return;
  }
  event.respondWith(
    fetch(req)
      .then((res) => {
        if (res.ok && (url.pathname.startsWith("/assets/") || url.pathname.endsWith("manifest.json"))) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() => caches.match(req))
  );
});
