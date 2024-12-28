from django.contrib import admin
from apps.security.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ['email', 'username']  # Habilita la búsqueda por correo y nombre de usuario
    list_display = ['email', 'username', 'is_active', 'date_joined']  # Campos visibles en la lista
    list_filter = ['is_active', 'date_joined']  # Filtros en la vista del administrador
    readonly_fields = ['id', 'date_joined', 'last_login']  # Campos que no se pueden editar
