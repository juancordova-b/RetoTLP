from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("betting", "0001_initial"),
        ("wallet", "0002_nombres_es"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name="SportEvent",
            new_name="EventoDeportivo",
        ),
        migrations.RenameModel(
            old_name="Market",
            new_name="Mercado",
        ),
        migrations.RenameModel(
            old_name="MarketSelection",
            new_name="SeleccionMercado",
        ),
        migrations.RenameModel(
            old_name="Bet",
            new_name="Apuesta",
        ),
        migrations.AlterModelOptions(
            name="eventodeportivo",
            options={
                "ordering": ["inicio_programado"],
                "verbose_name": "Evento deportivo",
                "verbose_name_plural": "Eventos deportivos",
            },
        ),
        migrations.AlterModelOptions(
            name="mercado",
            options={
                "verbose_name": "Mercado",
                "verbose_name_plural": "Mercados",
            },
        ),
        migrations.AlterModelOptions(
            name="seleccionmercado",
            options={
                "verbose_name": "Selección de mercado",
                "verbose_name_plural": "Selecciones de mercado",
            },
        ),
        migrations.AlterModelOptions(
            name="apuesta",
            options={
                "ordering": ["-creado_en"],
                "verbose_name": "Apuesta",
                "verbose_name_plural": "Apuestas",
            },
        ),
        migrations.RenameField(
            model_name="mercado",
            old_name="event",
            new_name="evento",
        ),
        migrations.AlterField(
            model_name="mercado",
            name="evento",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="mercados",
                to="betting.eventodeportivo",
            ),
        ),
        migrations.RenameField(
            model_name="seleccionmercado",
            old_name="market",
            new_name="mercado",
        ),
        migrations.AlterField(
            model_name="seleccionmercado",
            name="mercado",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="selecciones",
                to="betting.mercado",
            ),
        ),
        migrations.RenameField(
            model_name="apuesta",
            old_name="event",
            new_name="evento",
        ),
        migrations.RenameField(
            model_name="apuesta",
            old_name="selection",
            new_name="seleccion",
        ),
        migrations.RenameField(
            model_name="apuesta",
            old_name="ledger_transaction",
            new_name="transaccion_contable",
        ),
        migrations.AlterField(
            model_name="apuesta",
            name="transaccion_contable",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="wallet.transaccioncontable",
            ),
        ),
        migrations.AlterField(
            model_name="apuesta",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="apuestas",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="eventodeportivo",
            name="status",
            field=models.CharField(
                choices=[
                    ("programado", "Programado"),
                    ("en_vivo", "En vivo"),
                    ("finalizado", "Finalizado"),
                    ("suspendido", "Suspendido"),
                    ("anulado", "Anulado"),
                ],
                default="programado",
                max_length=20,
                verbose_name="estado",
            ),
        ),
        migrations.AlterField(
            model_name="apuesta",
            name="status",
            field=models.CharField(
                choices=[
                    ("accepted", "Aceptada"),
                    ("won", "Ganada"),
                    ("lost", "Perdida"),
                    ("void", "Anulada"),
                ],
                default="accepted",
                max_length=16,
                verbose_name="estado",
            ),
        ),
    ]
