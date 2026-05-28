from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_alter_perfilusuario_dni_digito_verificador"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="limite_deposito_semanal_pendiente",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                help_text="Nuevo límite semanal que aplica tras 24 h si es mayor al actual",
                max_digits=18,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="limite_deposito_mensual_pendiente",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                help_text="Nuevo límite mensual que aplica tras 24 h si es mayor al actual",
                max_digits=18,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="limite_semanal_efectivo_desde",
            field=models.DateTimeField(
                blank=True,
                help_text="Momento en que entra en vigor el límite semanal pendiente",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="limite_mensual_efectivo_desde",
            field=models.DateTimeField(
                blank=True,
                help_text="Momento en que entra en vigor el límite mensual pendiente",
                null=True,
            ),
        ),
    ]
