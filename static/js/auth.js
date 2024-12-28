// auth.js
class PasswordHandler {
    constructor() {
        this.setupPasswordToggles();
        this.setupPasswordStrengthMeter();
        this.setupFormValidation();
    }

    setupPasswordToggles() {
        document.querySelectorAll('.password-toggle').forEach(toggle => {
            const input = toggle.previousElementSibling;
            toggle.addEventListener('click', () => this.togglePassword(input, toggle));
        });
    }

    togglePassword(input, toggle) {
        const type = input.type === 'password' ? 'text' : 'password';
        input.type = type;
        toggle.innerHTML = `<i class="fas fa-eye${type === 'password' ? '' : '-slash'}"></i>`;
    }

    setupPasswordStrengthMeter() {
        const passwordInput = document.querySelector('input[name="password1"]');
        if (!passwordInput) return;

        const strengthMeter = document.createElement('div');
        strengthMeter.className = 'password-strength';
        strengthMeter.innerHTML = `
            <div class="strength-meter">
                <div class="strength-meter-fill"></div>
            </div>
            <span class="strength-text"></span>
        `;
        passwordInput.parentElement.appendChild(strengthMeter);

        passwordInput.addEventListener('input', (e) => this.checkPasswordStrength(e.target.value));
    }

    checkPasswordStrength(password) {
        const strength = {
            0: { color: '#ff4336', text: 'Muy débil' },
            1: { color: '#ff9800', text: 'Débil' },
            2: { color: '#ffc107', text: 'Media' },
            3: { color: '#4caf50', text: 'Fuerte' },
            4: { color: '#2e7d32', text: 'Muy fuerte' }
        };

        let score = 0;
        if (password.length >= 8) score++;
        if (password.match(/[a-z]/) && password.match(/[A-Z]/)) score++;
        if (password.match(/\d/)) score++;
        if (password.match(/[^a-zA-Z\d]/)) score++;

        const fill = document.querySelector('.strength-meter-fill');
        const text = document.querySelector('.strength-text');
        
        fill.style.width = `${(score / 4) * 100}%`;
        fill.style.backgroundColor = strength[score].color;
        text.textContent = strength[score].text;
        text.style.color = strength[score].color;
    }

    setupFormValidation() {
        const form = document.querySelector('.auth-form');
        if (!form) return;

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            let isValid = true;
            let messages = [];

            // Validar campos requeridos
            form.querySelectorAll('input[required]').forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    messages.push(`El campo ${input.placeholder} es requerido`);
                }
            });

            // Validar email
            const email = form.querySelector('input[type="email"]');
            if (email && !this.validateEmail(email.value)) {
                isValid = false;
                messages.push('El correo electrónico no es válido');
            }

            // Validar contraseñas coincidentes
            const password1 = form.querySelector('input[name="password1"]');
            const password2 = form.querySelector('input[name="password2"]');
            if (password1 && password2 && password1.value !== password2.value) {
                isValid = false;
                messages.push('Las contraseñas no coinciden');
            }

            if (!isValid) {
                messages.forEach(message => {
                    notifications.show(message, 'error');
                });
                return;
            }

            // Si todo está bien, enviar el formulario
            form.submit();
        });
    }

    validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
}

// Inicializar el manejador de contraseñas cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new PasswordHandler();
});