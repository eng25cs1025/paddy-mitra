const STATIC_CACHE = 'paddy-mitra-static-v2';
const STATIC_FILES = ['/login.html', '/register.html', '/dashboard.html', '/paddy-mitra-logo.svg', '/icon-192.svg', '/icon-512.svg', '/manifest.json'];

self.addEventListener('install', event => {
    event.waitUntil(caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_FILES)));
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
    const request = new URL(event.request.url);
    if (request.origin !== self.location.origin || request.pathname.startsWith('/api/')) return;
    event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
