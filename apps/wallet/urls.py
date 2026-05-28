from django.urls import path

from apps.wallet.views import BalanceView, DepositView

urlpatterns = [
    path("balance/", BalanceView.as_view(), name="wallet-balance"),
    path("deposit/", DepositView.as_view(), name="wallet-deposit"),
]
