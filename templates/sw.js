/**
 * High-Performance Cross-Browser Service Worker
 * Compatible with: Google Chrome, Microsoft Edge, Mozilla Firefox
 * Features:
 * - Cache Versioning & Automatic Old Cache Purge
 * - Network-First for dynamic /api endpoints
 * - Stale-While-Revalidate for UI assets
 * - Active Heartbeat Keep-Alive to prevent worker sleep
 * - Cross-tab communication and console/memory pruning coordination
 */

const CACHE_NAME = 'crewai-rag-cache-v1.0';
const RUNTIME_CACHE = 'crewai-rag-runtime-v1.0';

// Critical core assets to pre-cache
const PRECACHE_ASSETS = [
    '/',
    '/manifest.json',
    '/favicon.ico',
    '/icons/icon.svg',
    '/icons/icon-192.png',
    '/icons/icon-512.png',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
    'https://cdn.jsdelivr.net/npm/marked/marked.min.js'
];

/* ==========================================================================
   1. Install Phase - Precache Core Assets & Skip Waiting
   ========================================================================== */
self.addEventListener('install', (event) => {
    // Force immediate activation without waiting for existing tabs to close
    self.skipWaiting();

    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS).catch((err) => {
                console.warn('[SW] Core asset precache warning:', err);
            });
        })
    );
});

/* ==========================================================================
   2. Activate Phase - Purge Old Caches & Claim Clients Immediately
   ========================================================================== */
self.addEventListener('activate', (event) => {
    // Immediately claim all active clients across Chrome, Edge, and Firefox
    event.waitUntil(
        Promise.all([
            self.clients.claim(),
            // Purge outdated cache versions
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
        ])
    );
});

/* ==========================================================================
   3. Fetch Strategy:
      - /api/* -> Network Only / Network First (never serve stale AI responses)
      - Static assets -> Stale-While-Revalidate (instant offline / high velocity)
   ========================================================================== */
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Bypass non-GET requests (e.g. POST /api/chat, file uploads)
    if (event.request.method !== 'GET') {
        return;
    }

    // Dynamic API Routes: Always fetch fresh from server
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => {
                return new Response(
                    JSON.stringify({ error: 'Offline', detail: 'Server unreachable from current network.' }),
                    { headers: { 'Content-Type': 'application/json' }, status: 503 }
                );
            })
        );
        return;
    }

    // Static Assets & Web Dashboard: Stale-While-Revalidate
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            const fetchPromise = fetch(event.request).then((networkResponse) => {
                if (networkResponse && networkResponse.status === 200) {
                    const responseClone = networkResponse.clone();
                    caches.open(RUNTIME_CACHE).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return networkResponse;
            }).catch(() => cachedResponse);

            return cachedResponse || fetchPromise;
        })
    );
});

/* ==========================================================================
   4. Keep-Alive Heartbeat & Inter-Process Messaging
   ========================================================================== */
self.addEventListener('message', (event) => {
    if (!event.data) return;

    switch (event.data.type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;

        case 'HEARTBEAT':
            // Respond with ACK to keep worker and client loop active
            if (event.source) {
                event.source.postMessage({
                    type: 'HEARTBEAT_ACK',
                    timestamp: Date.now(),
                    cacheVersion: CACHE_NAME
                });
            }
            break;

        case 'CLEAR_CACHE':
            caches.keys().then((keys) => {
                return Promise.all(keys.map(k => caches.delete(k)));
            }).then(() => {
                if (event.source) {
                    event.source.postMessage({ type: 'CACHE_CLEARED' });
                }
            });
            break;

        default:
            break;
    }
});
