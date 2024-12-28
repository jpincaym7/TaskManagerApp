from django.db import models
from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
from apps.core.models import BaseManager, SoftDeleteModel, TimeStampedModel
from django.db import models
from apps.tasks.models import Task

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('task_due', 'Tarea Próxima'),
        ('task_overdue', 'Tarea Vencida'),
        ('pomodoro_break', 'Descanso Pomodoro'),
        ('pomodoro_complete', 'Pomodoro Completado'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True)