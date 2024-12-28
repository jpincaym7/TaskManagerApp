// tasks_calendar.js
class TaskCalendar {
    constructor(taskData) {
        this.currentDate = new Date();
        this.selectedDate = new Date();
        this.tasks = taskData.tasks || [];
        this.categories = taskData.categories || [];
        this.view = 'month';
        this.init();
    }

    init() {
        this.container = document.querySelector('.calendar-container');
        if (!this.container) {
            console.error('Calendar container not found');
            return;
        }
        this.renderCalendar();
        this.setupEventListeners();
        this.renderTasks();
        this.setupGestures();
    }

    setupGestures() {
        if (typeof Hammer !== 'undefined') {
            const hammer = new Hammer(this.container);
            hammer.on('swipeleft', () => this.navigateCalendar(1));
            hammer.on('swiperight', () => this.navigateCalendar(-1));
        }
    }

    renderCalendar() {
        const calendarHTML = `
            <div class="calendar-header">
                <div class="calendar-nav">
                    <button class="btn-prev" aria-label="Mes anterior">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <h2 class="current-month"></h2>
                    <button class="btn-next" aria-label="Mes siguiente">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
                <div class="view-options">
                    <button class="btn-view active" data-view="month">Mes</button>
                    <button class="btn-view" data-view="week">Semana</button>
                    <button class="btn-view" data-view="day">Día</button>
                </div>
            </div>
            <div class="calendar-grid"></div>
            <div class="task-details-modal" role="dialog" aria-modal="true" style="display: none;">
                <div class="modal-overlay"></div>
            </div>
        `;
        
        this.container.innerHTML = calendarHTML;
        this.updateCalendarGrid();
    }

    updateCalendarGrid() {
        const grid = this.container.querySelector('.calendar-grid');
        const monthYear = this.currentDate.toLocaleString('es-ES', { 
            month: 'long', 
            year: 'numeric' 
        });
        
        this.container.querySelector('.current-month').textContent = 
            monthYear.charAt(0).toUpperCase() + monthYear.slice(1);

        switch(this.view) {
            case 'month':
                this.renderMonthView(grid);
                break;
            case 'week':
                this.renderWeekView(grid);
                break;
            case 'day':
                this.renderDayView(grid);
                break;
        }
    }

    renderMonthView(grid) {
        const firstDay = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
        const lastDay = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - startDate.getDay());

        const weekDays = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
        
        let gridHTML = `
            <div class="calendar-days" role="row">
                ${weekDays.map(day => 
                    `<div class="day-header" role="columnheader">${day}</div>`
                ).join('')}
            </div>
            <div class="calendar-dates" role="grid">
        `;

        for (let date = new Date(startDate); date <= lastDay || date.getDay() !== 0; date.setDate(date.getDate() + 1)) {
            const isToday = this.isToday(date);
            const isSelected = this.isSelectedDate(date);
            const isCurrentMonth = date.getMonth() === this.currentDate.getMonth();
            
            gridHTML += `
                <div class="calendar-cell ${isToday ? 'today' : ''} 
                                        ${isSelected ? 'selected' : ''} 
                                        ${isCurrentMonth ? '' : 'other-month'}"
                     data-date="${date.toISOString()}"
                     role="gridcell"
                     aria-selected="${isSelected}"
                     aria-label="${date.toLocaleDateString('es-ES', { 
                         weekday: 'long', 
                         year: 'numeric', 
                         month: 'long', 
                         day: 'numeric' 
                     })}">
                    <div class="date-number">${date.getDate()}</div>
                    <div class="task-indicators"></div>
                </div>
            `;
        }

        gridHTML += '</div>';
        grid.innerHTML = gridHTML;
    }

    renderTasks() {
        const taskIndicators = {};
        
        this.tasks.forEach(task => {
            const dateKey = new Date(task.due_date).toISOString().split('T')[0];
            if (!taskIndicators[dateKey]) {
                taskIndicators[dateKey] = [];
            }
            taskIndicators[dateKey].push(task);
        });

        document.querySelectorAll('.calendar-cell').forEach(cell => {
            const dateKey = new Date(cell.dataset.date).toISOString().split('T')[0];
            const cellTasks = taskIndicators[dateKey] || [];
            
            const indicators = cell.querySelector('.task-indicators');
            indicators.innerHTML = cellTasks.slice(0, 3).map(task => {
                const category = this.categories.find(c => c.id === task.category);
                return `
                    <div class="task-indicator" 
                         style="background-color: ${category?.color || '#ddd'}"
                         title="${task.title}"
                         role="status">
                        ${task.priority === 3 ? '!' : ''}
                    </div>
                `;
            }).join('');

            if (cellTasks.length > 3) {
                indicators.innerHTML += `
                    <div class="task-indicator more" role="status">
                        +${cellTasks.length - 3}
                    </div>
                `;
            }
        });
    }

    setupEventListeners() {
        // Navigation
        this.container.querySelector('.btn-prev').addEventListener('click', () => this.navigateCalendar(-1));
        this.container.querySelector('.btn-next').addEventListener('click', () => this.navigateCalendar(1));

        // View switching
        this.container.querySelectorAll('.btn-view').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.container.querySelectorAll('.btn-view').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.view = e.target.dataset.view;
                this.updateCalendarGrid();
            });
        });

        // Cell selection
        this.container.addEventListener('click', (e) => {
            const cell = e.target.closest('.calendar-cell');
            if (cell) {
                this.selectedDate = new Date(cell.dataset.date);
                this.updateCalendarGrid();
                this.showTaskDetails(cell.dataset.date);
            }
        });

        // Modal close on overlay click
        this.container.querySelector('.task-details-modal').addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeTaskModal();
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeTaskModal();
            }
        });
    }

    closeTaskModal() {
        const modal = this.container.querySelector('.task-details-modal');
        modal.style.display = 'none';
    }

    showTaskDetails(dateString) {
        const date = new Date(dateString);
        const tasks = this.tasks.filter(task => {
            const taskDate = new Date(task.due_date);
            return taskDate.toDateString() === date.toDateString();
        });

        const modal = this.container.querySelector('.task-details-modal');
        const modalContent = `
            <div class="modal-overlay"></div>
            <div class="modal-content" role="document">
                <div class="modal-header">
                    <h3>${date.toLocaleDateString('es-ES', { 
                        weekday: 'long', 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                    })}</h3>
                    <button class="close-modal" aria-label="Cerrar">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    ${tasks.length ? this.renderTaskList(tasks) : 
                      '<p class="no-tasks">No hay tareas para este día</p>'}
                    <a href="/tasks/new/?date=${dateString}" 
                       class="btn-add-task">
                        <i class="fas fa-plus"></i> Agregar Tarea
                    </a>
                </div>
            </div>
        `;

        modal.innerHTML = modalContent;
        modal.style.display = 'flex';
        
        modal.querySelector('.close-modal').addEventListener('click', () => {
            this.closeTaskModal();
        });
    }

    renderTaskList(tasks) {
        return `
            <div class="task-list">
                ${tasks.map(task => {
                    const category = this.categories.find(c => c.id === task.category);
                    return `
                        <div class="task-item" data-task-id="${task.id}">
                            <div class="task-status ${task.status}">
                                <i class="fas ${this.getStatusIcon(task.status)}"></i>
                            </div>
                            <div class="task-content">
                                <h4>${task.title}</h4>
                                <div class="task-meta">
                                    <span class="category" 
                                          style="background-color: ${category?.color || '#ddd'}">
                                        ${category?.name || 'Sin categoría'}
                                    </span>
                                    <span class="priority priority-${task.priority}">
                                        ${this.getPriorityLabel(task.priority)}
                                    </span>
                                </div>
                            </div>
                            <a href="/tasks/${task.id}/edit/" 
                               class="btn-edit" 
                               aria-label="Editar tarea">
                                <i class="fas fa-edit"></i>
                            </a>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    getStatusIcon(status) {
        const icons = {
            'pending': 'fa-clock',
            'in_progress': 'fa-spinner fa-spin',
            'completed': 'fa-check',
            'postponed': 'fa-calendar-alt'
        };
        return icons[status] || 'fa-clock';
    }

    getPriorityLabel(priority) {
        return ['', 'Baja', 'Media', 'Alta'][priority] || 'Normal';
    }

    navigateCalendar(direction) {
        switch(this.view) {
            case 'month':
                this.currentDate.setMonth(this.currentDate.getMonth() + direction);
                break;
            case 'week':
                this.currentDate.setDate(this.currentDate.getDate() + (direction * 7));
                break;
            case 'day':
                this.currentDate.setDate(this.currentDate.getDate() + direction);
                break;
        }
        this.updateCalendarGrid();
    }

    isToday(date) {
        const today = new Date();
        return date.toDateString() === today.toDateString();
    }

    isSelectedDate(date) {
        return date.toDateString() === this.selectedDate.toDateString();
    }
}

// Initialize calendar with data from template
document.addEventListener('DOMContentLoaded', function() {
    try {
        const taskDataElement = document.getElementById('task-data');
        if (!taskDataElement) {
            throw new Error('Task data element not found');
        }
        
        const taskData = JSON.parse(taskDataElement.textContent);
        new TaskCalendar(taskData);
        
        // Setup notifications if available
        if ('Notification' in window) {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    setupReminders(taskData.tasks);
                }
            });
        }
    } catch (error) {
        console.error('Error initializing calendar:', error);
    }
});

function setupReminders(tasks) {
    function checkReminders() {
        const now = new Date();
        tasks.forEach(task => {
            if (task.reminder_time) {
                const reminderTime = new Date(task.reminder_time);
                if (Math.abs(now - reminderTime) < 60000) {
                    showNotification('Recordatorio de tarea', {
                        body: task.title,
                        icon: '/static/img/mindhelper-logo.png',
                        tag: `task-${task.id}`,
                        requireInteraction: true
                    });
                }
            }
        });
    }
    
    setInterval(checkReminders, 60000);
}

function showNotification(title, options) {
    if ('Notification' in window && Notification.permission === 'granted') {
        return new Notification(title, options);
    }
    return null;
}