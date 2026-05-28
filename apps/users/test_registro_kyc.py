from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.users import services as users_services
from apps.users.models import EstadoCuenta, PerfilUsuario
from apps.users.serializers import RegistroSerializer
from apps.users.validators import calcular_digito_verificador_tarjeta
from apps.wallet import services as wallet_services

User = get_user_model()


@pytest.mark.django_db
def test_registro_acepta_dni_con_digito_verificador_correcto():
    dni = "77814916"
    serializer = RegistroSerializer(
        data={
            "username": "kyc_ok",
            "email": "kyc_ok@example.com",
            "password": "testpass123",
            "dni": dni,
            "dni_digito_verificador": calcular_digito_verificador_tarjeta(dni),
            "fecha_nacimiento": date(2000, 1, 1),
        }
    )

    assert serializer.is_valid(), serializer.errors
    user = serializer.save()
    assert user.perfil.status == EstadoCuenta.PENDIENTE_VERIFICACION
    assert user.perfil.dni_digito_verificador == calcular_digito_verificador_tarjeta(dni)


@pytest.mark.django_db
def test_dni_real_77814916_acepta_digito_3_de_tarjeta():
    """Caso real: tarjeta física con verificador 3 (no el 8.º dígito del número)."""
    assert calcular_digito_verificador_tarjeta("77814916") == "3"


@pytest.mark.django_db
def test_registro_rechaza_dni_con_digito_verificador_incorrecto():
    serializer = RegistroSerializer(
        data={
            "username": "kyc_bad",
            "email": "kyc_bad@example.com",
            "password": "testpass123",
            "dni": "77814916",
            "dni_digito_verificador": "0",
            "fecha_nacimiento": date(2000, 1, 1),
        }
    )

    assert not serializer.is_valid()
    assert "dni_digito_verificador" in serializer.errors
    assert "debe ser" not in str(serializer.errors).lower()


@pytest.mark.django_db
def test_limites_bajar_es_inmediato_y_subir_queda_pendiente():
    user = User.objects.create_user(username="limites_user", password="testpass123")
    perfil = PerfilUsuario.objects.create(
        user=user,
        dni="12345678",
        dni_digito_verificador=calcular_digito_verificador_tarjeta("12345678"),
        fecha_nacimiento=date(2000, 1, 1),
        status=EstadoCuenta.VERIFICADO,
        limite_deposito_diario=Decimal("500.0000"),
        limite_deposito_semanal=Decimal("2000.0000"),
        limite_deposito_mensual=Decimal("5000.0000"),
    )

    users_services.actualizar_limites(
        perfil,
        {
            "diario": Decimal("300.0000"),
            "semanal": Decimal("2500.0000"),
            "mensual": Decimal("6000.0000"),
        },
    )

    perfil.refresh_from_db()
    assert perfil.limite_deposito_diario == Decimal("300.0000")
    assert perfil.limite_deposito_diario_pendiente is None
    assert perfil.limite_deposito_semanal == Decimal("2000.0000")
    assert perfil.limite_deposito_semanal_pendiente == Decimal("2500.0000")
    assert perfil.limite_deposito_mensual == Decimal("5000.0000")
    assert perfil.limite_deposito_mensual_pendiente == Decimal("6000.0000")


@pytest.mark.django_db
def test_recarga_aplica_limites_semanal_y_mensual_pendientes_vencidos():
    user = User.objects.create_user(username="limites_apply", password="testpass123")
    perfil = PerfilUsuario.objects.create(
        user=user,
        dni="87654321",
        dni_digito_verificador=calcular_digito_verificador_tarjeta("87654321"),
        fecha_nacimiento=date(2000, 1, 1),
        status=EstadoCuenta.VERIFICADO,
        limite_deposito_diario=Decimal("10000.0000"),
        limite_deposito_semanal=Decimal("100.0000"),
        limite_deposito_mensual=Decimal("100.0000"),
        limite_deposito_semanal_pendiente=Decimal("1000.0000"),
        limite_deposito_mensual_pendiente=Decimal("1000.0000"),
        limite_semanal_efectivo_desde=timezone.now() - timezone.timedelta(minutes=1),
        limite_mensual_efectivo_desde=timezone.now() - timezone.timedelta(minutes=1),
    )

    wallet_services.recarga_simulada(user, Decimal("150.0000"))

    perfil.refresh_from_db()
    assert perfil.limite_deposito_semanal == Decimal("1000.0000")
    assert perfil.limite_deposito_mensual == Decimal("1000.0000")
    assert perfil.limite_deposito_semanal_pendiente is None
    assert perfil.limite_deposito_mensual_pendiente is None
