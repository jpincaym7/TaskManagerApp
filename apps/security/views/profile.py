from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, DetailView, View, ListView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Sum
import json

from apps.security.models import User

class UserProfileView(LoginRequiredMixin, DetailView):
    """Vista detallada del perfil de usuario con todas sus configuraciones y estadísticas"""
    template_name = 'security/profile/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        
        # Obtener resumen de tareas
        context['task_summary'] = user.get_daily_task_summary()
        
        # Obtener configuraciones de accesibilidad
        context['accessibility_settings'] = user.get_accessibility_settings()
        
        # Añadir estadísticas de Pomodoro
        context['pomodoro_stats'] = {
            'work_duration': user.pomodoro_work_duration,
            'break_duration': user.pomodoro_break_duration,
        }
        
        # Añadir información de contacto de emergencia
        context['emergency_contact'] = {
            'name': user.emergency_contact_name,
            'phone': user.emergency_contact_phone,
            'email': user.emergency_contact_email
        }
        
        # Obtener tareas pendientes organizadas por prioridad
        context['pending_tasks'] = user.tasks.filter(
            status='pending'
        ).order_by('-priority', 'due_date')
        
        return context

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualización completa del perfil de usuario"""
    template_name = 'security/profile/profile_update.html'
    fields = [
        'email', 'username', 'first_name', 'last_name',
        'preferred_notification_time', 'notification_frequency',
        'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_email',
        'pomodoro_work_duration', 'pomodoro_break_duration',
        'daily_task_limit'
    ]
    success_url = reverse_lazy('security:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Perfil actualizado exitosamente.')
            return response
        except ValidationError as e:
            messages.error(self.request, f'Error al actualizar perfil: {str(e)}')
            return self.form_invalid(form)

class AccessibilitySettingsView(LoginRequiredMixin, View):
    """Vista mejorada para gestionar configuraciones de accesibilidad"""
    template_name = 'users/accessibility_settings.html'

    def get(self, request):
        return render(request, self.template_name, {
            'user': request.user,
            'settings': request.user.get_accessibility_settings(),
            'text_size_choices': User._meta.get_field('text_size').choices,
            'task_complexity_choices': User._meta.get_field('task_complexity_preference').choices
        })

    def post(self, request):
        user = request.user
        try:
            # Actualizar configuraciones de accesibilidad
            user.use_high_contrast = request.POST.get('use_high_contrast') == 'on'
            user.text_size = request.POST.get('text_size')
            user.enable_text_to_speech = request.POST.get('enable_text_to_speech') == 'on'
            user.task_complexity_preference = request.POST.get('task_complexity_preference')
            
            # Validar y guardar
            user.full_clean()
            user.save()
            
            messages.success(request, 'Configuraciones de accesibilidad actualizadas correctamente')
            return redirect('users:profile')
            
        except ValidationError as e:
            messages.error(request, f'Error al actualizar configuraciones: {str(e)}')
            return self.get(request)

class TaskPreferencesView(LoginRequiredMixin, View):
    """Vista mejorada para gestionar preferencias de tareas"""
    template_name = 'users/task_preferences.html'

    def get(self, request):
        return render(request, self.template_name, {
            'user': request.user,
            'complexity_choices': User._meta.get_field('task_complexity_preference').choices,
            'notification_choices': User._meta.get_field('notification_frequency').choices
        })

    def post(self, request):
        try:
            user = request.user
            preferences = {
                'pomodoro_work_duration': int(request.POST.get('pomodoro_work_duration')),
                'pomodoro_break_duration': int(request.POST.get('pomodoro_break_duration')),
                'daily_task_limit': int(request.POST.get('daily_task_limit')),
                'task_complexity_preference': request.POST.get('task_complexity_preference'),
                'notification_frequency': request.POST.get('notification_frequency'),
                'preferred_notification_time': request.POST.get('preferred_notification_time')
            }
            
            user.update_task_preferences(**preferences)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Preferencias actualizadas correctamente'
            })
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error inesperado: {str(e)}'
            }, status=500)

class DailyTaskSummaryView(LoginRequiredMixin, View):
    """Vista mejorada para obtener resumen detallado de tareas diarias"""
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        
        # Obtener resumen básico
        summary = user.get_daily_task_summary()
        
        # Añadir información adicional
        tasks_by_priority = user.tasks.filter(
            due_date__date=today
        ).values('priority').annotate(
            count=Count('id')
        )
        
        summary.update({
            'tasks_by_priority': {
                item['priority']: item['count'] 
                for item in tasks_by_priority
            },
            'completed_pomodoros': user.tasks.filter(
                status='completed',
                completed_at__date=today
            ).aggregate(
                total=Sum('completed_pomodoros')
            )['total'] or 0
        })
        
        return JsonResponse(summary)

class UserNeedsAssistanceView(LoginRequiredMixin, View):
    """Vista mejorada para verificar necesidades de asistencia del usuario"""
    def get(self, request):
        user = request.user
        overdue_tasks = user.tasks.filter(
            status='pending',
            due_date__lt=timezone.now()
        )
        
        high_priority_overdue = overdue_tasks.filter(priority=3).count()
        needs_assistance = user.needs_assistance()
        
        response_data = {
            'needs_assistance': needs_assistance,
            'overdue_tasks': overdue_tasks.count(),
            'high_priority_overdue': high_priority_overdue,
            'task_completion_rate': self._calculate_completion_rate(user),
            'assistance_reasons': self._get_assistance_reasons(user)
        }
        
        return JsonResponse(response_data)
    
    def _calculate_completion_rate(self, user):
        """Calcula la tasa de completitud de tareas del usuario"""
        total_tasks = user.tasks.count()
        if total_tasks == 0:
            return 100
        
        completed_tasks = user.tasks.filter(status='completed').count()
        return round((completed_tasks / total_tasks) * 100, 2)
    
    def _get_assistance_reasons(self, user):
        """Determina las razones por las que el usuario podría necesitar asistencia"""
        reasons = []
        overdue_tasks = user.tasks.filter(
            status='pending',
            due_date__lt=timezone.now()
        )
        
        if overdue_tasks.filter(priority=3).exists():
            reasons.append('Tareas de alta prioridad vencidas')
        
        if overdue_tasks.count() >= 3:
            reasons.append('Múltiples tareas vencidas')
        
        completion_rate = self._calculate_completion_rate(user)
        if completion_rate < 50:
            reasons.append('Baja tasa de completitud de tareas')
            
        return reasons

class UserAjaxUpdateView(LoginRequiredMixin, View):
    """Vista mejorada para actualización AJAX del perfil de usuario"""
    def post(self, request):
        try:
            user = request.user
            
            # Lista de campos permitidos
            allowed_fields = [
                'first_name', 'last_name', 'preferred_notification_time', 
                'notification_frequency', 'emergency_contact_name', 
                'emergency_contact_phone', 'emergency_contact_email',
                'pomodoro_work_duration', 'pomodoro_break_duration',
                'daily_task_limit', 'task_complexity_preference',
                'use_high_contrast', 'text_size', 'enable_text_to_speech'
            ]
            
            # Actualizar campos permitidos
            updated_fields = set()  # Usamos set para evitar duplicados
            
            # Procesar campos normales
            for field in allowed_fields:
                value = request.POST.get(field)
                if value not in [None, '']:
                    if field in ['use_high_contrast', 'enable_text_to_speech']:
                        setattr(user, field, value == 'on')
                    else:
                        setattr(user, field, value)
                    updated_fields.add(field)
            
            # Procesar la foto de perfil
            if 'profile_photo' in request.FILES:
                # Si ya existe una foto, la eliminamos
                if user.profile_photo:
                    user.profile_photo.delete(save=False)
                
                user.profile_photo = request.FILES['profile_photo']
                updated_fields.add('profile_photo')
            
            if not updated_fields:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No se proporcionaron campos válidos para actualizar'
                }, status=400)
            
            # Validar y guardar
            try:
                user.full_clean()
                user.save(update_fields=updated_fields)
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Error de validación',
                    'errors': {field: msgs[0] for field, msgs in e.message_dict.items()}
                }, status=400)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Perfil actualizado correctamente',
                'updated_fields': list(updated_fields),
                'profile_photo_url': user.get_profile_photo() if 'profile_photo' in updated_fields else None
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error inesperado: {str(e)}'
            }, status=500)