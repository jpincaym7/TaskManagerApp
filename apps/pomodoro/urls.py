from django.urls import path
from apps.pomodoro.views.api_pomodoro import PomodoroAPIView, PomodoroSessionView, PomodoroSettingsView

app_name = 'pomodoro'

urlpatterns = [
    path('', PomodoroSessionView.as_view(), name='dashboard'),
    
    # API para operaciones AJAX
    path('api/', PomodoroAPIView.as_view(), name='pomodoro_api'),
    
    # Configuración del Pomodoro
    path('settings/', PomodoroSettingsView.as_view(), name='pomodoro_settings'),
]