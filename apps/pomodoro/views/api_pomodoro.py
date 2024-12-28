from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
from apps.pomodoro.models import PomodoroSession, PomodoroSettings
from apps.tasks.models import Task

class PomodoroAPIView(LoginRequiredMixin, View):
    """
    Vista API para manejar operaciones AJAX de sesiones Pomodoro
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            action = data.get('action')
            session_id = data.get('session_id')
            
            if session_id:
                session = get_object_or_404(PomodoroSession, id=session_id, user=request.user)
            
            if action == 'start':
                task_id = data.get('task_id')
                session_type = data.get('session_type', 'pomodoro')
                
                # Verificar si hay una sesión activa
                active_session = PomodoroSession.objects.filter(
                    user=request.user,
                    status__in=['in_progress', 'paused']
                ).first()
                
                if active_session:
                    return JsonResponse({
                        'error': 'Ya existe una sesión activa'
                    }, status=400)
                
                # Obtener la duración según la configuración del usuario
                settings = request.user.pomodorosettings
                duration = {
                    'pomodoro': settings.pomodoro_duration,
                    'short_break': settings.short_break_duration,
                    'long_break': settings.long_break_duration
                }.get(session_type)
                
                session = PomodoroSession.objects.create(
                    user=request.user,
                    task_id=task_id,
                    session_type=session_type,
                    duration=duration
                )
                
            elif action == 'pause':
                session.pause()
                
            elif action == 'resume':
                session.resume()
                
            elif action == 'complete':
                session.complete()
                next_session_type = session.calculate_next_session_type()
                
            elif action == 'cancel':
                session.cancel()
                
            elif action == 'interrupt':
                session.interrupt()
                
            else:
                return JsonResponse({'error': 'Acción no válida'}, status=400)
            
            response_data = {
                'session_id': session.id,
                'status': session.status,
                'started_at': session.started_at.isoformat(),
                'duration': session.duration,
                'actual_duration': session.actual_duration,
                'pause_count': session.pause_count,
                'interruption_count': session.interruption_count
            }
            
            if action == 'complete':
                response_data['next_session_type'] = next_session_type
            
            return JsonResponse(response_data)
            
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Error interno del servidor'}, status=500)

class PomodoroSessionView(LoginRequiredMixin, TemplateView):
    """
    Vista principal para la interfaz de usuario del Pomodoro
    """
    template_name = 'pomodoro/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener la sesión activa si existe
        active_session = PomodoroSession.objects.filter(
            user=self.request.user,
            status__in=['in_progress', 'paused']
        ).first()
        
        # Obtener las tareas pendientes
        pending_tasks = Task.objects.exclude(
            status__in=['completed', 'in_progress', 'postponed']
        ).filter(
            user=self.request.user
        ).order_by('due_date')

        
        # Obtener el historial de sesiones del día
        today_sessions = PomodoroSession.objects.filter(
            user=self.request.user,
            started_at__date=timezone.now().date()
        ).order_by('-started_at')
        
        # Obtener estadísticas del día
        completed_pomodoros = today_sessions.filter(
            session_type='pomodoro',
            status='completed'
        ).count()
        
        total_focus_time = sum(
            session.actual_duration or 0 
            for session in today_sessions.filter(status='completed')
        )
        
        context.update({
            'active_session': active_session,
            'pending_tasks': pending_tasks,
            'today_sessions': today_sessions,
            'completed_pomodoros': completed_pomodoros,
            'total_focus_time': total_focus_time,
            'settings': self.request.user.pomodorosettings
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