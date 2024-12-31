from django.db import models
from django.conf import settings
from django.utils import timezone

class TaskCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#000000")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Task Categories"

class Task(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Baja'),
        (2, 'Media'),
        (3, 'Alta'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('postponed', 'Pospuesta'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True)
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateTimeField(null=True, blank=True)
    reminder_time = models.DateTimeField(null=True, blank=True)
    estimated_pomodoros = models.IntegerField(default=1)
    completed_pomodoros = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    reminded_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Verificar si es una nueva tarea o si se modificó reminder_time
        is_new = self._state.adding
        if not is_new:
            old_task = Task.objects.get(pk=self.pk)
            reminder_time_changed = old_task.reminder_time != self.reminder_time
        else:
            reminder_time_changed = False

        super().save(*args, **kwargs)

        # Programar recordatorio si es necesario
        if (is_new or reminder_time_changed) and self.reminder_time and self.reminder_time > timezone.now():
            from apps.tasks.views.task_view import send_task_reminder
            send_task_reminder.apply_async(
                args=[self.id],
                eta=self.reminder_time
            )
        
    def handle_session_pause(self, session):
        """
        Handle task status when a Pomodoro session is paused
        
        Args:
            session: PomodoroSession instance that was paused
        """
        # Only update task status if this is an active task
        if self.status == 'in_progress':
            # Keep track of the pause in task metadata
            self.updated_at = timezone.now()
            self.save(update_fields=['updated_at'])
            
            # You might want to create a TaskEvent to track this pause
            TaskEvent.objects.create(
                task=self,
                event_type='session_paused',
                description=f'Sesión de pomodoro pausada después de {session.actual_duration or 0} minutos'
            )

    def handle_session_cancellation(self, session):
        """
        Handle task status when a Pomodoro session is cancelled
        
        Args:
            session: PomodoroSession instance that was cancelled
        """
        # If this was the only active session for this task, update task status
        active_sessions = self.pomodorosession_set.filter(
            status__in=['in_progress', 'paused']
        ).exclude(id=session.id).exists()
        
        if not active_sessions and self.status == 'in_progress':
            self.status = 'pending'
            self.updated_at = timezone.now()
            self.save(update_fields=['status', 'updated_at'])
            
            # Create a task event to track this cancellation
            TaskEvent.objects.create(
                task=self,
                event_type='session_cancelled',
                description=f'Sesión de pomodoro cancelada después de {session.actual_duration or 0} minutos'
            )

    def handle_session_interruption(self, session):
        """
        Handle task status when a Pomodoro session is interrupted
        
        Args:
            session: PomodoroSession instance that was interrupted
        """
        self.updated_at = timezone.now()
        self.save(update_fields=['updated_at'])
        
        # Create a task event to track this interruption
        TaskEvent.objects.create(
            task=self,
            event_type='session_interrupted',
            description=f'Sesión de pomodoro interrumpida'
        )
    
    class Meta:
        indexes = [
            # ... (índices existentes) ...
            models.Index(fields=['status', 'due_date', 'reminded_at']),
        ]

class TaskEvent(models.Model):
    """Model to track important events in a task's lifecycle"""
    EVENT_TYPES = [
        ('session_started', 'Sesión Iniciada'),
        ('session_paused', 'Sesión Pausada'),
        ('session_resumed', 'Sesión Reanudada'),
        ('session_completed', 'Sesión Completada'),
        ('session_cancelled', 'Sesión Cancelada'),
        ('session_interrupted', 'Sesión Interrumpida'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'event_type', 'created_at'])
        ]
