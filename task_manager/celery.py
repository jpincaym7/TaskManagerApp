import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Establecer la configuración de Django por defecto para el programa 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_manager.settings')

# Crear la aplicación Celery
app = Celery('task_manager')

# Configurar usando el objeto settings de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar tareas de todos los módulos registrados en INSTALLED_APPS
app.autodiscover_tasks()

# Configuración del schedule de tareas periódicas
app.conf.beat_schedule = {
    'daily-task-summary': {
        'task': 'apps.tasks.notifications.send_daily_task_summary',
        'schedule': crontab(hour=7, minute=0),  # 7:00 AM todos los días
    },
    'upcoming-task-reminders': {
        'task': 'apps.tasks.notifications.send_upcoming_task_reminders',
        'schedule': crontab(minute=0, hour='*/4'),  # Cada 4 horas
    },
    'weekly-task-summary': {
        'task': 'apps.tasks.notifications.send_weekly_task_summary',
        'schedule': crontab(hour=8, minute=0, day_of_week='monday'),  # Lunes 8:00 AM
    },
}

# Configuración opcional adicional de Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Guayaquil',
    enable_utc=True,
)