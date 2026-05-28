from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from apps.users.views import (
    VistaAutoexclusion,
    VistaLimiteDiario,
    VistaMiPerfil,
    VistaRegistro,
    VistaVerificarKyc,
)

urlpatterns = [
    path("register/", VistaRegistro.as_view(), name="register"),
    path("login/", obtain_auth_token, name="login"),
    path("me/", VistaMiPerfil.as_view(), name="me"),
    path("verify-kyc/", VistaVerificarKyc.as_view(), name="verify-kyc"),
    path("self-exclude/", VistaAutoexclusion.as_view(), name="self-exclude"),
    path("limits/daily/", VistaLimiteDiario.as_view(), name="limits-daily"),
]
