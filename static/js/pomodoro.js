// Sonidos para las notificaciones
const sounds = {
    start: new Howl({ src: ['/static/sounds/start.mp3'] }),
    complete: new Howl({ src: ['/static/sounds/complete.mp3'] }),
    pause: new Howl({ src: ['/static/sounds/pause.mp3'] })
};

class PomodoroTimer {
    constructor() {
        this.timeDisplay = document.getElementById('time-display');
        this.sessionLabel = document.getElementById('session-label');
        this.startBtn = document.getElementById('start-btn');
        this.pauseBtn = document.getElementById('pause-btn');
        this.cancelBtn = document.getElementById('cancel-btn');
        this.progressRing = document.querySelector('.progress-ring__circle');
        
        this.currentSession = null;
        this.timeLeft = 0;
        this.totalTime = 0;
        this.timer = null;
        this.status = 'idle';

        this.setupEventListeners();
        this.setupCircle();
    }

    setupCircle() {
        const circle = this.progressRing;
        const radius = circle.r.baseVal.value;
        this.circumference = radius * 2 * Math.PI;
        
        circle.style.strokeDasharray = `${this.circumference} ${this.circumference}`;
        circle.style.strokeDashoffset = this.circumference;
    }

    setProgress(percent) {
        const offset = this.circumference - (percent / 100 * this.circumference);
        this.progressRing.style.strokeDashoffset = offset;
    }

    setupEventListeners() {
        this.startBtn.addEventListener('click', () => this.startSession());
        this.pauseBtn.addEventListener('click', () => this.pauseSession());
        this.cancelBtn.addEventListener('click', () => this.cancelSession());
    }

    async startSession() {
        try {
            const response = await fetch('/pomodoro/api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    action: 'start',
                    session_type: 'pomodoro'
                })
            });

            const data = await response.json();
            if (response.ok) {
                this.currentSession = data;
                this.timeLeft = data.duration * 60;
                this.totalTime = this.timeLeft;
                this.startTimer();
                this.updateUI('running');
                sounds.start.play();
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            this.showNotification('Error al iniciar la sesión', 'error');
        }
    }

    startTimer() {
        this.timer = setInterval(() => {
            this.timeLeft--;
            this.updateTimeDisplay();
            
            const progress = ((this.totalTime - this.timeLeft) / this.totalTime) * 100;
            this.setProgress(progress);

            if (this.timeLeft <= 0) {
                this.completeSession();
            }
        }, 1000);
    }

    async pauseSession() {
        try {
            const response = await fetch('/pomodoro/api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    action: 'pause',
                    session_id: this.currentSession.session_id
                })
            });

            if (response.ok) {
                clearInterval(this.timer);
                this.updateUI('paused');
                sounds.pause.play();
            }
        } catch (error) {
            this.showNotification('Error al pausar la sesión', 'error');
        }
    }

    async cancelSession() {
        if (confirm('¿Estás seguro de que deseas cancelar la sesión?')) {
            try {
                const response = await fetch('/pomodoro/api/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        action: 'cancel',
                        session_id: this.currentSession.session_id
                    })
                });

                if (response.ok) {
                    clearInterval(this.timer);
                    this.resetTimer();
                    this.updateUI('idle');
                }
            } catch (error) {
                this.showNotification('Error al cancelar la sesión', 'error');
            }
        }
    }

    async completeSession() {
        clearInterval(this.timer);
        sounds.complete.play();
        
        try {
            const response = await fetch('/pomodoro/api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    action: 'complete',
                    session_id: this.currentSession.session_id
                })
            });

            const data = await response.json();
            if (response.ok) {
                this.showNotification('¡Sesión completada!', 'success');
                this.resetTimer();
                this.updateUI('idle');
                
                // Preguntar si desea iniciar el siguiente tipo de sesión
                if (confirm(`¿Deseas iniciar un ${data.next_session_type}?`)) {
                    // Iniciar siguiente sesión
                    this.startSession(data.next_session_type);
                }
            }
        } catch (error) {
            this.showNotification('Error al completar la sesión', 'error');
        }
    }

    updateTimeDisplay() {
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        this.timeDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    updateUI(status) {
        switch (status) {
            case 'running':
                this.startBtn.style.display = 'none';
                this.pauseBtn.style.display = 'inline-flex';
                this.cancelBtn.style.display = 'inline-flex';
                this.timeDisplay.parentElement.classList.add('timer-active');
                break;
            case 'paused':
                this.startBtn.style.display = 'inline-flex';
                this.pauseBtn.style.display = 'none';
                this.cancelBtn.style.display = 'inline-flex';
                this.timeDisplay.parentElement.classList.remove('timer-active');
                break;
            case 'idle':
                this.startBtn.style.display = 'inline-flex';
                this.pauseBtn.style.display = 'none';
                this.cancelBtn.style.display = 'none';
                this.timeDisplay.parentElement.classList.remove('timer-active');
                break;
        }
    }

    resetTimer() {
        this.timeLeft = 0;
        this.totalTime = 0;
        this.currentSession = null;
        this.updateTimeDisplay();
        this.setProgress(0);
    }

    showNotification(message, type) {
        // Crear el elemento de notificación
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} notification-icon"></i>
                <span class="notification-message">${message}</span>
            </div>
            <button class="notification-close">&times;</button>`;
        
        // Añadir la notificación al contenedor
        const container = document.querySelector('.notification-container') || (() => {
            const cont = document.createElement('div');
            cont.className = 'notification-container';
            document.body.appendChild(cont);
            return cont;
        })();
        
        container.appendChild(notification);

        // Configurar el botón de cierre
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.classList.add('hiding');
            setTimeout(() => notification.remove(), 300);
        });

        // Auto-cerrar después de 5 segundos
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.add('hiding');
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    requestNotificationPermission() {
        if ("Notification" in window) {
            Notification.requestPermission();
        }
    }

    sendNotification(title, options = {}) {
        if ("Notification" in window && Notification.permission === "granted") {
            new Notification(title, {
                icon: '/static/images/logo.png',
                badge: '/static/images/badge.png',
                ...options
            });
        }
    }
}

// Service Worker para notificaciones y PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js').then(registration => {
            console.log('ServiceWorker registration successful');
        }).catch(err => {
            console.log('ServiceWorker registration failed: ', err);
        });
    });
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', () => {
    const timer = new PomodoroTimer();
    timer.requestNotificationPermission();
    
    // Gestos táctiles para controlar el timer
    const timerCard = document.querySelector('.timer-card');
    const hammer = new Hammer(timerCard);

    // Swipe izquierda para cancelar
    hammer.on('swipeleft', () => {
        if (timer.status === 'running' || timer.status === 'paused') {
            timer.cancelSession();
        }
    });

    // Swipe derecha para pausar/reanudar
    hammer.on('swiperight', () => {
        if (timer.status === 'running') {
            timer.pauseSession();
        } else if (timer.status === 'paused') {
            timer.startSession();
        }
    });

    // Doble tap para iniciar
    hammer.get('tap').set({ taps: 2 });
    hammer.on('tap', () => {
        if (timer.status === 'idle') {
            timer.startSession();
        }
    });
});