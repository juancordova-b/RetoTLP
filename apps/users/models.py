from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.users.validators import validar_dni_peruano


class EstadoCuenta(models.TextChoices):
    PENDIENTE_VERIFICACION = "pendiente_verificacion", "Pendiente de verificación"
    VERIFICADO = "verificado", "Verificado"
    BLOQUEADO = "bloqueado", "Bloqueado"
    AUTOEXCLUIDO = "autoexcluido", "Autoexcluido"


class PerfilUsuario(models.Model):
    """
    Datos extra del usuario: KYC simulado, DNI, juego responsable básico.
    Se conecta 1-a-1 con auth.User de Django.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    dni = models.CharField(max_length=8, unique=True)
    dni_digito_verificador = models.CharField(
        max_length=1,
        verbose_name="dígito verificador DNI",
        help_text="Dígito verificador calculado sobre los 8 dígitos del DNI.",
    )
    fecha_nacimiento = models.DateField()
    status = models.CharField(
        max_length=32,
        choices=EstadoCuenta.choices,
        default=EstadoCuenta.PENDIENTE_VERIFICACION,
        verbose_name="estado",
    )
    limite_deposito_diario = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=500,
        help_text="Máximo de fichas que puede recargar por día",
    )
    limite_deposito_semanal = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=2000,
        help_text="Máximo de fichas que puede recargar por semana",
    )
    limite_deposito_mensual = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=5000,
        help_text="Máximo de fichas que puede recargar por mes",
    )
    limite_deposito_diario_pendiente = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Nuevo límite diario que aplica tras 24 h si es mayor al actual",
    )
    limite_deposito_semanal_pendiente = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Nuevo límite semanal que aplica tras 24 h si es mayor al actual",
    )
    limite_deposito_mensual_pendiente = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Nuevo límite mensual que aplica tras 24 h si es mayor al actual",
    )
    limite_efectivo_desde = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que entra en vigor el límite diario pendiente",
    )
    limite_semanal_efectivo_desde = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que entra en vigor el límite semanal pendiente",
    )
    limite_mensual_efectivo_desde = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que entra en vigor el límite mensual pendiente",
    )
    autoexclusion_hasta = models.DateTimeField(null=True, blank=True)
    bono_bienvenida_activo = models.BooleanField(
        default=False,
        help_text="True cuando existe un bono de bienvenida con rollover pendiente.",
    )
    bono_bienvenida_monto = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
    )
    rollover_objetivo = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
        help_text="Monto total que debe apostarse antes de permitir retiro.",
    )
    rollover_acumulado = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
    )
    bono_bienvenida_asignado_en = models.DateTimeField(null=True, blank=True)
    bono_bienvenida_liberado_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"{self.user.username} ({self.status})"

    def clean(self):
        super().clean()
        if self.dni and self.dni_digito_verificador and not validar_dni_peruano(
            self.dni, self.dni_digito_verificador
        ):
            raise ValidationError(
                {
                    "dni_digito_verificador": (
                        "Dígito verificador incorrecto. Revísalo en tu documento de identidad."
                    )
                }
            )

    def renovar_autoexclusion_si_expiró(self) -> None:
        """Si el plazo terminó, vuelve a verificado (no puede revertir antes por API)."""
        if (
            self.status == EstadoCuenta.AUTOEXCLUIDO
            and self.autoexclusion_hasta
            and timezone.now() >= self.autoexclusion_hasta
        ):
            self.status = EstadoCuenta.VERIFICADO
            self.autoexclusion_hasta = None
            self.save(update_fields=["status", "autoexclusion_hasta", "actualizado_en"])

    @property
    def esta_autoexcluido(self) -> bool:
        self.renovar_autoexclusion_si_expiró()
        if self.status != EstadoCuenta.AUTOEXCLUIDO:
            return False
        if self.autoexclusion_hasta is None:
            return True
        return timezone.now() < self.autoexclusion_hasta

    @property
    def limite_diario_vigente(self):
        """Límite diario efectivo (aplica pendiente tras 24 h si corresponde)."""
        if (
            self.limite_deposito_diario_pendiente is not None
            and self.limite_efectivo_desde
            and timezone.now() >= self.limite_efectivo_desde
        ):
            return self.limite_deposito_diario_pendiente
        return self.limite_deposito_diario

    @property
    def limite_semanal_vigente(self):
        """Límite semanal efectivo (aplica pendiente tras 24 h si corresponde)."""
        if (
            self.limite_deposito_semanal_pendiente is not None
            and self.limite_semanal_efectivo_desde
            and timezone.now() >= self.limite_semanal_efectivo_desde
        ):
            return self.limite_deposito_semanal_pendiente
        return self.limite_deposito_semanal

    @property
    def limite_mensual_vigente(self):
        """Límite mensual efectivo (aplica pendiente tras 24 h si corresponde)."""
        if (
            self.limite_deposito_mensual_pendiente is not None
            and self.limite_mensual_efectivo_desde
            and timezone.now() >= self.limite_mensual_efectivo_desde
        ):
            return self.limite_deposito_mensual_pendiente
        return self.limite_deposito_mensual

    @property
    def puede_apostar(self) -> bool:
        return self.status == EstadoCuenta.VERIFICADO and not self.esta_autoexcluido

    @property
    def puede_recargar(self) -> bool:
        return self.status == EstadoCuenta.VERIFICADO and not self.esta_autoexcluido

    @property
    def rollover_pendiente(self):
        pendiente = self.rollover_objetivo - self.rollover_acumulado
        return pendiente if pendiente > 0 else Decimal("0.0000")
