"""
Lógica del wallet con partida doble.
Cada operación crea al menos 2 LedgerEntry balanceadas.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from apps.users.models import AccountStatus
from apps.wallet.models import EntryDirection, LedgerAccount, LedgerEntry, LedgerTransaction

User = get_user_model()


class WalletError(Exception):
    pass


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0001"))


def calcular_saldo(user, account: str = LedgerAccount.WALLET_USUARIO) -> Decimal:
    """
    Saldo = SUM(créditos) - SUM(débitos). Nunca leer de una columna 'saldo'.
    """
    agg = LedgerEntry.objects.filter(user=user, account=account).aggregate(
        creditos=Sum("amount", filter=Q(direction=EntryDirection.CREDIT)),
        debitos=Sum("amount", filter=Q(direction=EntryDirection.DEBIT)),
    )
    creditos = agg["creditos"] or Decimal("0")
    debitos = agg["debitos"] or Decimal("0")
    return _money(creditos - debitos)


def _deposito_hoy(user) -> Decimal:
    hoy = timezone.localdate()
    total = LedgerEntry.objects.filter(
        user=user,
        account=LedgerAccount.WALLET_USUARIO,
        direction=EntryDirection.CREDIT,
        transaction__tipo="deposito_simulado",
        creado_en__date=hoy,
    ).aggregate(s=Sum("amount"))["s"]
    return _money(total or 0)


@transaction.atomic
def recarga_simulada(
    user,
    monto: Decimal,
    idempotency_key: str | None = None,
) -> LedgerTransaction:
    """
    Usuario recibe fichas desde la casa.
    CREDIT wallet_usuario / DEBIT casa (misma cantidad).
    """
    monto = _money(monto)
    if monto <= 0:
        raise WalletError("El monto debe ser mayor a cero.")

    if idempotency_key and LedgerTransaction.objects.filter(idempotency_key=idempotency_key).exists():
        return LedgerTransaction.objects.get(idempotency_key=idempotency_key)

    profile = user.profile
    if profile.status == AccountStatus.AUTOEXCLUIDO:
        raise WalletError("Cuenta autoexcluida: no puede recargar fichas.")
    if profile.status != AccountStatus.VERIFICADO:
        raise WalletError("Cuenta no verificada: completa el KYC simulado primero.")

    if _deposito_hoy(user) + monto > profile.limite_deposito_diario:
        raise WalletError(
            f"Superas tu límite diario de recarga ({profile.limite_deposito_diario} fichas)."
        )

    User.objects.select_for_update().get(pk=user.pk)

    tx = LedgerTransaction.objects.create(
        tipo="deposito_simulado",
        referencia=f"user:{user.id}",
        idempotency_key=idempotency_key,
    )
    LedgerEntry.objects.bulk_create(
        [
            LedgerEntry(
                transaction=tx,
                user=user,
                account=LedgerAccount.WALLET_USUARIO,
                amount=monto,
                direction=EntryDirection.CREDIT,
            ),
            LedgerEntry(
                transaction=tx,
                user=None,
                account=LedgerAccount.CASA,
                amount=monto,
                direction=EntryDirection.DEBIT,
            ),
        ]
    )
    return tx


@transaction.atomic
def bloquear_fondos_apuesta(
    user,
    monto: Decimal,
    bet_id: str,
    idempotency_key: str | None = None,
) -> LedgerTransaction:
    """
    Al confirmar apuesta: fondos pasan de wallet a apuestas_pendientes.
    DEBIT wallet / CREDIT apuestas_pendientes.
    """
    monto = _money(monto)
    if idempotency_key and LedgerTransaction.objects.filter(idempotency_key=idempotency_key).exists():
        return LedgerTransaction.objects.get(idempotency_key=idempotency_key)

    saldo = calcular_saldo(user)
    if saldo < monto:
        raise WalletError(f"Saldo insuficiente. Disponible: {saldo}, requerido: {monto}.")

    User.objects.select_for_update().get(pk=user.pk)

    tx = LedgerTransaction.objects.create(
        tipo="bloqueo_apuesta",
        referencia=f"bet:{bet_id}",
        idempotency_key=idempotency_key,
    )
    LedgerEntry.objects.bulk_create(
        [
            LedgerEntry(
                transaction=tx,
                user=user,
                account=LedgerAccount.WALLET_USUARIO,
                amount=monto,
                direction=EntryDirection.DEBIT,
            ),
            LedgerEntry(
                transaction=tx,
                user=user,
                account=LedgerAccount.APUESTAS_PENDIENTES,
                amount=monto,
                direction=EntryDirection.CREDIT,
            ),
        ]
    )
    return tx


def verificar_transaccion_balanceada(tx: LedgerTransaction) -> bool:
    """True si débitos == créditos en la transacción."""
    agg = tx.entries.aggregate(
        deb=Sum("amount", filter=Q(direction=EntryDirection.DEBIT)),
        cred=Sum("amount", filter=Q(direction=EntryDirection.CREDIT)),
    )
    return (agg["deb"] or Decimal("0")) == (agg["cred"] or Decimal("0"))
