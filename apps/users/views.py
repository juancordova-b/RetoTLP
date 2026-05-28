from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import EstadoCuenta, PerfilUsuario
from apps.users.serializers import (
    AutoexclusionSerializer,
    LimiteDiarioSerializer,
    PerfilUsuarioSerializer,
    RegistroSerializer,
)
from apps.users import services as servicios_perfil
from apps.users.services import ErrorPerfil


class VistaRegistro(APIView):
    """Registro con KYC inicial (queda pendiente_verificacion hasta que admin verifique)."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        perfil = user.perfil
        try:
            from apps.audit.antifraude import evaluar_registro_usuario
            from apps.audit.context import get_client_ip
            from apps.audit.services import registrar_auditoria

            registrar_auditoria(
                tipo_evento="registro_usuario",
                referencia=str(user.id),
                payload={"username": user.username, "dni": perfil.dni},
                usuario=user,
                ip_origen=get_client_ip(),
            )
            evaluar_registro_usuario(user)
        except Exception:
            # En etapas tempranas del proyecto, audit puede no estar listo aún.
            pass
        return Response(
            {
                "token": token.key,
                "perfil": PerfilUsuarioSerializer(perfil).data,
                "mensaje": "Registro exitoso. Tu cuenta está pendiente de verificación (KYC simulado).",
            },
            status=status.HTTP_201_CREATED,
        )


class VistaMiPerfil(APIView):
    """Devuelve el perfil del usuario autenticado."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            perfil = user.perfil
            return Response(PerfilUsuarioSerializer(perfil).data)
        except PerfilUsuario.DoesNotExist:
            # Superusuarios creados con createsuperuser no tienen PerfilUsuario.
            if user.is_staff:
                return Response(
                    {
                        "username": user.username,
                        "email": user.email or "",
                        "es_staff": True,
                        "status": "staff_sin_perfil",
                        "puede_apostar": False,
                        "puede_recargar": False,
                        "es_cuenta_operador": True,
                        "mensaje": "Cuenta operador (staff). Usa Operador o /admin/.",
                    }
                )
            return Response(
                {"error": "Perfil no encontrado. Regístrate con /api/users/register/."},
                status=status.HTTP_404_NOT_FOUND,
            )


class VistaVerificarKyc(APIView):
    """
    Simula que un admin verificó el KYC (solo para demo del avance).
    En producción esto sería un endpoint de staff.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        perfil = request.user.perfil
        if perfil.esta_autoexcluido:
            return Response(
                {"error": "Cuenta autoexcluida; no se puede verificar."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        perfil.status = EstadoCuenta.VERIFICADO
        perfil.save(update_fields=["status", "actualizado_en"])
        return Response(
            {
                "mensaje": "Cuenta verificada (simulación KYC).",
                "perfil": PerfilUsuarioSerializer(perfil).data,
            }
        )


class VistaAutoexclusion(APIView):
    """Autoexclusión temporal (7/30/90 días) o indefinida."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AutoexclusionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        perfil = request.user.perfil
        try:
            servicios_perfil.autoexcluir(
                perfil,
                dias=serializer.validated_data.get("dias"),
                indefinido=serializer.validated_data.get("indefinido", False),
            )
        except ErrorPerfil as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        perfil.refresh_from_db()
        return Response(
            {
                "mensaje": "Autoexclusión activada. No podrás apostar ni recargar hasta que termine el plazo.",
                "perfil": PerfilUsuarioSerializer(perfil).data,
            }
        )


class VistaLimiteDiario(APIView):
    """Actualizar límites diario/semanal/mensual (subir = 24 h de espera)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LimiteDiarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        perfil = request.user.perfil
        try:
            limites = {}
            if "limite_deposito_diario" in serializer.validated_data:
                limites["diario"] = serializer.validated_data["limite_deposito_diario"]
            if "limite_deposito_semanal" in serializer.validated_data:
                limites["semanal"] = serializer.validated_data["limite_deposito_semanal"]
            if "limite_deposito_mensual" in serializer.validated_data:
                limites["mensual"] = serializer.validated_data["limite_deposito_mensual"]
            servicios_perfil.actualizar_limites(perfil, limites)
        except ErrorPerfil as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        perfil.refresh_from_db()
        mensaje = "Límites actualizados."
        pendientes = [
            perfil.limite_deposito_diario_pendiente,
            perfil.limite_deposito_semanal_pendiente,
            perfil.limite_deposito_mensual_pendiente,
        ]
        if any(pendientes):
            mensaje = (
                "Solicitud registrada. Los aumentos de límite aplicarán en 24 horas. "
                "Las reducciones ya están activas."
            )
        return Response({"mensaje": mensaje, "perfil": PerfilUsuarioSerializer(perfil).data})
