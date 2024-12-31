from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
import json
from datetime import timedelta

from apps.pomodoro.models import PomodoroSession, PomodoroSettings
from apps.tasks.models import Task, TaskEvent

class PomodoroAPIView(LoginRequiredMixin, View):
    """Vista API mejorada para manejar operaciones AJAX de sesiones Pomodoro"""
    
    def get_active_session(self, user):
        """Obtener la sesión activa del usuario si existe"""
        return PomodoroSession.objects.filter(
            user=user,
            status__in=['in_progress', 'paused']
        ).first()
    
    def calculate_session_duration(self, session_type, settings):
        """Calcular la duración según el tipo de sesión y configuración"""
        duration_map = {
            'pomodoro': settings.pomodoro_duration,
            'short_break': settings.short_break_duration,
            'long_break': settings.long_break_duration
        }
        return duration_map.get(session_type)

    @transaction.atomic
    def handle_start_session(self, request, data):
        """Manejar el inicio de una nueva sesión"""
        task_id = data.get('task_id')
        session_type = data.get('session_type', 'pomodoro')
        enable_audio = data.get('enable_audio', False)
        
        # Verificar si hay una sesión activa
        active_session = self.get_active_session(request.user)
        if active_session:
            return JsonResponse({
                'error': 'Ya existe una sesión activa',
                'session_data': self.get_session_data(active_session)
            }, status=400)
        
        task = get_object_or_404(Task, id=task_id, user=request.user)
        
        # Verificar si la tarea ya completó sus pomodoros estimados
        if session_type == 'pomodoro' and task.completed_pomodoros >= task.estimated_pomodoros:
            return JsonResponse({
                'error': 'Esta tarea ya ha completado todos sus pomodoros estimados',
                'completed': True
            }, status=400)
        
        settings = request.user.pomodorosettings
        duration = self.calculate_session_duration(session_type, settings)
        
        session = PomodoroSession.objects.create(
            user=request.user,
            task=task,
            session_type=session_type,
            duration=duration,
            status='in_progress',
            background_audio_enabled=enable_audio
        )
        
        # Actualizar estado de la tarea
        if session_type == 'pomodoro' and task.status == 'pending':
            task.status = 'in_progress'
            task.save(update_fields=['status'])
        
        return JsonResponse(self.get_session_data(session))

    @transaction.atomic
    def handle_resume_session(self, session):
        """Manejar la reanudación de una sesión pausada"""
        if session.status != 'paused':
            raise ValidationError('Solo se pueden reanudar sesiones pausadas')
        
        # Calcular la duración de la pausa
        pause_duration = int((timezone.now() - session.last_pause_start).total_seconds())
        session.total_pause_duration += pause_duration
        session.status = 'in_progress'
        session.last_pause_start = None
        session.save()
        
        TaskEvent.objects.create(
            task=session.task,
            event_type='session_resumed',
            description='Sesión reanudada'
        )
        
        return JsonResponse(self.get_session_data(session))

    def get_session_data(self, session):
        """Obtener datos formateados de la sesión"""
        data = {
            'session_id': session.id,
            'status': session.status,
            'session_type': session.session_type,
            'started_at': session.started_at.isoformat(),
            'duration': session.duration,
            'actual_duration': session.actual_duration,
            'pause_count': session.pause_count,
            'interruption_count': session.interruption_count,
            'total_pause_duration': session.total_pause_duration,
            'task': {
                'id': session.task.id,
                'title': session.task.title,
                'status': session.task.status,
                'completed_pomodoros': session.task.completed_pomodoros,
                'estimated_pomodoros': session.task.estimated_pomodoros
            }
        }
        
        if session.ended_at:
            data['ended_at'] = session.ended_at.isoformat()
            
        return data

    def get(self, request, *args, **kwargs):
        active_session = self.get_active_session(request.user)
        if active_session:
            return JsonResponse({
                'active_session': self.get_session_data(active_session)
            })
        return JsonResponse({'active_session': None})
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            action = data.get('action')
            session_id = data.get('session_id')
            
            if action == 'start':
                return self.handle_start_session(request, data)
            
            # Para las demás acciones, necesitamos una sesión existente
            session = get_object_or_404(
                PomodoroSession, 
                id=session_id, 
                user=request.user
            )
            
            if action == 'pause':
                session.pause()
                return JsonResponse(self.get_session_data(session))
                
            elif action == 'resume':
                return self.handle_resume_session(session)
                
            elif action == 'complete':
                session.complete()
                next_session_type = session.calculate_next_session_type()
                response_data = self.get_session_data(session)
                response_data['next_session_type'] = next_session_type
                return JsonResponse(response_data)
                
            elif action == 'cancel':
                print("cancelamiento")
                session.cancel()
                return JsonResponse(self.get_session_data(session))
                
            elif action == 'interrupt':
                session.interrupt()
                return JsonResponse(self.get_session_data(session))
            
            return JsonResponse({'error': 'Acción no válida'}, status=400)
            
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Error interno del servidor'}, status=500)

class PomodoroSessionView(LoginRequiredMixin, TemplateView):
    """Vista mejorada para la interfaz de usuario del Pomodoro"""
    template_name = 'pomodoro/dashboard.html'
    
    def get_or_create_settings(self, user):
        """Get existing settings or create default ones"""
        settings, created = PomodoroSettings.objects.get_or_create(
            user=user,
            defaults={
                'pomodoro_duration': 25,
                'short_break_duration': 5,
                'long_break_duration': 15,
                'pomodoros_until_long_break': 4,
                'auto_start_breaks': False,
                'auto_start_pomodoros': False
            }
        )
        return settings
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        
        settings = self.get_or_create_settings(user)
        
        # Obtener la sesión activa y su tiempo restante
        active_session = PomodoroSession.objects.filter(
            user=user,
            status__in=['in_progress', 'paused']
        ).select_related('task').first()
        
        if active_session:
            elapsed_time = timezone.now() - active_session.started_at
            remaining_time = timedelta(minutes=active_session.duration) - elapsed_time
            context['remaining_minutes'] = max(int(remaining_time.total_seconds() / 60), 0)
        
        # Obtener tareas pendientes priorizadas
        pending_tasks = Task.objects.filter(
            user=user,
            status__in=['pending', 'in_progress']
        ).exclude(
            due_date__lt=today
        ).select_related('category').order_by(
            '-priority',
            'due_date',
            'created_at'
        )[:10]
        
        # Obtener estadísticas del día
        today_sessions = PomodoroSession.objects.filter(
            user=user,
            started_at__date=today
        )
        
        completed_sessions = today_sessions.filter(
            status='completed',
            session_type='pomodoro'
        )
        
        # Calcular estadísticas
        stats = {
            'completed_pomodoros': completed_sessions.count(),
            'total_focus_time': sum(
                session.actual_duration or 0 
                for session in completed_sessions
            ),
            'interruption_count': today_sessions.filter(
                interruption_count__gt=0
            ).count(),
            'pause_count': sum(
                session.pause_count or 0
                for session in today_sessions
            )
        }
        
        # Obtener historial de sesiones organizadas por tarea
        session_history = []
        for task in pending_tasks:
            task_sessions = today_sessions.filter(task=task).order_by('-started_at')
            if task_sessions.exists():
                session_history.append({
                    'task': task,
                    'sessions': task_sessions,
                    'total_time': sum(
                        session.actual_duration or 0 
                        for session in task_sessions.filter(status='completed')
                    )
                })
        
        context.update({
            'active_session': active_session,
            'pending_tasks': pending_tasks,
            'session_history': session_history,
            'stats': stats,
            'settings': settings
        })
        
        return context

class PomodoroSettingsView(LoginRequiredMixin, View):
    """
    Vista para manejar la configuración del Pomodoro
    """
    template_name = 'tasks/pomodoro_settings.html'
    
    def get(self, request, *args, **kwargs):
        settings = request.user.pomodorosettings
        return render(request, self.template_name, {'settings': settings})
    
    def post(self, request, *args, **kwargs):
        settings = request.user.pomodorosettings
        try:
            settings.pomodoro_duration = int(request.POST.get('pomodoro_duration'))
            settings.short_break_duration = int(request.POST.get('short_break_duration'))
            settings.long_break_duration = int(request.POST.get('long_break_duration'))
            settings.pomodoros_until_long_break = int(request.POST.get('pomodoros_until_long_break'))
            settings.auto_start_breaks = request.POST.get('auto_start_breaks') == 'on'
            settings.auto_start_pomodoros = request.POST.get('auto_start_pomodoros') == 'on'
            settings.save()
            return redirect('pomodoro')
        except (ValueError, ValidationError) as e:
            return render(request, self.template_name, {
                'settings': settings,
                'error': str(e)
            })