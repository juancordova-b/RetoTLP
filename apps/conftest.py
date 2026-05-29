"""Fixtures compartidas para tests de wallet y betting."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.betting.models import EventoDeportivo, EstadoEvento, Mercado, SeleccionMercado, TipoMercado
from apps.users.models import EstadoCuenta, PerfilUsuario
from apps.wallet import services as wallet_services

User = get_user_model()


@pytest.fixture
def usuario_verificado(db):
    user = User.objects.create_user(username="testuser", password="testpass123")
    PerfilUsuario.objects.create(
        user=user,
        dni="12345671",
        fecha_nacimiento="2000-05-15",
        status=EstadoCuenta.VERIFICADO,
        limite_deposito_diario=Decimal("5000.0000"),
        limite_deposito_semanal=Decimal("10000.0000"),
        limite_deposito_mensual=Decimal("20000.0000"),
    )
    return user


@pytest.fixture
def usuario_con_token(usuario_verificado):
    token, _ = Token.objects.get_or_create(user=usuario_verificado)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client, usuario_verificado


@pytest.fixture
def escenario_partido(db, usuario_verificado):
    wallet_services.recarga_simulada(usuario_verificado, Decimal("500.0000"))
    evento = EventoDeportivo.objects.create(
        nombre="Perú vs Chile",
        equipo_local="Perú",
        equipo_visitante="Chile",
        inicio_programado=timezone.now(),
        status=EstadoEvento.PROGRAMADO,
    )
    mercado = Mercado.objects.create(
        evento=evento, nombre="1X2", tipo=TipoMercado.RESULTADO_1X2
    )
    sel_local = SeleccionMercado.objects.create(
        mercado=mercado, etiqueta="Gana Perú", codigo="1", odds=Decimal("2.10")
    )
    sel_empate = SeleccionMercado.objects.create(
        mercado=mercado, etiqueta="Empate", codigo="X", odds=Decimal("3.20")
    )
    sel_visit = SeleccionMercado.objects.create(
        mercado=mercado, etiqueta="Gana Chile", codigo="2", odds=Decimal("3.50")
    )
    return {
        "user": usuario_verificado,
        "evento": evento,
        "mercado": mercado,
        "sel_local": sel_local,
        "sel_empate": sel_empate,
        "sel_visit": sel_visit,
    }
