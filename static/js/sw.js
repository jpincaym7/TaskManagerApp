// Service Worker para la funcionalidad offline y PWA
const CACHE_NAME = 'pomodoro-cache-v1';
const urlsToCache = [
    '/',
    '/static/css/styles.css',
    '/static/js/main.js',
    '/static/sounds/start.mp3',
    '/static/sounds/complete.mp3',
    '/static/sounds/pause.mp3',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/howler/2.2.3/howler.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/hammer.js/2.0.8/hammer.min.js'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
    );
});

self.addEventListener('push', event => {
    const options = {
        body: event.data.text(),
        icon: '/static/images/logo.png',
        badge: '/static/images/badge.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'start',
                title: 'Iniciar Pomodoro',
                icon: '/static/images/start.png'
            },
            {
                action: 'cancel',
                title: 'Cancelar',
                icon: '/static/images/cancel.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('MindHelper Pomodoro', options)
    );
});

self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.action === 'start') {
        // Abrir la aplicación y comenzar un nuevo pomodoro
        clients.openWindow('/pomodoro?action=start');
    }
});