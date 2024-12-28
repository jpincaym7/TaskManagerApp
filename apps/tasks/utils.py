from django.utils import timezone
from apps.notifications.models import Notification

def create_task_notification(user, task, notification_type, scheduled_for=None):
    """
    Crea una notificación relacionada a una tarea.
    
    Args:
        user: Usuario que recibirá la notificación
        task: Tarea relacionada
        notification_type: Tipo de notificación (debe ser uno válido de NOTIFICATION_TYPES)
        scheduled_for: Fecha y hora programada para la notificación
    """
    notification_messages = {
        'task_due': {
            'title': f'Tarea próxima a vencer: {task.title}',
            'message': f'La tarea "{task.title}" vence pronto.'
        },
        'task_overdue': {
            'title': f'Tarea vencida: {task.title}',
            'message': f'La tarea "{task.title}" ha vencido.'
        },
        'pomodoro_complete': {
            'title': 'Pomodoros completados',
            'message': f'Has completado todos los pomodoros estimados para la tarea "{task.title}".'
        },
        'pomodoro_break': {
            'title': 'Tiempo de descanso',
            'message': 'Es hora de tomar un descanso.'
        }
    }
    
    if notification_type not in notification_messages:
        raise ValueError(f'Tipo de notificación inválido: {notification_type}')
        
    message_data = notification_messages[notification_type]
    
    Notification.objects.create(
        user=user,
        task=task,
        type=notification_type,
        title=message_data['title'],
        message=message_data['message'],
        scheduled_for=scheduled_for or timezone.now()
    )