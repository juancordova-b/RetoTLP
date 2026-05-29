
from django.urls import path

from apps.wallet.views import VistaBonoBienvenida, VistaDeposito, VistaRetiro, VistaSaldo, VistaTransferencia

urlpatterns = [
    path("balance/", VistaSaldo.as_view(), name="wallet-balance"),
    path("deposit/", VistaDeposito.as_view(), name="wallet-deposit"),
    path("withdraw/", VistaRetiro.as_view(), name="wallet-withdraw"),
    path("transfer/", VistaTransferencia.as_view(), name="wallet-transfer"),
    path("bonus/welcome/", VistaBonoBienvenida.as_view(), name="wallet-bonus-welcome"),
]