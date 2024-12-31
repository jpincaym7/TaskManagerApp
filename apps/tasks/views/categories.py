from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from apps.tasks.models import TaskCategory

class CategoryListView(LoginRequiredMixin, ListView):
    model = TaskCategory
    template_name = 'tasks/categories.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return TaskCategory.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_url'] = reverse_lazy('tasks:category_create')
        context['category'] = None  # Para el formulario vacío
        return context

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = TaskCategory
    fields = ['name', 'description', 'color']
    
    def get(self, request, *args, **kwargs):
        # Renderizar el formulario vacío
        form_html = render_to_string(
            'includes/category_form.html',
            {
                'form_url': reverse_lazy('tasks:category_create'),
                'category': None  # Indicamos que es un formulario nuevo
            },
            request=request
        )
        return JsonResponse({'form_html': form_html})
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        category = form.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Categoría creada exitosamente',
            'category': {
                'id': category.id,
                'html': render_to_string(
                    'includes/category_card.html',
                    {'category': category},
                    request=self.request
                )
            }
        })
    
    def form_invalid(self, form):
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = TaskCategory
    fields = ['name', 'description', 'color']
    
    def get(self, request, *args, **kwargs):
        category = self.get_object()
        form_html = render_to_string(
            'includes/category_form.html',
            {
                'form_url': reverse_lazy('tasks:category_update', kwargs={'pk': category.pk}),
                'category': category
            },
            request=request
        )
        return JsonResponse({'form_html': form_html})
    
    def form_valid(self, form):
        category = form.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Categoría actualizada exitosamente',
            'category': {
                'id': category.id,
                'html': render_to_string(
                    'includes/category_card.html',
                    {'category': category},
                    request=self.request
                )
            }
        })
    
    def form_invalid(self, form):
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = TaskCategory
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        category.delete()
        
        # Retorna una respuesta JSON con un mensaje de éxito
        return JsonResponse({
            'status': 'success',
            'message': 'Categoría eliminada exitosamente',
            'category_id': category.id  # Devuelve el ID de la categoría eliminada
        })