from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_limites_semanal_mensual_pendientes"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="bono_bienvenida_activo",
            field=models.BooleanField(
                default=False,
                help_text="True cuando existe un bono de bienvenida con rollover pendiente.",
            ),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="bono_bienvenida_asignado_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="bono_bienvenida_liberado_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="bono_bienvenida_monto",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=18),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="rollover_acumulado",
            field=models.DecimalField(decimal_places=4, default=0, max_digits=18),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="rollover_objetivo",
            field=models.DecimalField(
                decimal_places=4,
                default=0,
                help_text="Monto total que debe apostarse antes de permitir retiro.",
                max_digits=18,
            ),
        ),
    ]
