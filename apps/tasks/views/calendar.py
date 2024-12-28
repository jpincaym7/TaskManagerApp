from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import datetime
from apps.tasks.models import Task, TaskCategory

class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the requested date from query params
        requested_date = self.request.GET.get('date')
        
        # Initialize start_date
        if requested_date:
            try:
                # Parse the ISO format date string
                start_date = datetime.fromisoformat(requested_date).date()
            except (TypeError, ValueError):
                # If parsing fails, use current date
                start_date = timezone.now().date()
        else:
            # If no date provided, use current date
            start_date = timezone.now().date()
        
        # Always start from the first day of the month
        start_date = start_date.replace(day=1)
        
        # Calculate end date (45 days from start_date)
        end_date = (start_date + timezone.timedelta(days=45)).replace(day=1)
        
        # Get tasks
        context['tasks'] = Task.objects.filter(
            user=self.request.user,
            due_date__range=[start_date, end_date]
        ).select_related('category')
        
        # Get categories
        context['categories'] = TaskCategory.objects.filter(
            user=self.request.user
        )
        
        return context