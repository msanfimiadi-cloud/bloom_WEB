const SW_BUILD_ID = '2026-07-07-ios-pwa-startup-v2';
const STATIC_CACHE_NAME = `bloom-club-static-${SW_BUILD_ID}`;
const CACHEABLE_STATIC_PATHS = ['/assets/', '/docs/icons/', '/icons/'];

self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key.startsWith('bloom-club-') && key !== STATIC_CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

function isValidCacheResponse(response) {
  return response && response.ok && response.type === 'basic' && response.status === 200;
}

function isCacheableStaticRequest(request, url) {
  if (request.method !== 'GET' || url.origin !== self.location.origin) return false;
  if (url.pathname.endsWith('.html') || url.pathname === '/' || url.pathname === '/manifest.webmanifest' || url.pathname === '/sw.js') return false;
  return CACHEABLE_STATIC_PATHS.some((path) => url.pathname.startsWith(path));
}

function noStoreResponseHeaders(response) {
  const headers = new Headers(response.headers);
  headers.set('cache-control', 'no-store');
  return headers;
}

async function networkFirstNavigation(request) {
  try {
    const response = await fetch(request, { cache: 'no-store' });
    if (response && response.ok) return response;
    return response;
  } catch (error) {
    return new Response(`<!doctype html><html lang="ru"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/><title>Bloom Club</title><style>body{margin:0;background:#fff7fa;color:#2b1b22;font-family:-apple-system,BlinkMacSystemFont,system-ui,sans-serif}.wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:14px;padding:24px;text-align:center;box-sizing:border-box}button{border:0;border-radius:999px;background:#2b1b22;color:white;padding:12px 18px;font:inherit}</style></head><body><main class="wrap" role="alert"><h1>Проблемы с соединением</h1><p>Проверьте интернет или VPN и попробуйте снова.</p><button type="button" onclick="location.reload()">Повторить</button></main></body></html>`, {
      status: 503,
      statusText: 'Offline',
      headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' },
    });
  }
}

async function cacheFirstStatic(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (isValidCacheResponse(response)) {
    const cache = await caches.open(STATIC_CACHE_NAME);
    await cache.put(request, response.clone());
  }
  return response;
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== 'GET' || url.pathname.startsWith('/api/')) return;

  if (request.mode === 'navigate') {
    event.respondWith(networkFirstNavigation(request));
    return;
  }

  if (url.origin === self.location.origin && (url.pathname === '/manifest.webmanifest' || url.pathname === '/sw.js')) {
    event.respondWith(fetch(request, { cache: 'no-store' }).then((response) => new Response(response.body, { status: response.status, statusText: response.statusText, headers: noStoreResponseHeaders(response) })));
    return;
  }

  if (isCacheableStaticRequest(request, url)) {
    event.respondWith(cacheFirstStatic(request));
  }
});
