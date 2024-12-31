document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('categoryModal');
    const categoriesContainer = document.getElementById('categoriesContainer');
    let activeNotifications = [];
    let deleteConfirmDialog = null;

    // Modal Functions
    function showModal(content) {
        modal.querySelector('.modal-content').innerHTML = content;
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function hideModal() {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }

    // Notification System
    function showNotification(type, message) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="notification-icon fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                <span class="notification-message">${message}</span>
                <button class="notification-close" aria-label="Close notification">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Add touch event listeners for mobile
        let touchStartX = 0;
        let touchStartY = 0;
        
        notification.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        }, { passive: true });
        
        notification.addEventListener('touchmove', (e) => {
            const touchEndX = e.touches[0].clientX;
            const touchEndY = e.touches[0].clientY;
            const deltaX = touchEndX - touchStartX;
            const deltaY = Math.abs(touchEndY - touchStartY);
            
            // Only slide horizontally if the movement is more horizontal than vertical
            if (Math.abs(deltaX) > deltaY && Math.abs(deltaX) > 50) {
                notification.style.transform = `translateX(${deltaX}px)`;
                notification.style.opacity = 1 - Math.abs(deltaX) / 200;
            }
        }, { passive: true });
        
        notification.addEventListener('touchend', (e) => {
            const touchEndX = e.changedTouches[0].clientX;
            const deltaX = touchEndX - touchStartX;
            
            if (Math.abs(deltaX) > 100) {
                dismissNotification(notification);
            } else {
                notification.style.transform = '';
                notification.style.opacity = '1';
            }
        }, { passive: true });

        // Close button handler
        notification.querySelector('.notification-close').addEventListener('click', () => {
            dismissNotification(notification);
        });

        // Add to DOM with stacking
        const container = document.querySelector('.notification-container') || createNotificationContainer();
        container.appendChild(notification);
        activeNotifications.push(notification);

        // Stack management
        if (activeNotifications.length > 3) {
            dismissNotification(activeNotifications[0]);
        }

        // Auto dismiss
        setTimeout(() => {
            if (notification.isConnected) {
                dismissNotification(notification);
            }
        }, 5000);

        // Entrance animation
        requestAnimationFrame(() => {
            notification.style.transform = 'translateY(0)';
            notification.style.opacity = '1';
        });
    }

    function createNotificationContainer() {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
        return container;
    }

    function dismissNotification(notification) {
        notification.classList.add('hiding');
        setTimeout(() => {
            if (notification.isConnected) {
                notification.remove();
                activeNotifications = activeNotifications.filter(n => n !== notification);
            }
        }, 300);
    }

    // Confirmation Dialog
    function showDeleteConfirmation(categoryId, categoryName) {
        // Remove existing dialog if present
        if (deleteConfirmDialog) {
            deleteConfirmDialog.remove();
        }

        deleteConfirmDialog = document.createElement('div');
        deleteConfirmDialog.className = 'fixed inset-0 z-50 flex items-center justify-center p-4';
        deleteConfirmDialog.innerHTML = `
            <div class="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm"></div>
            <div class="bg-white rounded-lg shadow-xl w-full max-w-sm mx-auto relative z-10 transform transition-all">
                <div class="p-6">
                    <div class="text-center mb-4">
                        <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                        <h3 class="text-xl font-semibold text-gray-900 mb-2">¿Eliminar categoría?</h3>
                        <p class="text-gray-600">¿Estás seguro de que deseas eliminar la categoría "${categoryName}"? Esta acción no se puede deshacer.</p>
                    </div>
                    <div class="flex gap-3 mt-6">
                        <button class="cancel-delete flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors">
                            Cancelar
                        </button>
                        <button class="confirm-delete flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors">
                            Eliminar
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(deleteConfirmDialog);

        // Add event listeners with haptic feedback simulation
        const cancelBtn = deleteConfirmDialog.querySelector('.cancel-delete');
        const confirmBtn = deleteConfirmDialog.querySelector('.confirm-delete');

        cancelBtn.addEventListener('click', () => {
            deleteConfirmDialog.remove();
            if (window.navigator.vibrate) {
                window.navigator.vibrate(50);
            }
        });

        confirmBtn.addEventListener('click', () => {
            if (window.navigator.vibrate) {
                window.navigator.vibrate([100, 50, 100]);
            }
            deleteCategory(categoryId);
            deleteConfirmDialog.remove();
        });
    }

    function deleteCategory(categoryId) {
        fetch(`/tasks/categories/${categoryId}/delete/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Elimina el card correspondiente sin recargar la página
                const card = document.querySelector(`.category-card[data-category-id="${categoryId}"]`);
                if (card) {
                    card.style.transform = 'translateX(-100%)';
                    card.style.opacity = '0';
                    setTimeout(() => card.remove(), 300);
                }
                showNotification('success', data.message);
            } else {
                showNotification('error', data.message || 'Error al eliminar la categoría');
            }
        })
        .catch(() => {
            showNotification('error', 'Error al procesar la solicitud');
        });
    }    

    // Event Listeners
    document.getElementById('addCategoryBtn').addEventListener('click', function() {
        fetch('/tasks/categories/create/')
            .then(response => response.json())
            .then(data => showModal(data.form_html))
            .catch(() => showNotification('error', 'Error al cargar el formulario'));
    });

    document.addEventListener('click', function(e) {
        // Edit category handler
        if (e.target.matches('.edit-category-btn') || e.target.closest('.edit-category-btn')) {
            const card = e.target.closest('.category-card');
            const categoryId = card.dataset.categoryId;
            
            fetch(`/tasks/categories/${categoryId}/update/`)
                .then(response => response.json())
                .then(data => showModal(data.form_html))
                .catch(() => showNotification('error', 'Error al cargar el formulario'));
        }
        
        document.addEventListener('click', function (e) {
            // Manejo del botón de eliminar categoría
            if (e.target.matches('.delete-category-btn') || e.target.closest('.delete-category-btn')) {
                const card = e.target.closest('.category-card');
        
                // Verifica si existe el contenedor de la tarjeta
                if (!card) {
                    console.error('No se encontró la tarjeta correspondiente al botón de eliminar.');
                    showNotification('error', 'Error: No se encontró la tarjeta de categoría.');
                    return;
                }
        
                // Busca el nombre de la categoría dentro de la tarjeta
                const categoryNameElement = card.querySelector('.category-name'); // Selector simplificado
                const categoryName = categoryNameElement ? categoryNameElement.textContent.trim() : 'Sin nombre';
        
                // Verifica si existe un ID de categoría
                const categoryId = card.dataset.categoryId;
                if (!categoryId) {
                    console.error('No se encontró el ID de la categoría en la tarjeta.', card);
                    showNotification('error', 'Error: No se encontró el ID de la categoría.');
                    return;
                }
        
                // Llama a la función para mostrar la confirmación
                showDeleteConfirmation(categoryId, categoryName);
            }
        });
        
        
        // Modal close handler
        if (e.target.matches('.close-modal') || 
            (e.target.matches('.modal-overlay') && !e.target.closest('.modal-container'))) {
            hideModal();
        }
    });

    // Form submission handler
    document.addEventListener('submit', function(e) {
        if (e.target.matches('.category-form')) {
            e.preventDefault();
            const form = e.target;
            const categoryId = form.dataset.categoryId;
            
            fetch(form.action, {
                method: 'POST',
                body: new FormData(form)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (categoryId === 'new') {
                        categoriesContainer.insertAdjacentHTML('afterbegin', data.category.html);
                        const newCard = categoriesContainer.firstElementChild;
                        newCard.style.opacity = '0';
                        newCard.style.transform = 'translateY(20px)';
                        requestAnimationFrame(() => {
                            newCard.style.opacity = '1';
                            newCard.style.transform = 'translateY(0)';
                        });
                    } else {
                        const oldCard = document.querySelector(`.category-card[data-category-id="${categoryId}"]`);
                        oldCard.outerHTML = data.category.html;
                        const newCard = document.querySelector(`.category-card[data-category-id="${categoryId}"]`);
                        newCard.classList.add('highlight');
                        setTimeout(() => newCard.classList.remove('highlight'), 1000);
                    }
                    hideModal();
                    showNotification('success', data.message);
                } else {
                    showNotification('error', data.message || 'Por favor, verifica los datos ingresados');
                }
            })
            .catch(() => showNotification('error', 'Error al procesar el formulario'));
        }
    });
});