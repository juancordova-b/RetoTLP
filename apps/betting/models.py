import uuid

from django.conf import settings
from django.db import models


class EstadoEvento(models.TextChoices):
    PROGRAMADO = "programado", "Programado"
    EN_VIVO = "en_vivo", "En vivo"
    FINALIZADO = "finalizado", "Finalizado"
    SUSPENDIDO = "suspendido", "Suspendido"
    ANULADO = "anulado", "Anulado"


class EstadoApuesta(models.TextChoices):
    ACEPTADA = "aceptada", "Aceptada"
    GANADA = "ganada", "Ganada"
    PERDIDA = "perdida", "Perdida"
    ANULADA = "anulada", "Anulada"
    CASHOUT = "cashout", "Cash-out"


class TipoMercado(models.TextChoices):
    RESULTADO_1X2 = "1X2", "Resultado 1X2"
    OVER_UNDER_25 = "OU25", "Más/Menos 2.5 goles"
    BTTS = "BTTS", "Ambos anotan"
    HANDICAP_ASIATICO = "AH", "Hándicap asiático"


class EventoDeportivo(models.Model):
    """Partido o evento deportivo."""

    nombre = models.CharField(max_length=200)
    deporte = models.CharField(max_length=64, default="futbol")
    equipo_local = models.CharField(max_length=120)
    equipo_visitante = models.CharField(max_length=120)
    goles_local = models.PositiveSmallIntegerField(default=0)
    goles_visitante = models.PositiveSmallIntegerField(default=0)
    inicio_programado = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=EstadoEvento.choices,
        default=EstadoEvento.PROGRAMADO,
        verbose_name="estado",
    )
    seleccion_ganadora = models.ForeignKey(
        "SeleccionMercado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_ganados",
        verbose_name="selección ganadora",
        help_text="Selección ganadora del mercado 1X2 (para liquidar apuestas).",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["inicio_programado"]
        verbose_name = "Evento deportivo"
        verbose_name_plural = "Eventos deportivos"

    def __str__(self):
        return f"{self.equipo_local} vs {self.equipo_visitante}"

    @property
    def marcador(self) -> str:
        return f"{self.equipo_local} {self.goles_local} - {self.goles_visitante} {self.equipo_visitante}"

    @property
    def acepta_apuestas(self) -> bool:
        return self.status in (EstadoEvento.PROGRAMADO, EstadoEvento.EN_VIVO)


class Mercado(models.Model):
    """Mercado de apuestas (ej. 1X2)."""

    evento = models.ForeignKey(
        EventoDeportivo, on_delete=models.CASCADE, related_name="mercados"
    )
    nombre = models.CharField(max_length=64)
    tipo = models.CharField(max_length=32, default=TipoMercado.RESULTADO_1X2)
    activo = models.BooleanField(default=True)
    suspendido_hasta = models.DateTimeField(
        null=True,
        blank=True,
        help_text="In-play: mercado pausado tras gol/expulsión hasta esta hora.",
    )
    seleccion_ganadora = models.ForeignKey(
        "SeleccionMercado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mercados_ganados",
        verbose_name="selección ganadora del mercado",
    )

    class Meta:
        verbose_name = "Mercado"
        verbose_name_plural = "Mercados"

    def __str__(self):
        return f"{self.evento} — {self.nombre}"

    @property
    def esta_disponible(self) -> bool:
        from django.utils import timezone

        if not self.activo:
            return False
        if self.suspendido_hasta and timezone.now() < self.suspendido_hasta:
            return False
        return True


class SeleccionMercado(models.Model):
    """Selección dentro del mercado (local, empate, visitante) con su cuota."""

    mercado = models.ForeignKey(
        Mercado, on_delete=models.CASCADE, related_name="selecciones"
    )
    etiqueta = models.CharField(max_length=64)
    codigo = models.CharField(max_length=16)
    odds = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="cuota")
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = [("mercado", "codigo")]
        verbose_name = "Selección de mercado"
        verbose_name_plural = "Selecciones de mercado"

    def __str__(self):
        return f"{self.etiqueta} @ {self.odds}"


class Apuesta(models.Model):
    """Apuesta simple del usuario (avance: solo estado aceptada)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="apuestas",
    )
    evento = models.ForeignKey(EventoDeportivo, on_delete=models.PROTECT)
    seleccion = models.ForeignKey(SeleccionMercado, on_delete=models.PROTECT)
    stake = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="monto")
    odds_locked = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="cuota bloqueada"
    )
    status = models.CharField(
        max_length=16,
        choices=EstadoApuesta.choices,
        default=EstadoApuesta.ACEPTADA,
        verbose_name="estado",
    )
    idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    transaccion_contable = models.ForeignKey(
        "wallet.TransaccionContable",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    cashout_monto = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True, verbose_name="monto cash-out"
    )
    cashout_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "Apuesta"
        verbose_name_plural = "Apuestas"

    @property
    def payout_potencial(self):
        from decimal import Decimal

        return (self.stake * self.odds_locked).quantize(Decimal("0.0001"))


class ApuestaCombinada(models.Model):
    """Acumuladora: varias piernas; cuota = producto de cuotas."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="apuestas_combinadas",
    )
    stake = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="monto")
    odds_locked = models.DecimalField(max_digits=12, decimal_places=4, verbose_name="cuota combinada")
    status = models.CharField(
        max_length=16,
        choices=EstadoApuesta.choices,
        default=EstadoApuesta.ACEPTADA,
        verbose_name="estado",
    )
    idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    transaccion_contable = models.ForeignKey(
        "wallet.TransaccionContable",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "Apuesta combinada"
        verbose_name_plural = "Apuestas combinadas"

    @property
    def payout_potencial(self):
        from decimal import Decimal

        return (self.stake * self.odds_locked).quantize(Decimal("0.0001"))


class PiernaCombinada(models.Model):
    combinada = models.ForeignKey(
        ApuestaCombinada, on_delete=models.CASCADE, related_name="piernas"
    )
    evento = models.ForeignKey(EventoDeportivo, on_delete=models.PROTECT)
    seleccion = models.ForeignKey(SeleccionMercado, on_delete=models.PROTECT)
    odds_locked = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Pierna combinada"
        verbose_name_plural = "Piernas combinadas"
        unique_together = [("combinada", "seleccion")]

