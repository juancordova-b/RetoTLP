from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.models import EstadoCuenta, PerfilUsuario
from apps.users.validators import es_mayor_de_edad, validar_formato_dni, validar_dni_peruano

User = get_user_model()


class RegistroSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    dni = serializers.CharField(max_length=8)
    dni_digito_verificador = serializers.CharField(max_length=1)
    fecha_nacimiento = serializers.DateField()

    def validate_dni(self, value):
        if not validar_formato_dni(value):
            raise serializers.ValidationError(
                "DNI inválido: debe tener exactamente 8 dígitos numéricos (ej. 77814916)."
            )
        return value

    def validate_dni_digito_verificador(self, value):
        value = (value or "").strip()
        if len(value) != 1 or not value.isdigit():
            raise serializers.ValidationError("El dígito verificador debe ser un solo número.")
        return value

    def validate(self, attrs):
        if not es_mayor_de_edad(attrs["fecha_nacimiento"]):
            raise serializers.ValidationError("Debes ser mayor de 18 años para registrarte.")
        if not validar_dni_peruano(attrs["dni"], attrs["dni_digito_verificador"]):
            raise serializers.ValidationError(
                {
                    "dni_digito_verificador": (
                        "Dígito verificador incorrecto. Revísalo en tu documento de identidad."
                    )
                }
            )
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "Ese nombre de usuario ya existe."})
        if PerfilUsuario.objects.filter(dni=attrs["dni"]).exists():
            raise serializers.ValidationError({"dni": "Ese DNI ya está registrado."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        PerfilUsuario.objects.create(
            user=user,
            dni=validated_data["dni"],
            dni_digito_verificador=validated_data["dni_digito_verificador"],
            fecha_nacimiento=validated_data["fecha_nacimiento"],
            status=EstadoCuenta.PENDIENTE_VERIFICACION,
        )
        return user


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    limite_diario_vigente = serializers.DecimalField(
        max_digits=18, decimal_places=4, read_only=True
    )
    puede_apostar = serializers.BooleanField(read_only=True)
    puede_recargar = serializers.BooleanField(read_only=True)
    esta_autoexcluido = serializers.BooleanField(read_only=True)
    es_staff = serializers.BooleanField(source="user.is_staff", read_only=True)
    rollover_pendiente = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)

    class Meta:
        model = PerfilUsuario
        fields = (
            "username",
            "email",
            "dni",
            "dni_digito_verificador",
            "fecha_nacimiento",
            "status",
            "limite_deposito_diario",
            "limite_deposito_semanal",
            "limite_deposito_mensual",
            "limite_diario_vigente",
            "limite_semanal_vigente",
            "limite_mensual_vigente",
            "limite_deposito_diario_pendiente",
            "limite_deposito_semanal_pendiente",
            "limite_deposito_mensual_pendiente",
            "limite_efectivo_desde",
            "limite_semanal_efectivo_desde",
            "limite_mensual_efectivo_desde",
            "puede_apostar",
            "puede_recargar",
            "esta_autoexcluido",
            "autoexclusion_hasta",
            "bono_bienvenida_activo",
            "bono_bienvenida_monto",
            "rollover_objetivo",
            "rollover_acumulado",
            "rollover_pendiente",
            "bono_bienvenida_asignado_en",
            "bono_bienvenida_liberado_en",
            "es_staff",
        )
        read_only_fields = fields


class AutoexclusionSerializer(serializers.Serializer):
    dias = serializers.IntegerField(required=False, allow_null=True)
    indefinido = serializers.BooleanField(default=False)


class LimiteDiarioSerializer(serializers.Serializer):
    limite_deposito_diario = serializers.DecimalField(
        max_digits=18, decimal_places=4, required=False
    )
    limite_deposito_semanal = serializers.DecimalField(
        max_digits=18, decimal_places=4, required=False
    )
    limite_deposito_mensual = serializers.DecimalField(
        max_digits=18, decimal_places=4, required=False
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Debes enviar al menos un límite.")
        return attrs
