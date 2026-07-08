const SW_BUILD_ID = '2026-07-08-ios-pwa-safe-no-cache';

self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key.startsWith('bloom-club-') || key.startsWith('workbox-')).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

function withNoStoreHeaders(response) {
  const headers = new Headers(response.headers);
  headers.set('cache-control', 'no-store');
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== 'GET' || url.origin !== self.location.origin) {
    return;
  }

  // Startup-critical files must always come from the network and must never be
  // persisted by this service worker. APIs are intentionally untouched too.
  if (
    request.mode === 'navigate' ||
    url.pathname === '/' ||
    url.pathname.endsWith('.html') ||
    url.pathname === '/sw.js' ||
    url.pathname === '/manifest.webmanifest' ||
    url.pathname === '/runtime-config.json' ||
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/assets/')
  ) {
    event.respondWith(fetch(request, { cache: 'no-store' }).then(withNoStoreHeaders));
  }
});
