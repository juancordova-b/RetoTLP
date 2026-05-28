from decimal import Decimal

from rest_framework import serializers

from apps.betting.models import Apuesta, ApuestaCombinada, EventoDeportivo, Mercado, SeleccionMercado


class SeleccionMercadoSerializer(serializers.ModelSerializer):
    mercado_disponible = serializers.SerializerMethodField()

    class Meta:
        model = SeleccionMercado
        fields = ("id", "etiqueta", "codigo", "odds", "activo", "mercado_disponible")

    def get_mercado_disponible(self, obj):
        return obj.mercado.esta_disponible


class MercadoSerializer(serializers.ModelSerializer):
    selecciones = SeleccionMercadoSerializer(many=True, read_only=True)
    disponible = serializers.SerializerMethodField()

    class Meta:
        model = Mercado
        fields = ("id", "nombre", "tipo", "activo", "disponible", "suspendido_hasta", "selecciones")

    def get_disponible(self, obj):
        return obj.esta_disponible


class EventoDeportivoListaSerializer(serializers.ModelSerializer):
    mercados = MercadoSerializer(many=True, read_only=True)
    mercado_1x2 = serializers.SerializerMethodField()

    class Meta:
        model = EventoDeportivo
        fields = (
            "id",
            "nombre",
            "equipo_local",
            "equipo_visitante",
            "goles_local",
            "goles_visitante",
            "inicio_programado",
            "status",
            "mercado_1x2",
            "mercados",
        )

    def get_mercado_1x2(self, obj):
        mercado = obj.mercados.filter(tipo="1X2").first()
        if not mercado:
            return None
        return MercadoSerializer(mercado).data


class ColocarApuestaSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    selection_id = serializers.IntegerField()
    stake = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("1.0000"))
    odds_esperada = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    confirmar_requote = serializers.BooleanField(default=False)
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)


class ColocarCombinadaSerializer(serializers.Serializer):
    selection_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=2, max_length=10
    )
    stake = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("1.0000"))
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)


class ApuestaSerializer(serializers.ModelSerializer):
    evento = serializers.CharField(source="evento.__str__", read_only=True)
    seleccion = serializers.CharField(source="seleccion.etiqueta", read_only=True)
    cashout_disponible = serializers.SerializerMethodField()
    cashout_estimado = serializers.SerializerMethodField()

    class Meta:
        model = Apuesta
        fields = (
            "id",
            "evento",
            "seleccion",
            "stake",
            "odds_locked",
            "status",
            "payout_potencial",
            "cashout_disponible",
            "cashout_estimado",
            "cashout_monto",
            "cashout_en",
            "creado_en",
        )

    def get_cashout_disponible(self, obj):
        return obj.status == "aceptada"

    def get_cashout_estimado(self, obj):
        if obj.status != "aceptada":
            return None
        try:
            from apps.betting.services import calcular_cashout

            return str(calcular_cashout(obj))
        except Exception:
            return None


class PiernaCombinadaSerializer(serializers.Serializer):
    evento = serializers.CharField()
    seleccion = serializers.CharField()
    odds_locked = serializers.DecimalField(max_digits=10, decimal_places=2)


class ApuestaCombinadaSerializer(serializers.ModelSerializer):
    piernas = serializers.SerializerMethodField()

    class Meta:
        model = ApuestaCombinada
        fields = (
            "id",
            "stake",
            "odds_locked",
            "status",
            "payout_potencial",
            "piernas",
            "creado_en",
        )

    def get_piernas(self, obj):
        return [
            {
                "evento": str(p.evento),
                "seleccion": p.seleccion.etiqueta,
                "odds_locked": str(p.odds_locked),
            }
            for p in obj.piernas.all()
        ]
