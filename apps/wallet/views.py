from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.wallet import services
from apps.wallet.serializers import BonoBienvenidaSerializer, DepositoSerializer, TransferenciaSerializer


class VistaSaldo(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        saldo = services.calcular_saldo(request.user)
        perfil = request.user.perfil
        return Response(
            {
                "saldo_fichas": str(saldo),
                "cuenta": "cartera_usuario",
                "nota": "Saldo calculado desde el libro mayor (partida doble), no guardado en columna fija.",
                "bono": {
                    "activo": perfil.bono_bienvenida_activo,
                    "monto": str(perfil.bono_bienvenida_monto),
                    "rollover_objetivo": str(perfil.rollover_objetivo),
                    "rollover_acumulado": str(perfil.rollover_acumulado),
                    "rollover_pendiente": str(perfil.rollover_pendiente),
                },
            }
        )


class VistaDeposito(APIView):
    """Recarga simulada de fichas virtuales."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DepositoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data.get("idempotency_key") or None
        if key == "":
            key = None
        try:
            tx = services.recarga_simulada(
                request.user,
                serializer.validated_data["monto"],
                idempotency_key=key,
            )
        except services.ErrorWallet as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        saldo = services.calcular_saldo(request.user)
        return Response(
            {
                "mensaje": "Recarga simulada aplicada.",
                "transaction_id": str(tx.id),
                "saldo_fichas": str(saldo),
            },
            status=status.HTTP_201_CREATED,
        )


class VistaRetiro(APIView):
    """Retiro simulado de fichas virtuales."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DepositoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data.get("idempotency_key") or None
        if key == "":
            key = None
        try:
            tx = services.retiro_simulado(
                request.user,
                serializer.validated_data["monto"],
                idempotency_key=key,
            )
        except services.ErrorWallet as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        saldo = services.calcular_saldo(request.user)
        return Response(
            {
                "mensaje": "Retiro simulado aplicado.",
                "transaction_id": str(tx.id),
                "saldo_fichas": str(saldo),
            },
            status=status.HTTP_201_CREATED,
        )


class VistaTransferencia(APIView):
    """Envía soles virtuales a otro usuario verificado."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TransferenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data.get("idempotency_key") or None
        if key == "":
            key = None
        try:
            tx = services.transferencia_interna(
                request.user,
                serializer.validated_data["destino_username"],
                serializer.validated_data["monto"],
                idempotency_key=key,
            )
        except services.ErrorWallet as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        saldo = services.calcular_saldo(request.user)
        return Response(
            {
                "mensaje": f"Transferencia enviada a {serializer.validated_data['destino_username']}.",
                "transaction_id": str(tx.id),
                "saldo_fichas": str(saldo),
            },
            status=status.HTTP_201_CREATED,
        )


class VistaBonoBienvenida(APIView):
    """Activa bono de bienvenida con rollover."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        perfil = request.user.perfil
        return Response(
            {
                "activo": perfil.bono_bienvenida_activo,
                "monto": str(perfil.bono_bienvenida_monto),
                "rollover_objetivo": str(perfil.rollover_objetivo),
                "rollover_acumulado": str(perfil.rollover_acumulado),
                "rollover_pendiente": str(perfil.rollover_pendiente),
                "asignado_en": perfil.bono_bienvenida_asignado_en.isoformat()
                if perfil.bono_bienvenida_asignado_en
                else None,
                "liberado_en": perfil.bono_bienvenida_liberado_en.isoformat()
                if perfil.bono_bienvenida_liberado_en
                else None,
            }
        )

    def post(self, request):
        serializer = BonoBienvenidaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tx = services.activar_bono_bienvenida(
                request.user,
                idempotency_key=f"bonus-{request.user.id}",
            )
        except services.ErrorWallet as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        perfil = request.user.perfil
        return Response(
            {
                "mensaje": "Bono de bienvenida activado.",
                "transaction_id": str(tx.id),
                "monto_bono": str(perfil.bono_bienvenida_monto),
                "rollover_objetivo": str(perfil.rollover_objetivo),
                "rollover_pendiente": str(perfil.rollover_pendiente),
            },
            status=status.HTTP_201_CREATED,
        )
