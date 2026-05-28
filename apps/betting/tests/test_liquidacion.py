from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.betting.models import (
    Apuesta,
    EstadoApuesta,
    EstadoEvento,
    EventoDeportivo,
    Mercado,
    SeleccionMercado,
    TipoMercado,
)
from apps.betting.services import colocar_apuesta_combinada, colocar_apuesta_simple, liquidar_evento
from apps.users.models import EstadoCuenta, PerfilUsuario
from apps.wallet import services

User = get_user_model()


@pytest.fixture
def escenario_partido(db):
    user = User.objects.create_user(username="apostador", password="pass12345")
    PerfilUsuario.objects.create(
        user=user,
        dni="87654321",
        fecha_nacimiento="1999-01-01",
        status=EstadoCuenta.VERIFICADO,
    )
    services.recarga_simulada(user, Decimal("200.0000"))

    from django.utils import timezone

    evento = EventoDeportivo.objects.create(
        nombre="A vs B",
        equipo_local="A",
        equipo_visitante="B",
        inicio_programado=timezone.now(),
        status=EstadoEvento.PROGRAMADO,
    )
    mercado = Mercado.objects.create(evento=evento, nombre="1X2", tipo="1X2")
    sel_local = SeleccionMercado.objects.create(
        mercado=mercado, etiqueta="Gana A", codigo="1", odds=Decimal("2.00")
    )
    SeleccionMercado.objects.create(
        mercado=mercado, etiqueta="Empate", codigo="X", odds=Decimal("3.00")
    )
    sel_visit = SeleccionMercado.objects.create(
        mercado=mercado, etiqueta="Gana B", codigo="2", odds=Decimal("4.00")
    )
    return user, evento, sel_local, sel_visit


@pytest.mark.django_db
def test_liquidacion_apuesta_ganada(escenario_partido):
    user, evento, sel_local, _ = escenario_partido
    apuesta = colocar_apuesta_simple(user, evento, sel_local, Decimal("50.0000"))
    assert services.calcular_saldo(user) == Decimal("150.0000")

    evento.seleccion_ganadora = sel_local
    evento.status = EstadoEvento.FINALIZADO
    evento.save()

    stats = liquidar_evento(evento)
    apuesta.refresh_from_db()

    assert stats["ganadas"] == 1
    assert apuesta.status == EstadoApuesta.GANADA
    assert services.calcular_saldo(user) == Decimal("250.0000")


@pytest.mark.django_db
def test_liquidacion_apuesta_perdida(escenario_partido):
    user, evento, sel_local, sel_visit = escenario_partido
    apuesta = colocar_apuesta_simple(user, evento, sel_local, Decimal("40.0000"))

    evento.seleccion_ganadora = sel_visit
    evento.status = EstadoEvento.FINALIZADO
    evento.save()

    stats = liquidar_evento(evento)
    apuesta.refresh_from_db()

    assert stats["perdidas"] == 1
    assert apuesta.status == EstadoApuesta.PERDIDA
    assert services.calcular_saldo(user) == Decimal("160.0000")


@pytest.mark.django_db
def test_liquidacion_mercado_ou(escenario_partido):
    user, evento, sel_local, _ = escenario_partido
    m_ou = Mercado.objects.create(
        evento=evento, nombre="Más/Menos 2.5", tipo=TipoMercado.OVER_UNDER_25
    )
    s_menos = SeleccionMercado.objects.create(
        mercado=m_ou, etiqueta="Menos 2.5", codigo="U", odds=Decimal("1.90")
    )
    SeleccionMercado.objects.create(
        mercado=m_ou, etiqueta="Más 2.5", codigo="O", odds=Decimal("1.90")
    )
    apuesta = colocar_apuesta_simple(user, evento, s_menos, Decimal("20.0000"))

    evento.status = EstadoEvento.FINALIZADO
    evento.save()
    m_ou.seleccion_ganadora = s_menos
    m_ou.save()

    stats = liquidar_evento(evento)
    apuesta.refresh_from_db()

    assert stats["ganadas"] == 1
    assert apuesta.status == EstadoApuesta.GANADA


@pytest.mark.django_db
def test_combinada_mismo_partido_liquida_con_ganadores_por_mercado(escenario_partido):
    user, evento, sel_local, _ = escenario_partido
    m_ou = Mercado.objects.create(
        evento=evento, nombre="Más/Menos 2.5", tipo=TipoMercado.OVER_UNDER_25
    )
    s_menos = SeleccionMercado.objects.create(
        mercado=m_ou, etiqueta="Menos 2.5", codigo="U", odds=Decimal("1.80")
    )
    comb = colocar_apuesta_combinada(user, [sel_local.id, s_menos.id], Decimal("10.0000"))

    evento.seleccion_ganadora = sel_local
    evento.status = EstadoEvento.FINALIZADO
    evento.save()
    m_ou.seleccion_ganadora = s_menos
    m_ou.save()

    stats = liquidar_evento(evento)
    comb.refresh_from_db()

    assert stats["combinadas"] >= 1
    assert comb.status == EstadoApuesta.GANADA


@pytest.fixture
def usuario_verificado(db):
    user = User.objects.create_user(username="retiro_user", password="testpass123")
    PerfilUsuario.objects.create(
        user=user,
        dni="11223344",
        fecha_nacimiento="2000-05-15",
        status=EstadoCuenta.VERIFICADO,
        limite_deposito_diario=Decimal("1000.0000"),
    )
    return user


@pytest.mark.django_db
def test_retiro_simulado(usuario_verificado):
    services.recarga_simulada(usuario_verificado, Decimal("100.0000"))
    services.retiro_simulado(usuario_verificado, Decimal("30.0000"))
    assert services.calcular_saldo(usuario_verificado) == Decimal("70.0000")
