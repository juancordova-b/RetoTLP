from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.betting.models import EventStatus, Market, MarketSelection, SportEvent


class Command(BaseCommand):
    help = "Crea eventos de demo (Mundial 2026) con mercado 1X2 y cuotas de ejemplo."

    def handle(self, *args, **options):
        if SportEvent.objects.exists():
            self.stdout.write(self.style.WARNING("Ya hay eventos; omitiendo seed."))
            return

        partidos = [
            ("Perú vs Chile", "Perú", "Chile", Decimal("2.10"), Decimal("3.20"), Decimal("3.50")),
            ("Argentina vs Brasil", "Argentina", "Brasil", Decimal("2.80"), Decimal("3.10"), Decimal("2.45")),
            ("España vs Francia", "España", "Francia", Decimal("2.55"), Decimal("3.00"), Decimal("2.90")),
        ]
        inicio = timezone.now() + timedelta(days=2)

        for nombre, local, visitante, o1, ox, o2 in partidos:
            event = SportEvent.objects.create(
                nombre=nombre,
                equipo_local=local,
                equipo_visitante=visitante,
                inicio_programado=inicio,
                status=EventStatus.PROGRAMADO,
            )
            market = Market.objects.create(event=event, nombre="Resultado 1X2", tipo="1X2")
            MarketSelection.objects.bulk_create(
                [
                    MarketSelection(market=market, etiqueta=f"Gana {local}", codigo="1", odds=o1),
                    MarketSelection(market=market, etiqueta="Empate", codigo="X", odds=ox),
                    MarketSelection(
                        market=market, etiqueta=f"Gana {visitante}", codigo="2", odds=o2
                    ),
                ]
            )
            inicio += timedelta(hours=3)

        self.stdout.write(self.style.SUCCESS(f"Creados {len(partidos)} eventos con mercado 1X2."))
