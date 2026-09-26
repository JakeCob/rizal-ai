/* App-shell service worker (DECISIONS.md D25). Caches the shell so the
   installed app opens instantly; lesson data and audio always go to the
   network. No offline lessons at MVP. */
// v2: the plan 012 palette and sun icons; activating it drops the v1 cache.
const CACHE = "rizalai-shell-v2";
const SHELL = ["/", "/manifest.json", "/icon.svg", "/icon-192.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const isShell = event.request.mode === "navigate" || SHELL.includes(url.pathname) || url.pathname.startsWith("/_next/static/");
  if (event.request.method !== "GET" || !isShell || url.origin !== self.location.origin) return;
  event.respondWith(
    fetch(event.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(event.request, copy));
        return res;
      })
      .catch(() => caches.match(event.request).then((hit) => hit ?? caches.match("/"))),
  );
});
