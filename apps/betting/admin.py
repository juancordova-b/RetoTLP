from django.contrib import admin, messages

from apps.betting.forms import EventoDeportivoAdminForm, MercadoAdminForm
from apps.betting.models import (
    Apuesta,
    ApuestaCombinada,
    EstadoEvento,
    EventoDeportivo,
    Mercado,
    PiernaCombinada,
    SeleccionMercado,
    TipoMercado,
)
from apps.betting.odds_broadcast import broadcast_odds_evento
from apps.betting.services import (
    ErrorApuesta,
    liquidar_evento,
    mercados_sin_ganador_para_liquidacion,
    registrar_evento_critico_inplay,
    registrar_gol_evento,
    suspender_mercado_por_evento_critico,
)


class SeleccionMercadoInline(admin.TabularInline):
    model = SeleccionMercado
    extra = 3


class MercadoInline(admin.TabularInline):
    model = Mercado
    extra = 1


@admin.action(description="Marcar eventos como EN VIVO")
def accion_marcar_en_vivo(modeladmin, request, queryset):
    actualizados = queryset.exclude(status=EstadoEvento.ANULADO).update(
        status=EstadoEvento.EN_VIVO
    )
    modeladmin.message_user(
        request,
        f"{actualizados} evento(s) marcados como en vivo. Ya aceptan apuestas in-play.",
        messages.SUCCESS,
    )


@admin.action(description="Simular gol / evento crítico (suspender 1X2 30s)")
def accion_simular_evento_critico(modeladmin, request, queryset):
    total = 0
    for evento in queryset:
        mercados = Mercado.objects.filter(evento=evento, tipo=TipoMercado.RESULTADO_1X2)
        if not mercados.exists():
            modeladmin.message_user(
                request,
                f"{evento}: no tiene mercado 1X2 para suspender.",
                messages.WARNING,
            )
            continue
        for mercado in mercados:
            suspender_mercado_por_evento_critico(mercado.id)
            total += 1
        if evento.status == EstadoEvento.PROGRAMADO:
            evento.status = EstadoEvento.EN_VIVO
            evento.save(update_fields=["status"])

    modeladmin.message_user(
        request,
        f"Simulación enviada: {total} mercado(s) 1X2 suspendidos temporalmente. "
        "Channels notifica al frontend y Celery los reactiva.",
        messages.SUCCESS if total else messages.WARNING,
    )


@admin.action(description="Simular expulsión / evento crítico")
def accion_simular_expulsion(modeladmin, request, queryset):
    total = 0
    for evento in queryset:
        try:
            registrar_evento_critico_inplay(evento.id, descripcion="Expulsión simulada")
            modeladmin.message_user(
                request,
                f"{evento}: expulsión simulada. Mercado 1X2 suspendido temporalmente.",
                messages.SUCCESS,
            )
            total += 1
        except ErrorApuesta as e:
            modeladmin.message_user(request, f"{evento}: {e}", messages.ERROR)
    if not total:
        modeladmin.message_user(request, "No se simuló ninguna expulsión.", messages.WARNING)


@admin.action(description="Registrar gol del LOCAL")
def accion_gol_local(modeladmin, request, queryset):
    _registrar_goles_admin(modeladmin, request, queryset, lado="local")


@admin.action(description="Registrar gol del VISITANTE")
def accion_gol_visitante(modeladmin, request, queryset):
    _registrar_goles_admin(modeladmin, request, queryset, lado="visitante")


def _registrar_goles_admin(modeladmin, request, queryset, lado: str) -> None:
    total = 0
    for evento in queryset:
        try:
            evento = registrar_gol_evento(evento.id, lado=lado)
            equipo = evento.equipo_local if lado == "local" else evento.equipo_visitante
            modeladmin.message_user(
                request,
                f"Gol registrado: {equipo}. Marcador: {evento.marcador}. "
                "Mercado 1X2 suspendido temporalmente.",
                messages.SUCCESS,
            )
            total += 1
        except ErrorApuesta as e:
            modeladmin.message_user(request, f"{evento}: {e}", messages.ERROR)
    if not total:
        modeladmin.message_user(request, "No se registró ningún gol.", messages.WARNING)


@admin.action(description="Finalizar eventos seleccionados")
def accion_finalizar_eventos(modeladmin, request, queryset):
    actualizados = queryset.exclude(status=EstadoEvento.ANULADO).update(
        status=EstadoEvento.FINALIZADO
    )
    modeladmin.message_user(
        request,
        f"{actualizados} evento(s) finalizados. Define ganadores antes de liquidar.",
        messages.SUCCESS,
    )


@admin.action(description="Liquidar apuestas de eventos seleccionados")
def accion_liquidar_eventos(modeladmin, request, queryset):
    for evento in queryset:
        try:
            pendientes = mercados_sin_ganador_para_liquidacion(evento)
            if pendientes:
                nombres = ", ".join(m.nombre for m in pendientes)
                modeladmin.message_user(
                    request,
                    f"{evento}: faltan ganadores en mercados: {nombres}. "
                    "Edítalos en Admin → Mercados antes de liquidar.",
                    messages.WARNING,
                )
                continue
            stats = liquidar_evento(evento)
            modeladmin.message_user(
                request,
                f"{evento}: ganadas {stats['ganadas']}, perdidas {stats['perdidas']}, "
                f"anuladas {stats['anuladas']}, combinadas revisadas {stats['combinadas']}.",
                messages.SUCCESS,
            )
        except ErrorApuesta as e:
            modeladmin.message_user(request, f"{evento}: {e}", messages.ERROR)


@admin.register(SeleccionMercado)
class SeleccionMercadoAdmin(admin.ModelAdmin):
    list_display = ("id", "mercado", "etiqueta", "codigo", "odds", "activo")
    list_filter = ("mercado__evento", "codigo")
    search_fields = ("etiqueta", "mercado__evento__nombre")

    def save_model(self, request, obj, form, change):
        cuota_cambio = False
        if change and "odds" in form.changed_data:
            cuota_cambio = True
        super().save_model(request, obj, form, change)
        if cuota_cambio:
            broadcast_odds_evento(
                obj.mercado.evento_id,
                {
                    "tipo": "odds_update",
                    "evento_id": obj.mercado.evento_id,
                    "selection_id": obj.id,
                    "mercado_id": obj.mercado_id,
                    "odds": str(obj.odds),
                    "etiqueta": obj.etiqueta,
                },
            )
            self.message_user(
                request,
                f"Cuota actualizada y notificada en vivo: {obj.etiqueta} @ {obj.odds}.",
                messages.SUCCESS,
            )


@admin.action(description="Suspender mercados seleccionados 30s")
def accion_suspender_mercados(modeladmin, request, queryset):
    total = 0
    for mercado in queryset:
        suspender_mercado_por_evento_critico(mercado.id)
        total += 1
    modeladmin.message_user(
        request,
        f"{total} mercado(s) suspendidos temporalmente. Celery los reactivará.",
        messages.SUCCESS if total else messages.WARNING,
    )


@admin.register(Mercado)
class MercadoAdmin(admin.ModelAdmin):
    form = MercadoAdminForm
    list_display = ("id", "evento", "nombre", "tipo", "seleccion_ganadora", "activo")
    list_filter = ("tipo", "evento")
    search_fields = ("nombre", "evento__nombre", "evento__equipo_local")
    actions = [accion_suspender_mercados]


@admin.register(EventoDeportivo)
class EventoDeportivoAdmin(admin.ModelAdmin):
    form = EventoDeportivoAdminForm
    list_display = (
        "nombre",
        "equipo_local",
        "equipo_visitante",
        "marcador_admin",
        "status",
        "seleccion_ganadora",
        "inicio_programado",
    )
    list_filter = ("status",)
    inlines = [MercadoInline]
    actions = [
        accion_marcar_en_vivo,
        accion_gol_local,
        accion_gol_visitante,
        accion_simular_expulsion,
        accion_simular_evento_critico,
        accion_finalizar_eventos,
        accion_liquidar_eventos,
    ]

    @admin.display(description="Marcador")
    def marcador_admin(self, obj):
        return f"{obj.goles_local} - {obj.goles_visitante}"


class PiernaCombinadaInline(admin.TabularInline):
    model = PiernaCombinada
    extra = 0


@admin.register(ApuestaCombinada)
class ApuestaCombinadaAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "stake", "odds_locked", "status", "creado_en")
    list_filter = ("status",)
    inlines = [PiernaCombinadaInline]


@admin.register(Apuesta)
class ApuestaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "evento",
        "stake",
        "odds_locked",
        "status",
        "cashout_monto",
        "creado_en",
    )
    list_filter = ("status",)
