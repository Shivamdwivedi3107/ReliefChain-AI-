const CACHE_NAME = 'reliefchain-v2.5.0-cache';
const STATIC_ASSETS = [
  '/ui/',
  '/ui/index.html',
  '/ui/css/styles.css',
  '/ui/js/app.js',
  '/ui/js/api.js',
  '/ui/js/config.js',
  '/ui/manifest.json'
];

// Install Event: Pre-cache core application shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[ServiceWorker] Pre-cache partial fetch failure:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate Event: Cleanup stale caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch Event: Cache-First for static assets, Network-Only for dynamic APIs
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // CRITICAL RULE: NEVER cache authenticated or dynamic API data
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/') || url.pathname.startsWith('/metrics')) {
    return; // Let standard network request proceed
  }

  // Cache-first strategy for UI static files with network fallback
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        // Fallback for HTML navigations when offline
        if (event.request.headers.get('accept') && event.request.headers.get('accept').includes('text/html')) {
          return caches.match('/ui/index.html');
        }
      });
    })
  );
});

// Background Sync Event: Replay queued offline SOS actions when online
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-offline-sos') {
    event.waitUntil(
      self.clients.matchAll().then((clients) => {
        clients.forEach((client) => {
          client.postMessage({ type: 'OFFLINE_SYNC_TRIGGERED' });
        });
      })
    );
  }
});
