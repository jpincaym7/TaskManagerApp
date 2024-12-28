from django import forms
from apps.pomodoro.models import PomodoroSettings, PomodoroSession

class PomodoroSettingsForm(forms.ModelForm):
    """
    Formulario para configurar las preferencias del Pomodoro
    """
    class Meta:
        model = PomodoroSettings
        fields = [
            'pomodoro_duration',
            'short_break_duration',
            'long_break_duration',
            'pomodoros_until_long_break',
            'auto_start_breaks',
            'auto_start_pomodoros'
        ]
        widgets = {
            'pomodoro_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '60',
                'step': '1'
            }),
            'short_break_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '30',
                'step': '1'
            }),
            'long_break_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '60',
                'step': '1'
            }),
            'pomodoros_until_long_break': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10',
                'step': '1'
            }),
            'auto_start_breaks': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'auto_start_pomodoros': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Validar que el descanso corto sea menor que el pomodoro
        if cleaned_data.get('short_break_duration') >= cleaned_data.get('pomodoro_duration'):
            raise forms.ValidationError(
                "El descanso corto debe ser menor que la duración del pomodoro"
            )

        # Validar que el descanso largo sea menor que el pomodoro
        if cleaned_data.get('long_break_duration') <= cleaned_data.get('short_break_duration'):
            raise forms.ValidationError(
                "El descanso largo debe ser mayor que el descanso corto"
            )

        return cleaned_data

class PomodoroSessionForm(forms.ModelForm):
    """
    Formulario para crear y editar sesiones Pomodoro
    """
    class Meta:
        model = PomodoroSession
        fields = ['task', 'session_type', 'notes']
        widgets = {
            'task': forms.Select(attrs={
                'class': 'form-control'
            }),
            'session_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Notas opcionales sobre la sesión...'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filtrar tareas por usuario
            self.fields['task'].queryset = user.task_set.filter(completed=False)

class QuickPomodoroForm(forms.Form):
    """
    Formulario simplificado para iniciar rápidamente un pomodoro
    """
    task = forms.ModelChoiceField(
        queryset=None,
        empty_label="Selecciona una tarea",
        widget=forms.Select(attrs={
            'class': 'form-control mb-2'
        })
    )
    session_type = forms.ChoiceField(
        choices=PomodoroSession.SESSION_TYPES,
        initial='pomodoro',
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['task'].queryset = user.task_set.filter(completed=False)

class SessionNoteForm(forms.Form):
    """
    Formulario para agregar notas rápidas a una sesión en curso
    """
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '2',
            'placeholder': 'Agrega una nota rápida sobre esta sesión...'
        }),
        required=False
    )

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        
        if session and session.notes:
            self.fields['notes'].initial = session.notes