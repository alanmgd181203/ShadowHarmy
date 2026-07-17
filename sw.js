/* Service Worker mínimo — Shadow Army Pergamino (PWA).
   Permite "Añadir a pantalla de inicio" / instalar. Cache ligero del altar. */
const CACHE = "shadow-army-pergamino-v2";
const PRECACHE = [
  "./",
  "./dashboard_sombras.html",
  "./manifest.json",
  "./assets/portales/tusk.png",
  "./assets/portales/beru.png",
  "./assets/portales/kamish.png",
  "./assets/portales/bellion.png",
  "./assets/portales/greed.png",
  "./assets/portales/igris.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
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
  event.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        const copy = res.clone();
        if (res.ok && (req.url.includes("/assets/") || req.url.endsWith(".html") || req.url.endsWith("manifest.json"))) {
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      }).catch(() => hit);
    })
  );
});
