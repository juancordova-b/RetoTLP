from django.contrib import admin

from apps.users.models import PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "dni",
        "dni_digito_verificador",
        "status",
        "fecha_nacimiento",
        "limite_deposito_diario",
    )
    list_filter = ("status",)
    search_fields = ("user__username", "dni")
