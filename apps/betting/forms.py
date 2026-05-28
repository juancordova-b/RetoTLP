from django import forms

from apps.betting.models import EventoDeportivo, Mercado, SeleccionMercado, TipoMercado


class EventoDeportivoAdminForm(forms.ModelForm):
    """Lista desplegable legible en lugar de un ID numérico sin lupa."""

    class Meta:
        model = EventoDeportivo
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["seleccion_ganadora"].queryset = SeleccionMercado.objects.filter(
                mercado__evento=self.instance,
                mercado__tipo=TipoMercado.RESULTADO_1X2,
            ).order_by("codigo")
            self.fields["seleccion_ganadora"].help_text = (
                "Ganador del mercado 1X2. Para OU, BTTS u otros mercados, "
                "edita cada mercado en la sección «Mercados» del admin."
            )
        else:
            self.fields["seleccion_ganadora"].queryset = SeleccionMercado.objects.none()
            self.fields["seleccion_ganadora"].help_text = (
                "Guarda el evento primero; luego edítalo para elegir el ganador 1X2."
            )

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if instance.seleccion_ganadora_id:
            mercado = instance.seleccion_ganadora.mercado
            if mercado.tipo == TipoMercado.RESULTADO_1X2:
                if mercado.seleccion_ganadora_id != instance.seleccion_ganadora_id:
                    mercado.seleccion_ganadora = instance.seleccion_ganadora
                    mercado.save(update_fields=["seleccion_ganadora"])
        return instance


class MercadoAdminForm(forms.ModelForm):
    """Ganador por mercado (OU, BTTS, hándicap, etc.)."""

    class Meta:
        model = Mercado
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["seleccion_ganadora"].queryset = SeleccionMercado.objects.filter(
                mercado=self.instance
            ).order_by("codigo", "etiqueta")
            self.fields["seleccion_ganadora"].help_text = (
                "Obligatorio para liquidar apuestas de este mercado (ej. Menos 2.5, Sí BTTS)."
            )
        else:
            self.fields["seleccion_ganadora"].queryset = SeleccionMercado.objects.none()
            self.fields["seleccion_ganadora"].help_text = (
                "Guarda el mercado primero; luego edítalo para marcar el ganador."
            )
