from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.tasks.models import Task, TaskEvent

class PomodoroSettings(models.Model):
    """Configuración personalizada de Pomodoro para cada usuario"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pomodoro_duration = models.IntegerField(
        default=25,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Duración del pomodoro en minutos"
    )
    short_break_duration = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Duración del descanso corto en minutos"
    )
    long_break_duration = models.IntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Duración del descanso largo en minutos"
    )
    pomodoros_until_long_break = models.IntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Número de pomodoros antes de un descanso largo"
    )
    auto_start_breaks = models.BooleanField(
        default=True,
        help_text="Iniciar descansos automáticamente"
    )
    auto_start_pomodoros = models.BooleanField(
        default=False,
        help_text="Iniciar pomodoros automáticamente después de un descanso"
    )

    class Meta:
        verbose_name = "Configuración Pomodoro"
        verbose_name_plural = "Configuraciones Pomodoro"
        app_label = 'tasks'

    def __str__(self):
        return f"Configuración Pomodoro de {self.user.username}"

class PomodoroSession(models.Model):
    SESSION_TYPES = [
        ('pomodoro', 'Pomodoro'),
        ('short_break', 'Descanso Corto'),
        ('long_break', 'Descanso Largo')
    ]
    
    STATUS_CHOICES = [
        ('in_progress', 'En Progreso'),
        ('paused', 'Pausado'),
        ('completed', 'Completado'),
        ('interrupted', 'Interrumpido'),
        ('cancelled', 'Cancelado')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(help_text='Duración planificada en minutos')
    actual_duration = models.IntegerField(null=True, blank=True, help_text='Duración real en minutos')
    
    pause_count = models.IntegerField(default=0)
    total_pause_duration = models.IntegerField(default=0, help_text='Duración total de pausas en segundos')
    last_pause_start = models.DateTimeField(null=True, blank=True)
    
    interruption_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    # Nuevo campo para tracking de audio
    background_audio_enabled = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status', 'started_at']),
            models.Index(fields=['task', 'session_type'])
        ]

    def clean(self):
        if self.status == 'in_progress' and PomodoroSession.objects.filter(
            user=self.user,
            status='in_progress'
        ).exclude(pk=self.pk).exists():
            raise ValidationError('Ya existe una sesión activa para este usuario')

    def save(self, *args, **kwargs):
        self.clean()
        if self.status in ['completed', 'interrupted', 'cancelled'] and not self.ended_at:
            self.ended_at = timezone.now()
            if self.started_at:
                # Calcular duración real considerando pausas
                total_duration = (self.ended_at - self.started_at).total_seconds()
                self.actual_duration = int((total_duration - self.total_pause_duration) / 60)
                
                # Actualizar contador de pomodoros completados si aplica
                if self.status == 'completed' and self.session_type == 'pomodoro':
                    self.task.completed_pomodoros += 1
                    self.task.save()
        
        super().save(*args, **kwargs)

    def pause(self):
        """Pausar la sesión actual y actualizar el estado de la tarea"""
        if self.status != 'in_progress':
            raise ValidationError('Solo se pueden pausar sesiones en progreso')
        
        self.status = 'paused'
        self.last_pause_start = timezone.now()
        self.pause_count += 1
        self.save()
        
        # Notify task about the pause
        self.task.handle_session_pause(self)

    def interrupt(self):
        """Registrar una interrupción en la sesión y notificar a la tarea"""
        if self.status not in ['in_progress', 'paused']:
            raise ValidationError('Solo se pueden interrumpir sesiones activas o pausadas')
        
        self.interruption_count += 1
        self.save()
        
        # Notify task about the interruption
        self.task.handle_session_interruption(self)

    def cancel(self):
        """Cancelar la sesión actual y actualizar el estado de la tarea"""
        if self.status not in ['in_progress', 'paused']:
            raise ValidationError('Solo se pueden cancelar sesiones activas o pausadas')
        
        if self.status == 'paused':
            pause_duration = int((timezone.now() - self.last_pause_start).total_seconds())
            self.total_pause_duration += pause_duration
            
        # Verificar si hay otras sesiones activas para la tarea
        has_other_active_sessions = PomodoroSession.objects.filter(
            task=self.task,
            status__in=['in_progress', 'paused']
        ).exclude(id=self.id).exists()
        
        # Solo cambiar estado de la tarea si no hay otras sesiones activas
        if not has_other_active_sessions:
            completed_pomodoros = PomodoroSession.objects.filter(
                task=self.task,
                status='completed',
                session_type='pomodoro'
            ).count()
            
            # Si no hemos alcanzado los pomodoros estimados, volver a pending
            if completed_pomodoros < self.task.estimated_pomodoros:
                self.task.status = 'pending'
                self.task.save(update_fields=['status'])
        
        self.status = 'cancelled'
        self.ended_at = timezone.now()
        self.save()
        
        # Registrar el evento
        TaskEvent.objects.create(
            task=self.task,
            event_type='session_cancelled',
            description=f'Sesión cancelada después de {self.actual_duration or 0} minutos'
        )
    
    def complete(self):
        """Completar la sesión y actualizar el estado de la tarea"""
        if self.status not in ['in_progress', 'paused']:
            raise ValidationError('Solo se pueden completar sesiones activas o pausadas')
        
        if self.status == 'paused':
            pause_duration = int((timezone.now() - self.last_pause_start).total_seconds())
            self.total_pause_duration += pause_duration
        
        self.status = 'completed'
        self.ended_at = timezone.now()
        
        # Actualizar el contador de pomodoros completados
        if self.session_type == 'pomodoro':
            self.task.completed_pomodoros += 1
            
            # Verificar si hemos alcanzado el estimado
            if self.task.completed_pomodoros >= self.task.estimated_pomodoros:
                self.task.status = 'completed'
                self.task.completed_at = timezone.now()
            
            self.task.save(update_fields=['completed_pomodoros', 'status', 'completed_at'])
        
        self.save()

    def calculate_next_session_type(self):
        """Determinar el tipo de la siguiente sesión"""
        if self.session_type != 'pomodoro':
            return 'pomodoro'
        
        completed_pomodoros = PomodoroSession.objects.filter(
            user=self.user,
            session_type='pomodoro',
            status='completed',
            started_at__date=timezone.now().date()
        ).count()
        
        settings = self.user.pomodorosettings
        if completed_pomodoros % settings.pomodoros_until_long_break == 0:
            return 'long_break'
        return 'short_break'