from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.views import View
from apps.security.forms.customUser import CustomUserCreationForm, CustomAuthenticationForm

class CustomLoginView(LoginView):
    template_name = 'security/auth.html'
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context
    
    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember', False)
        if not remember_me:
            self.request.session.set_expiry(0)
        
        response = super().form_valid(form)
        messages.success(self.request, '¡Inicio de sesión exitoso!')
        print("Redirigiendo a home...")
        return redirect('home')
    
    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return super().form_invalid(form)

class RegisterView(View):
    template_name = 'security/auth.html'
    form_class = CustomUserCreationForm
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, '¡Registro exitoso! Bienvenido a MindHelper.')
            return redirect('home')
        
        for error in form.errors.values():
            messages.error(request, error)
        return render(request, self.template_name, {'form': form})
    
class LogoutView(View):
    def post(self, request):
        logout(request)  # Termina la sesión del usuario
        messages.success(request, 'Has cerrado sesión exitosamente.')
        return redirect('security:login')