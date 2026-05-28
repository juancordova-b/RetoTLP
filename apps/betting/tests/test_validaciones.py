"""Validaciones de apuestas, re-cotización y reglas de negocio."""
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.betting.models import (
    ApuestaCombinada,
    EstadoApuesta,
    EstadoEvento,
    EventoDeportivo,
    Mercado,
    SeleccionMercado,
    TipoMercado,
)
from apps.betting.services import (
    ErrorApuesta,
    RequoteRequired,
    colocar_apuesta_combinada,
    colocar_apuesta_simple,
    liquidar_evento,
    mercados_sin_ganador_para_liquidacion,
    recalcular_cuotas_inplay,
    registrar_evento_critico_inplay,
    registrar_gol_evento,
    validar_piernas_combinada,
)
from apps.users.models import EstadoCuenta, PerfilUsuario

User = get_user_model()


@pytest.mark.django_db
def test_requote_exige_reconfirmacion(escenario_partido):
    ctx = escenario_partido
    with pytest.raises(RequoteRequired):
        colocar_apuesta_simple(
            ctx["user"],
            ctx["evento"],
            ctx["sel_local"],
            Decimal("10.0000"),
            odds_esperada=Decimal("1.50"),
            confirmar_requote=False,
        )


@pytest.mark.django_db
def test_requote_con_confirmacion_apuesta(escenario_partido):
    ctx = escenario_partido
    apuesta = colocar_apuesta_simple(
        ctx["user"],
        ctx["evento"],
        ctx["sel_local"],
        Decimal("10.0000"),
        odds_esperada=Decimal("2.10"),
        confirmar_requote=True,
    )
    assert apuesta.status == EstadoApuesta.ACEPTADA


@pytest.mark.django_db
def test_autoexcluido_no_apuesta(escenario_partido):
    ctx = escenario_partido
    perfil = ctx["user"].perfil
    perfil.status = EstadoCuenta.AUTOEXCLUIDO
    perfil.save()
    with pytest.raises(ErrorApuesta, match="autoexcluida"):
        colocar_apuesta_simple(
            ctx["user"], ctx["evento"], ctx["sel_local"], Decimal("5.0000")
        )


@pytest.mark.django_db
def test_evento_finalizado_no_apuesta(escenario_partido):
    ctx = escenario_partido
    ctx["evento"].status = EstadoEvento.FINALIZADO
    ctx["evento"].save()
    with pytest.raises(ErrorApuesta, match="no acepta apuestas"):
        colocar_apuesta_simple(
            ctx["user"], ctx["evento"], ctx["sel_local"], Decimal("5.0000")
        )


@pytest.mark.django_db
def test_stake_fuera_de_limites(escenario_partido):
    ctx = escenario_partido
    with pytest.raises(ErrorApuesta, match="Monto fuera"):
        colocar_apuesta_simple(
            ctx["user"], ctx["evento"], ctx["sel_local"], Decimal("0.5000")
        )


@pytest.mark.django_db
def test_mercados_sin_ganador_detecta_ou(escenario_partido):
    ctx = escenario_partido
    m_ou = Mercado.objects.create(
        evento=ctx["evento"], nombre="Más/Menos 2.5", tipo=TipoMercado.OVER_UNDER_25
    )
    s_menos = SeleccionMercado.objects.create(
        mercado=m_ou, etiqueta="Menos 2.5", codigo="U", odds=Decimal("1.85")
    )
    colocar_apuesta_simple(ctx["user"], ctx["evento"], s_menos, Decimal("10.0000"))

    ctx["evento"].status = EstadoEvento.FINALIZADO
    ctx["evento"].save()

    pendientes = mercados_sin_ganador_para_liquidacion(ctx["evento"])
    assert len(pendientes) == 1
    assert pendientes[0].id == m_ou.id


@pytest.mark.django_db
def test_liquidar_falla_si_faltan_ganadores_mercado(escenario_partido):
    ctx = escenario_partido
    m_ou = Mercado.objects.create(
        evento=ctx["evento"], nombre="Más/Menos 2.5", tipo=TipoMercado.OVER_UNDER_25
    )
    s_menos = SeleccionMercado.objects.create(
        mercado=m_ou, etiqueta="Menos 2.5", codigo="U", odds=Decimal("1.85")
    )
    colocar_apuesta_simple(ctx["user"], ctx["evento"], s_menos, Decimal("10.0000"))
    ctx["evento"].status = EstadoEvento.FINALIZADO
    ctx["evento"].save()

    with pytest.raises(ErrorApuesta, match="Faltan ganadores"):
        liquidar_evento(ctx["evento"])


@pytest.mark.django_db
def test_combinada_pierde_si_una_pierna_falla(escenario_partido):
    ctx = escenario_partido
    ev2 = EventoDeportivo.objects.create(
        nombre="Colombia vs Ecuador",
        equipo_local="Colombia",
        equipo_visitante="Ecuador",
        inicio_programado=timezone.now(),
        status=EstadoEvento.PROGRAMADO,
    )
    m2 = Mercado.objects.create(evento=ev2, nombre="1X2", tipo=TipoMercado.RESULTADO_1X2)
    s2 = SeleccionMercado.objects.create(
        mercado=m2, etiqueta="Gana Colombia", codigo="1", odds=Decimal("2.00")
    )
    SeleccionMercado.objects.create(
        mercado=m2, etiqueta="Gana Ecuador", codigo="2", odds=Decimal("3.00")
    )

    comb = colocar_apuesta_combinada(
        ctx["user"], [ctx["sel_local"].id, s2.id], Decimal("15.0000")
    )

    ctx["evento"].seleccion_ganadora = ctx["sel_local"]
    ctx["evento"].status = EstadoEvento.FINALIZADO
    ctx["evento"].save()

    ev2.seleccion_ganadora = SeleccionMercado.objects.get(mercado=m2, codigo="2")
    ev2.status = EstadoEvento.FINALIZADO
    ev2.save()

    liquidar_evento(ctx["evento"])
    liquidar_evento(ev2)

    comb.refresh_from_db()
    assert comb.status == EstadoApuesta.PERDIDA


@pytest.mark.django_db
@patch("apps.betting.services.broadcast_odds_evento")
def test_actualizar_cuota_notifica(mock_broadcast, escenario_partido):
    from apps.betting.services import actualizar_cuota_seleccion

    ctx = escenario_partido
    sel = actualizar_cuota_seleccion(ctx["sel_local"].id, Decimal("2.55"))
    assert sel.odds == Decimal("2.55")
    mock_broadcast.assert_called_once()


@pytest.mark.django_db
@patch("apps.betting.tasks.reactivar_mercado.apply_async")
@patch("apps.betting.services.broadcast_odds_evento")
def test_registrar_gol_local_actualiza_marcador_y_suspende(
    mock_broadcast, mock_reactivar, escenario_partido
):
    ctx = escenario_partido

    evento = registrar_gol_evento(ctx["evento"].id, "local", segundos=5)

    ctx["mercado"].refresh_from_db()
    assert evento.status == EstadoEvento.EN_VIVO
    assert evento.goles_local == 1
    assert evento.goles_visitante == 0
    assert evento.marcador == "Perú 1 - 0 Chile"
    assert ctx["mercado"].suspendido_hasta is not None
    ctx["sel_local"].refresh_from_db()
    ctx["sel_empate"].refresh_from_db()
    ctx["sel_visit"].refresh_from_db()
    assert ctx["sel_local"].odds == Decimal("1.50")
    assert ctx["sel_empate"].odds == Decimal("3.85")
    assert ctx["sel_visit"].odds == Decimal("5.20")
    mock_reactivar.assert_called_once_with(args=[ctx["mercado"].id], countdown=5)
    assert mock_broadcast.call_count == 5


@pytest.mark.django_db
@patch("apps.betting.tasks.reactivar_mercado.apply_async")
@patch("apps.betting.services.broadcast_odds_evento")
def test_registrar_gol_visitante_actualiza_marcador(
    mock_broadcast, mock_reactivar, escenario_partido
):
    evento = registrar_gol_evento(escenario_partido["evento"].id, "visitante", segundos=5)

    assert evento.goles_local == 0
    assert evento.goles_visitante == 1
    assert evento.marcador == "Perú 0 - 1 Chile"
    assert mock_broadcast.call_args.args[1]["equipo_gol"] == "Chile"
    assert mock_broadcast.call_args.args[1]["cuotas_actualizadas"] == 3
    mock_reactivar.assert_called_once()


@pytest.mark.django_db
def test_recalcular_cuotas_inplay_sin_goles_no_cambia(escenario_partido):
    assert recalcular_cuotas_inplay(escenario_partido["evento"]) == []


@pytest.mark.django_db
@patch("apps.betting.tasks.reactivar_mercado.apply_async")
@patch("apps.betting.services.broadcast_odds_evento")
def test_goles_recalculan_cuotas_ou_y_btts(mock_broadcast, mock_reactivar, escenario_partido):
    ctx = escenario_partido
    m_ou = Mercado.objects.create(
        evento=ctx["evento"], nombre="Más/Menos 2.5", tipo=TipoMercado.OVER_UNDER_25
    )
    over = SeleccionMercado.objects.create(
        mercado=m_ou, etiqueta="Más de 2.5", codigo="OVER", odds=Decimal("1.85")
    )
    under = SeleccionMercado.objects.create(
        mercado=m_ou, etiqueta="Menos de 2.5", codigo="UNDER", odds=Decimal("1.95")
    )
    m_btts = Mercado.objects.create(
        evento=ctx["evento"], nombre="Ambos anotan", tipo=TipoMercado.BTTS
    )
    si = SeleccionMercado.objects.create(
        mercado=m_btts, etiqueta="Sí", codigo="SI", odds=Decimal("1.75")
    )
    no = SeleccionMercado.objects.create(
        mercado=m_btts, etiqueta="No", codigo="NO", odds=Decimal("2.05")
    )

    registrar_gol_evento(ctx["evento"].id, "local", segundos=5)
    over.refresh_from_db()
    under.refresh_from_db()
    si.refresh_from_db()
    no.refresh_from_db()
    assert over.odds == Decimal("1.75")
    assert under.odds == Decimal("2.05")
    assert si.odds == Decimal("1.55")
    assert no.odds == Decimal("2.40")

    registrar_gol_evento(ctx["evento"].id, "visitante", segundos=5)
    over.refresh_from_db()
    under.refresh_from_db()
    si.refresh_from_db()
    no.refresh_from_db()
    assert over.odds == Decimal("1.35")
    assert under.odds == Decimal("3.20")
    assert si.odds == Decimal("1.05")
    assert no.odds == Decimal("12.00")

    registrar_gol_evento(ctx["evento"].id, "local", segundos=5)
    over.refresh_from_db()
    under.refresh_from_db()
    assert over.odds == Decimal("1.05")
    assert under.odds == Decimal("12.00")
    assert mock_reactivar.call_count == 3
    assert mock_broadcast.called


@pytest.mark.django_db
def test_registrar_gol_rechaza_lado_invalido(escenario_partido):
    with pytest.raises(ErrorApuesta, match="Lado inválido"):
        registrar_gol_evento(escenario_partido["evento"].id, "neutral")


@pytest.mark.django_db
def test_registrar_gol_rechaza_evento_finalizado(escenario_partido):
    evento = escenario_partido["evento"]
    evento.status = EstadoEvento.FINALIZADO
    evento.save()

    with pytest.raises(ErrorApuesta, match="finalizado o anulado"):
        registrar_gol_evento(evento.id, "local")


@pytest.mark.django_db
@patch("apps.betting.tasks.reactivar_mercado.apply_async")
@patch("apps.betting.services.broadcast_odds_evento")
def test_registrar_evento_critico_suspende_mercado(
    mock_broadcast, mock_reactivar, escenario_partido
):
    ctx = escenario_partido

    evento = registrar_evento_critico_inplay(
        ctx["evento"].id, descripcion="Expulsión simulada", segundos=5
    )

    ctx["mercado"].refresh_from_db()
    assert evento.status == EstadoEvento.EN_VIVO
    assert ctx["mercado"].suspendido_hasta is not None
    mock_reactivar.assert_called_once_with(args=[ctx["mercado"].id], countdown=5)
    assert mock_broadcast.call_args.args[1]["tipo"] == "evento_critico"
    assert mock_broadcast.call_args.args[1]["descripcion"] == "Expulsión simulada"


@pytest.mark.django_db
def test_validar_piernas_rechaza_una_sola(escenario_partido):
    with pytest.raises(ErrorApuesta, match="al menos 2"):
        validar_piernas_combinada([escenario_partido["sel_local"]])
