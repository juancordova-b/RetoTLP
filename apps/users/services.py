from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.users.models import EstadoCuenta, PerfilUsuario


class ErrorPerfil(Exception):
    pass


def autoexcluir(perfil: PerfilUsuario, dias: int | None = None, indefinido: bool = False) -> PerfilUsuario:
    """
    Autoexclusión: 7, 30, 90 días o indefinida.
    El usuario no puede revertirla antes del plazo por API.
    """
    if perfil.status == EstadoCuenta.BLOQUEADO:
        raise ErrorPerfil("Cuenta bloqueada por el operador.")

    perfil.status = EstadoCuenta.AUTOEXCLUIDO
    if indefinido:
        perfil.autoexclusion_hasta = None
    else:
        if dias not in (7, 30, 90):
            raise ErrorPerfil("Días válidos: 7, 30 o 90 (o indefinido=true).")
        perfil.autoexclusion_hasta = timezone.now() + timedelta(days=dias)

    perfil.save(update_fields=["status", "autoexclusion_hasta", "actualizado_en"])
    return perfil


def actualizar_limite_diario(perfil: PerfilUsuario, nuevo_limite: Decimal) -> PerfilUsuario:
    """
    Bajar límite: inmediato. Subir límite: pendiente 24 h (cooldown del enunciado).
    """
    return actualizar_limite(perfil, "diario", nuevo_limite)


def actualizar_limite(perfil: PerfilUsuario, periodo: str, nuevo_limite: Decimal) -> PerfilUsuario:
    """Actualiza límite diario/semanal/mensual con reducción inmediata y aumento en 24 h."""
    nuevo_limite = Decimal(str(nuevo_limite)).quantize(Decimal("0.0001"))
    if nuevo_limite <= 0:
        raise ErrorPerfil("El límite debe ser mayor a cero.")

    campos = {
        "diario": (
            "limite_deposito_diario",
            "limite_deposito_diario_pendiente",
            "limite_efectivo_desde",
            perfil.limite_diario_vigente,
        ),
        "semanal": (
            "limite_deposito_semanal",
            "limite_deposito_semanal_pendiente",
            "limite_semanal_efectivo_desde",
            perfil.limite_semanal_vigente,
        ),
        "mensual": (
            "limite_deposito_mensual",
            "limite_deposito_mensual_pendiente",
            "limite_mensual_efectivo_desde",
            perfil.limite_mensual_vigente,
        ),
    }
    if periodo not in campos:
        raise ErrorPerfil("Periodo inválido.")

    campo_base, campo_pendiente, campo_fecha, actual = campos[periodo]

    if nuevo_limite <= actual:
        setattr(perfil, campo_base, nuevo_limite)
        setattr(perfil, campo_pendiente, None)
        setattr(perfil, campo_fecha, None)
        perfil.save(update_fields=[campo_base, campo_pendiente, campo_fecha, "actualizado_en"])
        return perfil

    setattr(perfil, campo_pendiente, nuevo_limite)
    setattr(perfil, campo_fecha, timezone.now() + timedelta(hours=24))
    perfil.save(update_fields=[campo_pendiente, campo_fecha, "actualizado_en"])
    return perfil


def actualizar_limites(perfil: PerfilUsuario, limites: dict[str, Decimal]) -> PerfilUsuario:
    for periodo, nuevo_limite in limites.items():
        actualizar_limite(perfil, periodo, nuevo_limite)
        perfil.refresh_from_db()
    return perfil
