# views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, DetailView, View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
import json

class UserProfileView(LoginRequiredMixin, DetailView):
    """Vista para mostrar el perfil del usuario"""
    template_name = 'security/profile/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_summary'] = self.object.get_daily_task_summary()
        context['accessibility_settings'] = self.object.get_accessibility_settings()
        return context

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar información básica del perfil"""
    template_name = 'security/profile/profile_update.html'
    fields = [
        'email', 'preferred_notification_time', 'notification_frequency',
        'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_email'
    ]
    success_url = reverse_lazy('security:profile')
    
    def get_object(self):
        return self.request.user

class AccessibilitySettingsView(LoginRequiredMixin, View):
    """Vista para manejar configuraciones de accesibilidad"""
    template_name = 'users/accessibility_settings.html'

    def get(self, request):
        return render(request, self.template_name, {
            'user': request.user,
            'settings': request.user.get_accessibility_settings()
        })

    def post(self, request):
        user = request.user
        user.use_high_contrast = request.POST.get('use_high_contrast') == 'on'
        user.text_size = request.POST.get('text_size')
        user.enable_text_to_speech = request.POST.get('enable_text_to_speech') == 'on'
        user.task_complexity_preference = request.POST.get('task_complexity_preference')
        user.save()
        
        return redirect('users:profile')

class TaskPreferencesView(LoginRequiredMixin, View):
    """Vista para manejar preferencias de tareas"""
    template_name = 'users/task_preferences.html'

    def get(self, request):
        return render(request, self.template_name, {
            'user': request.user
        })

    def post(self, request):
        try:
            user = request.user
            preferences = {
                'pomodoro_work_duration': int(request.POST.get('pomodoro_work_duration')),
                'pomodoro_break_duration': int(request.POST.get('pomodoro_break_duration')),
                'daily_task_limit': int(request.POST.get('daily_task_limit')),
                'task_complexity_preference': request.POST.get('task_complexity_preference')
            }
            
            user.update_task_preferences(**preferences)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Preferencias actualizadas correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class DailyTaskSummaryView(LoginRequiredMixin, View):
    """Vista para obtener el resumen diario de tareas"""
    def get(self, request):
        summary = request.user.get_daily_task_summary()
        return JsonResponse(summary)

class UserNeedsAssistanceView(LoginRequiredMixin, View):
    """Vista para verificar si el usuario necesita asistencia"""
    def get(self, request):
        needs_assistance = request.user.needs_assistance()
        return JsonResponse({
            'needs_assistance': needs_assistance,
            'overdue_tasks': request.user.tasks.filter(
                status='pending',
                due_date__lt=timezone.now()
            ).count()
        })

class UserAjaxUpdateView(LoginRequiredMixin, View):
    """Vista para actualizar datos del usuario vía AJAX"""
    def post(self, request):
        try:
            user = request.user
            data = json.loads(request.body)
            
            # Lista de campos permitidos para actualización
            allowed_fields = [
                'email', 'preferred_notification_time', 'notification_frequency',
                'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_email'
            ]
            
            # Actualizar solo los campos permitidos
            for field in allowed_fields:
                if field in data:
                    setattr(user, field, data[field])
            
            user.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Perfil actualizado correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)