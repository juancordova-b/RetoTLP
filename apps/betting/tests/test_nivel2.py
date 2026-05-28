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
from apps.betting.services import (
    ErrorApuesta,
    calcular_cashout,
    colocar_apuesta_combinada,
    colocar_apuesta_simple,
    ejecutar_cashout_apuesta,
)
from apps.users.models import EstadoCuenta, PerfilUsuario
from apps.wallet import services

User = get_user_model()


@pytest.fixture
def usuario(db):
    user = User.objects.create_user(username="n2user", password="pass12345")
    PerfilUsuario.objects.create(
        user=user,
        dni="99887766",
        fecha_nacimiento="1998-06-01",
        status=EstadoCuenta.VERIFICADO,
    )
    services.recarga_simulada(user, Decimal("500.0000"))
    return user


@pytest.fixture
def dos_partidos(db):
    from django.utils import timezone

    eventos = []
    for nombre, l, v in [("A vs B", "A", "B"), ("C vs D", "C", "D")]:
        ev = EventoDeportivo.objects.create(
            nombre=nombre,
            equipo_local=l,
            equipo_visitante=v,
            inicio_programado=timezone.now(),
            status=EstadoEvento.PROGRAMADO,
        )
        m = Mercado.objects.create(evento=ev, nombre="1X2", tipo=TipoMercado.RESULTADO_1X2)
        s1 = SeleccionMercado.objects.create(mercado=m, etiqueta=f"Gana {l}", codigo="1", odds=Decimal("2.00"))
        SeleccionMercado.objects.create(mercado=m, etiqueta="Empate", codigo="X", odds=Decimal("3.00"))
        eventos.append((ev, s1))
    return eventos


@pytest.mark.django_db
def test_apuesta_combinada_cuota_producto(usuario, dos_partidos):
    (ev1, s1), (ev2, s2) = dos_partidos
    comb = colocar_apuesta_combinada(usuario, [s1.id, s2.id], Decimal("20.0000"))
    assert comb.odds_locked == Decimal("4.0000")
    assert comb.piernas.count() == 2


@pytest.mark.django_db
def test_combinada_rechaza_mismo_mercado(usuario, dos_partidos):
    (ev1, s1), _ = dos_partidos
    m = ev1.mercados.first()
    s_empate = SeleccionMercado.objects.get(mercado=m, codigo="X")
    with pytest.raises(ErrorApuesta):
        colocar_apuesta_combinada(usuario, [s1.id, s_empate.id], Decimal("10.0000"))


@pytest.mark.django_db
def test_combinada_mismo_partido_distintos_mercados(usuario, dos_partidos):
    (ev1, s1), _ = dos_partidos
    m_ou = Mercado.objects.create(
        evento=ev1, nombre="Más/Menos 2.5", tipo=TipoMercado.OVER_UNDER_25
    )
    s_menos = SeleccionMercado.objects.create(
        mercado=m_ou, etiqueta="Menos 2.5", codigo="U", odds=Decimal("1.80")
    )
    comb = colocar_apuesta_combinada(usuario, [s1.id, s_menos.id], Decimal("10.0000"))
    assert comb.odds_locked == Decimal("3.6000")
    assert comb.piernas.count() == 2
    assert comb.piernas.filter(evento=ev1).count() == 2


@pytest.mark.django_db
def test_cashout(usuario, dos_partidos):
    ev, sel = dos_partidos[0]
    apuesta = colocar_apuesta_simple(usuario, ev, sel, Decimal("50.0000"))
    monto = calcular_cashout(apuesta)
    assert monto > 0
    ejecutar_cashout_apuesta(apuesta)
    apuesta.refresh_from_db()
    assert apuesta.status == EstadoApuesta.CASHOUT
