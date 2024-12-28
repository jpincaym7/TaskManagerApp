from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class UserManager(models.Manager):
    def get_active_users_with_pending_tasks(self):
        """Retorna usuarios activos con tareas pendientes que requieren atención"""
        return self.filter(
            is_active=True,
            tasks__status='pending',
            tasks__due_date__lte=timezone.now() + timezone.timedelta(days=1)
        ).distinct()

    def get_users_needing_assistance(self):
        """Identifica usuarios que pueden necesitar ayuda adicional"""
        return self.filter(
            is_active=True,
            tasks__status='pending',
            tasks__due_date__lt=timezone.now()
        ).annotate(
            overdue_tasks_count=models.Count(
                'tasks',
                filter=models.Q(
                    tasks__status='pending',
                    tasks__due_date__lt=timezone.now()
                )
            )
        ).filter(overdue_tasks_count__gte=3)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    email = models.EmailField(unique=True)
    
    # Resolviendo conflictos de accesores inversos
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.'
    )
    
    # Campos de accesibilidad y preferencias
    preferred_notification_time = models.TimeField(
        default='09:00',
        help_text="Hora preferida para recibir notificaciones diarias"
    )
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('high', 'Alta - Múltiples recordatorios diarios'),
            ('medium', 'Media - Recordatorios diarios'),
            ('low', 'Baja - Recordatorios semanales')
        ],
        default='medium'
    )
    
    # Configuración Pomodoro personalizada
    pomodoro_work_duration = models.PositiveIntegerField(
        default=25,
        validators=[MinValueValidator(15), MaxValueValidator(45)],
        help_text="Duración del período de trabajo en minutos"
    )
    pomodoro_break_duration = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(3), MaxValueValidator(15)],
        help_text="Duración del período de descanso en minutos"
    )
    
    # Preferencias de interfaz (corregido max_length)
    use_high_contrast = models.BooleanField(
        default=False,
        help_text="Activar modo de alto contraste"
    )
    text_size = models.CharField(
        max_length=15,  # Aumentado para acomodar 'extra_large'
        choices=[
            ('small', 'Pequeño'),
            ('medium', 'Mediano'),
            ('large', 'Grande'),
            ('extra_large', 'Extra Grande')
        ],
        default='medium'
    )
    enable_text_to_speech = models.BooleanField(
        default=False,
        help_text="Activar lectura de texto en voz alta"
    )
    
    # Ajustes de asistencia cognitiva
    task_complexity_preference = models.CharField(
        max_length=20,
        choices=[
            ('simple', 'Tareas Simples'),
            ('moderate', 'Tareas Moderadas'),
            ('complex', 'Tareas Complejas')
        ],
        default='moderate',
        help_text="Nivel preferido de complejidad en la presentación de tareas"
    )
    daily_task_limit = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Número máximo de tareas principales por día"
    )
    
    # Contactos de emergencia
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    emergency_contact_email = models.EmailField(
        blank=True,
        null=True
    )
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def get_daily_task_summary(self):
        """Retorna un resumen de las tareas del día"""
        today = timezone.now().date()
        return {
            'pending_tasks': self.tasks.filter(
                status='pending',
                due_date__date=today
            ).count(),
            'completed_tasks': self.tasks.filter(
                status='completed',
                completed_at__date=today
            ).count(),
            'overdue_tasks': self.tasks.filter(
                status='pending',
                due_date__lt=timezone.now()
            ).count()
        }

    def get_accessibility_settings(self):
        """Retorna configuración de accesibilidad del usuario"""
        return {
            'high_contrast': self.use_high_contrast,
            'text_size': self.text_size,
            'text_to_speech': self.enable_text_to_speech,
            'task_complexity': self.task_complexity_preference,
            'notification_frequency': self.notification_frequency
        }

    def update_task_preferences(self, **kwargs):
        """Actualiza preferencias de tareas del usuario"""
        valid_fields = [
            'pomodoro_work_duration',
            'pomodoro_break_duration',
            'daily_task_limit',
            'task_complexity_preference'
        ]
        for field, value in kwargs.items():
            if field in valid_fields:
                setattr(self, field, value)
        self.save()

    def needs_assistance(self):
        """Determina si el usuario necesita asistencia adicional"""
        overdue_tasks = self.tasks.filter(
            status='pending',
            due_date__lt=timezone.now()
        ).count()
        return overdue_tasks >= 3