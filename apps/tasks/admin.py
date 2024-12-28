from django.contrib import admin
from django.utils.html import format_html
from apps.tasks.models import TaskCategory, Task
from apps.notifications.models import Notification
from django.utils import timezone

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color_display', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('name', 'description')
    
    def color_display(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'priority', 'status', 'due_date', 'completed_pomodoros')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    actions = ['mark_completed', 'mark_pending']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'user', 'category')
        }),
        ('Jerarquía', {
            'fields': ('parent_task',)
        }),
        ('Estado y Prioridad', {
            'fields': ('status', 'priority')
        }),
        ('Tiempo', {
            'fields': ('due_date', 'reminder_time')
        }),
        ('Pomodoros', {
            'fields': ('estimated_pomodoros', 'completed_pomodoros')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def mark_completed(self, request, queryset):
        queryset.update(status='completed', completed_at=timezone.now())
    mark_completed.short_description = "Marcar tareas seleccionadas como completadas"

    def mark_pending(self, request, queryset):
        queryset.update(status='pending', completed_at=None)
    mark_pending.short_description = "Marcar tareas seleccionadas como pendientes"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'user', 'task', 'created_at', 'read_status')
    list_filter = ('type', 'created_at', 'read_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at',)
    
    def read_status(self, obj):
        return "Leída" if obj.read_at else "No leída"
    read_status.short_description = "Estado"

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        queryset.update(read_at=timezone.now())
    mark_as_read.short_description = "Marcar notificaciones como leídas"

    def mark_as_unread(self, request, queryset):
        queryset.update(read_at=None)
    mark_as_unread.short_description = "Marcar notificaciones como no leídas"