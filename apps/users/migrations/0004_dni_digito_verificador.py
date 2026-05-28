from django.db import migrations, models


DNI_WEIGHTS = (3, 2, 7, 6, 5, 4, 3, 2)
SERIE_VERIFICADOR = "6789012345"


def calcular_digito(dni):
    nums = [int(c) for c in dni[:8]]
    total = sum(n * w for n, w in zip(nums, DNI_WEIGHTS))
    resto = total % 11
    digito = 11 - resto
    if digito == 11:
        digito = 0
    elif digito == 10:
        digito = 0
    digito += 1
    return SERIE_VERIFICADOR[digito - 1]


def completar_digitos_verificadores(apps, schema_editor):
    PerfilUsuario = apps.get_model("users", "PerfilUsuario")
    for perfil in PerfilUsuario.objects.all():
        if perfil.dni and len(perfil.dni) == 8 and perfil.dni.isdigit():
            perfil.dni_digito_verificador = calcular_digito(perfil.dni)
            perfil.save(update_fields=["dni_digito_verificador"])


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_nivel1_completo"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="dni_digito_verificador",
            field=models.CharField(
                default="",
                help_text="Dígito verificador calculado sobre los 8 dígitos del DNI.",
                max_length=1,
                verbose_name="dígito verificador DNI",
            ),
        ),
        migrations.RunPython(completar_digitos_verificadores, migrations.RunPython.noop),
    ]
