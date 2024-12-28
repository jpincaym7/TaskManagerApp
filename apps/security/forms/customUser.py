from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
    )
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
    )

    # Campos opcionales para el registro inicial
    notification_frequency = forms.ChoiceField(
        required=False,
        choices=[
            ('high', 'Alta - Múltiples recordatorios diarios'),
            ('medium', 'Media - Recordatorios diarios'),
            ('low', 'Baja - Recordatorios semanales')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    text_size = forms.ChoiceField(
        required=False,
        choices=[
            ('small', 'Pequeño'),
            ('medium', 'Mediano'),
            ('large', 'Grande'),
            ('extra_large', 'Extra Grande')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    terms = forms.BooleanField(
        required=True,
        error_messages={
            'required': 'Debes aceptar los términos y condiciones para registrarte.'
        }
    )

    class Meta:
        from django.contrib.auth import get_user_model
        model = get_user_model()
        fields = (
            'username', 
            'email', 
            'password1', 
            'password2',
            'notification_frequency',
            'text_size'
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = self.Meta.model
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('Este correo electrónico ya está registrado.'))
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        User = self.Meta.model
        if User.objects.filter(username=username).exists():
            raise ValidationError(_('Este nombre de usuario ya está en uso.'))
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        # Establecer valores predeterminados para campos adicionales
        user.notification_frequency = self.cleaned_data.get('notification_frequency', 'medium')
        user.text_size = self.cleaned_data.get('text_size', 'medium')
        
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )
    
    remember = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        
        # Permitir login con email
        if username and '@' in username:
            User = self.Meta.model if hasattr(self, 'Meta') else get_user_model()
            try:
                user = User.objects.get(email=username)
                cleaned_data['username'] = user.username
            except User.DoesNotExist:
                raise ValidationError(_('No existe un usuario con este correo electrónico.'))
                
        return cleaned_data