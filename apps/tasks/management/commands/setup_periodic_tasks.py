from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.image import MIMEImage
from apps.tasks.models import Task

@shared_task
def send_daily_task_summary():
    """
    Envía un resumen diario de tareas pendientes a los usuarios.
    Se ejecuta una vez al día a primera hora.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    for user in User.objects.filter(is_active=True):
        # Obtener tareas pendientes y en progreso
        today = timezone.localtime().date()
        week_end = today + timedelta(days=7)
        
        tasks = Task.objects.filter(
            user=user,
            status__in=['pending', 'in_progress'],
        ).filter(
            Q(due_date__date=today) |  # Tareas para hoy
            Q(due_date__date__range=[today, week_end])  # Tareas para esta semana
        ).order_by('due_date')
        
        if not tasks.exists():
            continue
        
        # Separar tareas por urgencia
        today_tasks = tasks.filter(due_date__date=today)
        week_tasks = tasks.filter(due_date__date__range=[today + timedelta(days=1), week_end])
        
        context = {
            'user': user,
            'today_tasks': today_tasks,
            'week_tasks': week_tasks,
            'today_date': today,
        }
        
        send_task_notification_email(
            user_email=user.email,
            template_name='email/daily_task_summary.html',
            context=context,
            subject='Resumen diario de tareas pendientes'
        )

@shared_task
def send_upcoming_task_reminders():
    """
    Envía recordatorios para tareas próximas a vencer.
    Se ejecuta cada 4 horas.
    """
    now = timezone.localtime()
    reminder_window = now + timedelta(hours=24)  # Recordar tareas que vencen en las próximas 24 horas
    
    tasks = Task.objects.filter(
        status__in=['pending', 'in_progress'],
        due_date__range=[now, reminder_window],
        reminded_at__isnull=True  # Campo nuevo para evitar recordatorios duplicados
    )
    
    for task in tasks:
        context = {
            'user': task.user,
            'task': task,
            'hours_remaining': (task.due_date - now).total_seconds() / 3600
        }
        
        send_task_notification_email(
            user_email=task.user.email,
            template_name='email/task_due_reminder.html',
            context=context,
            subject=f'Recordatorio: La tarea "{task.title}" vence pronto'
        )
        
        # Marcar como recordada
        task.reminded_at = now
        task.save(update_fields=['reminded_at'])

@shared_task
def send_weekly_task_summary():
    """
    Envía un resumen semanal de tareas pendientes y completadas.
    Se ejecuta una vez a la semana.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    today = timezone.localtime().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    for user in User.objects.filter(is_active=True):
        completed_tasks = Task.objects.filter(
            user=user,
            status='completed',
            completed_at__date__range=[week_start, week_end]
        )
        
        pending_tasks = Task.objects.filter(
            user=user,
            status__in=['pending', 'in_progress'],
            due_date__date__lte=week_end
        )
        
        if not (completed_tasks.exists() or pending_tasks.exists()):
            continue
            
        context = {
            'user': user,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'week_start': week_start,
            'week_end': week_end
        }
        
        send_task_notification_email(
            user_email=user.email,
            template_name='email/weekly_task_summary.html',
            context=context,
            subject='Resumen semanal de tareas'
        )

def send_task_notification_email(user_email, template_name, context, subject):
    """
    Función auxiliar para enviar correos de notificación.
    
    Args:
        user_email (str): Email del destinatario
        template_name (str): Nombre del template HTML
        context (dict): Contexto para el template
        subject (str): Asunto del correo
    """
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user_email]
    )
    
    email.attach_alternative(html_content, "text/html")
    
    # Adjuntar logo si existe
    logo_path = Path(settings.BASE_DIR) / 'static' / 'img' / 'mindhelper-logo.png'
    if logo_path.exists():
        with open(logo_path, 'rb') as logo_file:
            logo = MIMEImage(logo_file.read())
            logo.add_header('Content-ID', '<logo>')
            email.attach(logo)
    
    email.send()
