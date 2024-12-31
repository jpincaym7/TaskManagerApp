from datetime import datetime
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
from apps.tasks.models import Task
from django.utils import timezone
from pathlib import Path
from email.mime.image import MIMEImage
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from apps.tasks.models import Task, TaskCategory
from apps.notifications.models import Notification
from apps.tasks.forms.tasksform import MobileTaskForm
from apps.tasks.utils import create_task_notification
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from threading import Thread

def list_tasks_json(request):
    """
    Vista para obtener todas las tareas del usuario en formato JSON con filtros.
    """
    queryset = Task.objects.filter(user=request.user).select_related('category')
    
    # Aplicar filtros
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)
        
    category = request.GET.get('category')
    if category:
        queryset = queryset.filter(category_id=category)
        
    priority = request.GET.get('priority')
    if priority:
        queryset = queryset.filter(priority=priority)
        
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Ordenamiento
    order_by = request.GET.get('order_by', '-created_at')
    tasks = queryset.order_by(order_by)

    data = {
        'tasks': [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "category": {
                    "id": task.category.id if task.category else None,
                    "name": task.category.name if task.category else None,
                    "color": task.category.color if task.category else None,
                },
                "priority": dict(Task.PRIORITY_CHOICES).get(task.priority),
                "status": dict(Task.STATUS_CHOICES).get(task.status),
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "reminder_time": task.reminder_time.isoformat() if task.reminder_time else None,
                "estimated_pomodoros": task.estimated_pomodoros,
                "completed_pomodoros": task.completed_pomodoros,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }
            for task in tasks
        ]
    }

    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10

    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
            
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
            
        order_by = self.request.GET.get('order_by', '-created_at')
        return queryset.order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = TaskCategory.objects.filter(user=self.request.user)
        context['status_choices'] = Task.STATUS_CHOICES
        context['priority_choices'] = Task.PRIORITY_CHOICES
        return context

def send_email_async(email):
    try:
        email.send()
    except Exception as e:
        print(f"Error enviando correo: {str(e)}")

class TaskCreateView(LoginRequiredMixin, View):
    def post(self, request):
        # Recogemos los datos del formulario directamente desde request.POST
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        priority = request.POST.get('priority')
        status = request.POST.get('status')
        due_date = request.POST.get('due_date')
        estimated_pomodoros = request.POST.get('estimated_pomodoros')

        if due_date:
            try:
                due_date = datetime.strptime(due_date, '%Y-%m-%dT%H:%M')
            except ValueError:
                due_date = None

        category = TaskCategory.objects.get(id=category_id) if category_id else None

        task = Task(
            title=title,
            description=description,
            user=request.user,
            category=category,
            priority=priority,
            status=status,
            due_date=due_date,
            estimated_pomodoros=estimated_pomodoros
        )
        task.save()

        # Preparar el correo en segundo plano
        context = {'user': request.user, 'task': task}
        html_content = render_to_string('email/task_created.html', context)
        text_content = strip_tags(html_content)
        email = EmailMultiAlternatives(
            f'Nueva tarea creada: {task.title}',
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email]
        )
        email.attach_alternative(html_content, "text/html")
        logo_path = Path(settings.BASE_DIR) / 'static' / 'img' / 'mindhelper-logo.png'
        if logo_path.exists():
            with open(logo_path, 'rb') as logo_file:
                logo = MIMEImage(logo_file.read())
                logo.add_header('Content-ID', '<logo>')  # Definir el CID del logo
                email.attach(logo)

        # Usar un hilo para enviar el correo
        Thread(target=send_email_async, args=(email,)).start()
        
        return JsonResponse({
            'message': 'Tarea creada exitosamente',
            'task': {
                'title': task.title,
                'description': task.description,
                'category': task.category.name if task.category else 'Sin categoría',
                'priority': task.get_priority_display(),
                'status': task.status,
                'due_date': task.due_date.strftime('%Y-%m-%d %H:%M:%S') if task.due_date else None,
                'estimated_pomodoros': task.estimated_pomodoros,
            }
        })

class TaskDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        task_id = self.kwargs.get('pk')
        task = get_object_or_404(Task, pk=task_id)
        return task.user == self.request.user

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        
        return JsonResponse({
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'category': {
                    'id': task.category.id if task.category else None,
                    'name': task.category.name if task.category else None,
                    'color': task.category.color if task.category else None,
                },
                'priority': task.priority,
                'status': task.status,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'estimated_pomodoros': task.estimated_pomodoros,
                'completed_pomodoros': task.completed_pomodoros,
            }
        })


class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        task_id = self.kwargs.get('pk')
        task = get_object_or_404(Task, pk=task_id)
        return task.user == self.request.user

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        
        # Recoger los datos del formulario directamente desde request.POST
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        priority = request.POST.get('priority')
        status = request.POST.get('status')
        due_date = request.POST.get('due_date')
        estimated_pomodoros = request.POST.get('estimated_pomodoros')

        if due_date:
            try:
                due_date = datetime.strptime(due_date, '%Y-%m-%dT%H:%M')
            except ValueError:
                due_date = None

        category = TaskCategory.objects.get(id=category_id) if category_id else None

        # Actualizar los campos de la tarea
        task.title = title
        task.description = description
        task.category = category
        task.priority = priority
        task.status = status
        task.due_date = due_date
        task.estimated_pomodoros = estimated_pomodoros
        task.save()

        # Manejar las notificaciones de fecha límite
        if task.due_date:
            Notification.objects.filter(
                task=task,
                type='task_due'
            ).delete()
            
            create_task_notification(
                user=request.user,
                task=task,
                notification_type='task_due',
                scheduled_for=task.due_date
            )

        # Preparar el correo en segundo plano
        context = {'user': request.user, 'task': task}
        html_content = render_to_string('email/task_updated.html', context)
        text_content = strip_tags(html_content)
        email = EmailMultiAlternatives(
            f'Tarea actualizada: {task.title}',
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email]
        )
        email.attach_alternative(html_content, "text/html")
        logo_path = Path(settings.BASE_DIR) / 'static' / 'img' / 'mindhelper-logo.png'
        if logo_path.exists():
            with open(logo_path, 'rb') as logo_file:
                logo = MIMEImage(logo_file.read())
                logo.add_header('Content-ID', '<logo>')
                email.attach(logo)

        # Usar un hilo para enviar el correo
        Thread(target=send_email_async, args=(email,)).start()

        return JsonResponse({
            'message': 'Tarea actualizada exitosamente',
            'task': {
                'title': task.title,
                'description': task.description,
                'category': task.category.name if task.category else 'Sin categoría',
                'priority': task.get_priority_display(),
                'status': task.status,
                'due_date': task.due_date.strftime('%Y-%m-%d %H:%M:%S') if task.due_date else None,
                'estimated_pomodoros': task.estimated_pomodoros,
            }
        })

class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        task_id = self.kwargs.get('pk')
        task = get_object_or_404(Task, pk=task_id)
        return task.user == self.request.user

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Tarea eliminada exitosamente'
        })

class TaskStatusUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        status = request.POST.get('status')
        
        if status not in dict(Task.STATUS_CHOICES):
            return JsonResponse({'error': 'Estado inválido'}, status=400)
            
        task.status = status
        
        if status == 'completed':
            task.completed_at = timezone.now()
            
        task.save()
        
        return JsonResponse({
            'status': 'success',
            'new_status': task.get_status_display()
        })

class TaskPomodoroUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        action = request.POST.get('action')
        
        if action == 'increment':
            task.completed_pomodoros = min(
                task.completed_pomodoros + 1,
                task.estimated_pomodoros
            )
        elif action == 'decrement':
            task.completed_pomodoros = max(task.completed_pomodoros - 1, 0)
        else:
            return JsonResponse({'error': 'Acción inválida'}, status=400)
            
        task.save()
        
        if task.completed_pomodoros == task.estimated_pomodoros:
            create_task_notification(
                user=request.user,
                task=task,
                notification_type='pomodoro_complete',
                scheduled_for=timezone.now()
            )
        
        return JsonResponse({
            'status': 'success',
            'completed_pomodoros': task.completed_pomodoros
        })