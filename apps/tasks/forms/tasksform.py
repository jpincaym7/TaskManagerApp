from django import forms
from apps.tasks.models import Task, TaskCategory
from django.utils.translation import gettext_lazy as _

class MobileTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'category', 'priority', 'status', 'due_date', 'estimated_pomodoros']

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError("El título es obligatorio.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) > 500:
            raise forms.ValidationError("La descripción no puede tener más de 500 caracteres.")
        return description

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if not category:
            raise forms.ValidationError("Debes seleccionar una categoría.")
        return category

    def clean_estimated_pomodoros(self):
        estimated_pomodoros = self.cleaned_data.get('estimated_pomodoros')
        if estimated_pomodoros < 1:
            raise forms.ValidationError("El número de pomodoros debe ser al menos 1.")
        return estimated_pomodoros