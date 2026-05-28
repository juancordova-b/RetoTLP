from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.users.models import AccountStatus, UserProfile
from apps.wallet import services
from apps.wallet.models import EntryDirection, LedgerAccount

User = get_user_model()


@pytest.fixture
def usuario_verificado(db):
    user = User.objects.create_user(username="testuser", password="testpass123")
    UserProfile.objects.create(
        user=user,
        dni="12345671",
        fecha_nacimiento="2000-05-15",
        status=AccountStatus.VERIFICADO,
        limite_deposito_diario=Decimal("1000.0000"),
    )
    return user


@pytest.mark.django_db
def test_deposito_aumenta_saldo(usuario_verificado):
    services.recarga_simulada(usuario_verificado, Decimal("100.0000"))
    assert services.calcular_saldo(usuario_verificado) == Decimal("100.0000")


@pytest.mark.django_db
def test_partida_doble_balanceada(usuario_verificado):
    tx = services.recarga_simulada(usuario_verificado, Decimal("50.0000"))
    assert services.verificar_transaccion_balanceada(tx) is True


@pytest.mark.django_db
def test_idempotencia_deposito(usuario_verificado):
    key = "idem-test-001"
    tx1 = services.recarga_simulada(usuario_verificado, Decimal("10.0000"), idempotency_key=key)
    tx2 = services.recarga_simulada(usuario_verificado, Decimal("10.0000"), idempotency_key=key)
    assert tx1.id == tx2.id
    assert services.calcular_saldo(usuario_verificado) == Decimal("10.0000")


@pytest.mark.django_db
def test_bloqueo_apuesta_reduce_wallet(usuario_verificado):
    services.recarga_simulada(usuario_verificado, Decimal("100.0000"))
    services.bloquear_fondos_apuesta(usuario_verificado, Decimal("40.0000"), bet_id="bet-1")
    assert services.calcular_saldo(usuario_verificado) == Decimal("60.0000")
    pendiente = services.calcular_saldo(
        usuario_verificado, account=LedgerAccount.APUESTAS_PENDIENTES
    )
    assert pendiente == Decimal("40.0000")
