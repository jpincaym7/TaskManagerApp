// static/js/sw.js
self.addEventListener('install', (event) => {
    self.skipWaiting();
  });
  
  self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
  });
  
  self.addEventListener('push', (event) => {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: '/static/img/pomodoro-icon.png',
      badge: '/static/img/badge-icon.png',
      vibrate: [200, 100, 200],
      tag: data.tag || 'pomodoro-notification',
      renotify: true,
      data: {
        url: data.url || '/',
        sessionId: data.sessionId
      },
      actions: []
    };
  
    if (data.type === 'session_complete') {
      options.actions = [
        {
          action: 'start_break',
          title: 'Iniciar descanso'
        },
        {
          action: 'skip_break',
          title: 'Saltar descanso'
        }
      ];
    } else if (data.type === 'break_complete') {
      options.actions = [
        {
          action: 'start_pomodoro',
          title: 'Iniciar pomodoro'
        }
      ];
    }
  
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  });
  
  self.addEventListener('notificationclick', (event) => {
    event.notification.close();
  
    if (event.action === 'start_break' || event.action === 'start_pomodoro') {
      const sessionData = event.notification.data;
      event.waitUntil(
        fetch('/pomodoro/api/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            action: 'start',
            session_type: event.action === 'start_break' ? 'short_break' : 'pomodoro',
            task_id: sessionData.taskId
          })
        })
      );
    }
  
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((clientList) => {
          if (clientList.length > 0) {
            return clientList[0].focus();
          }
          return clients.openWindow(event.notification.data.url);
        })
    );
  });