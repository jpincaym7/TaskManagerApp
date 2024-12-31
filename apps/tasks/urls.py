from django.urls import path
from apps.tasks.views.calendar import CalendarView
from apps.tasks.views.categories import CategoryCreateView, CategoryDeleteView, CategoryListView, CategoryUpdateView
from apps.tasks.views.task_view import (
    TaskDetailView,
    TaskListView,
    TaskCreateView,
    TaskUpdateView,
    TaskDeleteView,
    TaskStatusUpdateView,
    TaskPomodoroUpdateView,
    list_tasks_json
)

app_name = 'tasks'

urlpatterns = [
    path('list/', TaskListView.as_view(), name='task-list'),  # Listar tareas
    path('list/json/', list_tasks_json, name='task-json'),  # lista_en_json
    path('create/', TaskCreateView.as_view(), name='task-create'),  # Crear tarea
    path('<int:pk>/update/', TaskUpdateView.as_view(), name='task-update'),  # Actualizar tarea
    path('<int:pk>/delete/', TaskDeleteView.as_view(), name='task-delete'),  # Eliminar tarea
    path('<int:pk>/status/', TaskStatusUpdateView.as_view(), name='task-status-update'),  # Actualizar estado
    path('<int:pk>/pomodoro/', TaskPomodoroUpdateView.as_view(), name='task-pomodoro-update'),# Actualizar pomodoros
    path('<int:pk>/detail/', TaskDetailView.as_view(), name='task-detail'),
    path('calendar/', CalendarView.as_view(), name='task-calendar'),
    
    
    # Rutas para categorías
    path(
        'categories/',
        CategoryListView.as_view(),
        name='category_list'
    ),
    path(
        'categories/create/',
        CategoryCreateView.as_view(),
        name='category_create'
    ),
    path(
        'categories/<int:pk>/update/',
        CategoryUpdateView.as_view(),
        name='category_update'
    ),
    path(
        'categories/<int:pk>/delete/',
        CategoryDeleteView.as_view(),
        name='category_delete'
    ),
]
