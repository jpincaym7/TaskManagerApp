// Añade esto a un nuevo archivo notification.js

class NotificationSystem {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${icons[type]} notification-icon"></i>
                <span class="notification-message">${message}</span>
            </div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        this.container.appendChild(notification);

        // Manejador para cerrar la notificación
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => this.hide(notification));

        // Auto-cerrar después del tiempo especificado
        if (duration) {
            setTimeout(() => this.hide(notification), duration);
        }
    }

    hide(notification) {
        notification.classList.add('hiding');
        notification.addEventListener('animationend', () => {
            notification.remove();
        });
    }
}

// Crear una instancia global
window.notifications = new NotificationSystem();