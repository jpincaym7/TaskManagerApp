class MobileTaskManager {
    constructor() {
        this.tasks = [];
        this.categories = new Map();
        this.currentFilter = {
            status: null,
            category: null,
            priority: null,
            search: ''
        };
        this.init();
    }

    async init() {
        await this.loadTasks();
        this.setupEventListeners();
        this.setupGestureRecognition();
        this.setupModalListeners();
    }

    setupModalListeners() {
        const fabButton = document.getElementById('add-task-fab');
        const modal = document.getElementById('task-modal');
        const closeButton = modal.querySelector('.close-modal');

        fabButton.addEventListener('click', () => {
            // Reset form when opening modal for new task
            const form = document.getElementById('task-form');
            form.reset();
            form.action = '/tasks/create/';
            modal.querySelector('.modal-header h3').textContent = 'Nueva Tarea';
            modal.classList.add('active');
        });

        closeButton.addEventListener('click', () => {
            modal.classList.remove('active');
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });

        modal.querySelector('.modal-content').addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    async loadTasks() {
        try {
            // Construir la URL con los filtros
            const params = new URLSearchParams();
            if (this.currentFilter.status) params.append('status', this.currentFilter.status);
            if (this.currentFilter.category) params.append('category', this.currentFilter.category);
            if (this.currentFilter.priority) params.append('priority', this.currentFilter.priority);
            if (this.currentFilter.search) params.append('search', this.currentFilter.search);

            const url = `/tasks/list/json/?${params.toString()}`;
            const response = await fetch(url);
            const data = await response.json();
            this.tasks = data.tasks;
            this.organizeTasksByCategory();
            this.renderTasks();
        } catch (error) {
            this.showNotification('Error cargando tareas', 'error');
        }
    }

    async handleTaskSubmission(form) {
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: form.method,
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            if (!response.ok) throw new Error('Error en la solicitud');

            const data = await response.json();
            this.showNotification('Tarea creada exitosamente', 'success');
            await this.loadTasks();
            form.reset();
            document.getElementById('task-modal').classList.remove('active');

        } catch (error) {
            this.showNotification('Error al crear la tarea', 'error');
        }
    }

    async handleTaskDeletion(taskId) {
        const modal = document.getElementById('delete-modal');
        const taskTitle = this.tasks.find(task => task.id === parseInt(taskId))?.title || 'esta tarea';
        
        // Set the task title in the modal
        modal.querySelector('.task-title-preview').textContent = `"${taskTitle}"`;
        
        return new Promise((resolve) => {
            modal.classList.add('active');
            
            const confirmBtn = modal.querySelector('.confirm-delete-btn');
            const cancelBtn = modal.querySelector('.cancel-delete-btn');
            const modalContent = modal.querySelector('.delete-modal-content');
            
            const closeModal = () => {
                modal.classList.remove('active');
                confirmBtn.removeEventListener('click', handleConfirm);
                cancelBtn.removeEventListener('click', handleCancel);
                modal.removeEventListener('click', handleOutsideClick);
            };
            
            const handleConfirm = async () => {
                try {
                    const response = await fetch(`/tasks/${taskId}/delete/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        }
                    });
    
                    if (!response.ok) throw new Error('Error al eliminar la tarea');
    
                    const data = await response.json();
                    this.showNotification(data.message, 'success');
                    await this.loadTasks();
                } catch (error) {
                    this.showNotification('Error al eliminar la tarea', 'error');
                }
                closeModal();
                resolve();
            };
            
            const handleCancel = () => {
                closeModal();
                resolve();
            };
            
            const handleOutsideClick = (e) => {
                if (e.target === modal) {
                    handleCancel();
                }
            };
            
            confirmBtn.addEventListener('click', handleConfirm);
            cancelBtn.addEventListener('click', handleCancel);
            modal.addEventListener('click', handleOutsideClick);
        });
    }

    async handleTaskUpdate(taskId, formData) {
        console.log(formData)
        try {
            const response = await fetch(`/tasks/${taskId}/update/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            if (!response.ok) throw new Error('Error al actualizar la tarea');

            const data = await response.json();
            this.showNotification(data.message, 'success');
            await this.loadTasks();
            document.getElementById('task-modal').classList.remove('active');

        } catch (error) {
            this.showNotification('Error al actualizar la tarea', 'error');
        }
    }

    async loadTaskIntoForm(taskId) {
        try {
            const response = await fetch(`/tasks/${taskId}/detail/`);
            if (!response.ok) throw new Error('Error al cargar los detalles de la tarea');
            
            const data = await response.json();
            const task = data.task;
            
            const form = document.getElementById('task-form');
            const modal = document.getElementById('task-modal');

            // Update form action and method
            form.action = `/tasks/${taskId}/update/`;
            form.method = 'POST';

            // Update modal title
            modal.querySelector('.modal-header h3').textContent = 'Editar Tarea';

            // Fill form fields
            form.title.value = task.title;
            form.description.value = task.description || '';
            form.category.value = task.category?.id || '';
            form.priority.value = task.priority;
            form.status.value = task.status;
            form.estimated_pomodoros.value = task.estimated_pomodoros;

            if (task.due_date) {
                const dueDate = new Date(task.due_date);
                const formattedDate = dueDate.toISOString().slice(0, 16);
                form.due_date.value = formattedDate;
            } else {
                form.due_date.value = '';
            }

            modal.classList.add('active');

        } catch (error) {
            this.showNotification('Error al cargar los detalles de la tarea', 'error');
        }
    }


    organizeTasksByCategory() {
        this.categories.clear();
        this.tasks.forEach(task => {
            const categoryId = task.category?.id || 'uncategorized';
            if (!this.categories.has(categoryId)) {
                this.categories.set(categoryId, {
                    id: categoryId,
                    name: task.category?.name || 'Sin categoría',
                    color: task.category?.color || '#808080',
                    tasks: []
                });
            }
            this.categories.get(categoryId).tasks.push(task);
        });
    }

    setupEventListeners() {
        // Form submission
        const form = document.getElementById('task-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!form.title.value.trim()) {
                this.showNotification('Por favor ingresa un título para la tarea', 'warning');
                return;
            }

            const formData = new FormData(form);
            const taskId = form.action.match(/\/tasks\/(\d+)\/update\//)?.[1];

            if (taskId) {
                await this.handleTaskUpdate(taskId, formData);
            } else {
                await this.handleTaskSubmission(form);
            }
        });

        // Task actions
        this.setupTaskActionListeners();

        // Filter controls
        document.querySelectorAll('.filter-control').forEach(control => {
            control.addEventListener('change', async (e) => {
                const filterType = e.target.dataset.filter;
                this.currentFilter[filterType] = e.target.value || null;
                await this.loadTasks();
            });
        });

        // Search input with debounce
        let searchTimeout;
        document.getElementById('search-input').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(async () => {
                this.currentFilter.search = e.target.value;
                await this.loadTasks();
            }, 300);
        });

        // Pomodoro counter
        const minusBtn = document.querySelector('.minus');
        const plusBtn = document.querySelector('.plus');
        const pomodoroInput = document.querySelector('#estimated_pomodoros');

        minusBtn.addEventListener('click', () => {
            const currentValue = parseInt(pomodoroInput.value);
            if (currentValue > 1) {
                pomodoroInput.value = currentValue - 1;
            }
        });

        plusBtn.addEventListener('click', () => {
            const currentValue = parseInt(pomodoroInput.value);
            pomodoroInput.value = currentValue + 1;
        });
    }

    setupTaskActionListeners() {
        document.addEventListener('click', async (e) => {
            const actionButton = e.target.closest('.action-button');
            if (!actionButton) return;

            const taskItem = actionButton.closest('.task-item');
            const taskId = taskItem.dataset.taskId;
            const action = actionButton.dataset.action;

            if (action === 'delete') {
                await this.handleTaskDeletion(taskId);
            } else if (action === 'edit') {
                await this.loadTaskIntoForm(taskId);
            }

            // Prevent the task details from toggling when clicking action buttons
            e.stopPropagation();
        });

        // Task item toggle details
        document.addEventListener('click', (e) => {
            const taskItem = e.target.closest('.task-item');
            if (taskItem && !e.target.closest('.action-button')) {
                this.toggleTaskDetails(taskItem);
            }
        });
    }

    setupGestureRecognition() {
        document.querySelectorAll('.task-item').forEach(taskEl => {
            const hammer = new Hammer(taskEl);

            hammer.on('swipeleft', () => {
                this.showTaskActions(taskEl);
            });

            hammer.on('swiperight', () => {
                this.hideTaskActions(taskEl);
            });
        });
    }

    createCategoryElement(category) {
        const categoryEl = document.createElement('div');
        categoryEl.className = 'category-section';
        categoryEl.innerHTML = `
            <div class="category-header">
                <div class="category-color" style="background-color: ${category.color}"></div>
                <h2 class="category-name">${category.name}</h2>
            </div>
        `;
        return categoryEl;
    }

    createTaskElement(task) {
        const taskEl = document.createElement('div');
        taskEl.className = 'task-item';
        taskEl.dataset.taskId = task.id;

        const dueDate = task.due_date ? new Date(task.due_date).toLocaleDateString() : 'Sin fecha';
        const description = task.description || 'Sin descripción';

        taskEl.innerHTML = `
            <div class="task-header">
                <h3 class="task-title">${task.title}</h3>
                <div class="task-actions">
                    <button class="action-button edit" data-action="edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="action-button delete" data-action="delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <span class="task-priority ${task.priority.toLowerCase()}">${task.priority}</span>
            </div>
            <div class="task-details">
                <p class="task-description">${description}</p>
                <div class="task-meta">
                    <span class="task-due-date">
                        <i class="fas fa-calendar"></i> ${dueDate}
                    </span>
                    <span class="task-status">
                        <i class="fas fa-tasks"></i> ${task.status}
                    </span>
                    <span class="task-pomodoros">
                        <i class="fas fa-clock"></i> ${task.completed_pomodoros}/${task.estimated_pomodoros} pomodoros
                    </span>
                </div>
            </div>
        `;

        return taskEl;
    }

    renderTasks() {
        const container = document.getElementById('tasks-container');
        container.innerHTML = '';

        if (this.tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-tasks fa-3x"></i>
                    <p>No hay tareas que mostrar</p>
                </div>
            `;
            return;
        }

        this.categories.forEach(category => {
            if (category.tasks.length === 0) return;

            const categoryEl = this.createCategoryElement(category);
            const tasksContainer = document.createElement('div');
            tasksContainer.className = 'tasks-list';

            category.tasks.forEach(task => {
                const taskEl = this.createTaskElement(task);
                tasksContainer.appendChild(taskEl);
            });

            categoryEl.appendChild(tasksContainer);
            container.appendChild(categoryEl);
        });

        this.setupGestureRecognition();
    }

    showTaskActions(taskEl) {
        taskEl.style.transform = 'translateX(-100px)';
    }

    hideTaskActions(taskEl) {
        taskEl.style.transform = 'translateX(0)';
    }

    toggleTaskDetails(taskEl) {
        const details = taskEl.querySelector('.task-details');
        details.classList.toggle('visible');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="notification-icon fas fa-${this.getNotificationIcon(type)}"></i>
                <span class="notification-message">${message}</span>
            </div>
            <button class="notification-close">&times;</button>
        `;

        const container = document.querySelector('.notification-container');
        container.appendChild(notification);

        // Auto-remove notification
        setTimeout(() => {
            notification.classList.add('hiding');
            setTimeout(() => notification.remove(), 300);
        }, 3000);

        // Manual close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.add('hiding');
            setTimeout(() => notification.remove(), 300);
        });
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }
}

// Initialize the task manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.taskManager = new MobileTaskManager();
});