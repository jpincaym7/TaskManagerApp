from django.urls import path
from apps.security.views.authenticate import CustomLoginView, RegisterView, LogoutView
from apps.security.views.profile import AccessibilitySettingsView, DailyTaskSummaryView, TaskPreferencesView, UserAjaxUpdateView, UserNeedsAssistanceView, UserProfileUpdateView, UserProfileView

app_name = 'security'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/',LogoutView.as_view(), name='logout' ),
     # Vistas principales
    path('profile/', 
         UserProfileView.as_view(), 
         name='profile'),
    path('profile/update/', 
         UserProfileUpdateView.as_view(), 
         name='profile-update'),
    path('profile/accessibility/', 
         AccessibilitySettingsView.as_view(), 
         name='accessibility-settings'),
    path('profile/task-preferences/', 
         TaskPreferencesView.as_view(), 
         name='task-preferences'),
         
    # Endpoints para AJAX
    path('profile/ajax-update/', 
         UserAjaxUpdateView.as_view(), 
         name='ajax-update'),
    path('profile/task-summary/', 
         DailyTaskSummaryView.as_view(), 
         name='task-summary'),
    path('profile/needs-assistance/', 
         UserNeedsAssistanceView.as_view(), 
         name='needs-assistance'),
]