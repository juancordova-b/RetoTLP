from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_dni_digito_verificador"),
    ]

    operations = [
        migrations.AlterField(
            model_name="perfilusuario",
            name="dni_digito_verificador",
            field=models.CharField(
                help_text="Dígito verificador calculado sobre los 8 dígitos del DNI.",
                max_length=1,
                verbose_name="dígito verificador DNI",
            ),
        ),
    ]
