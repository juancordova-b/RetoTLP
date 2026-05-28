from django.db import migrations, models


def convertir_estados_apuesta(apps, schema_editor):
    Apuesta = apps.get_model("betting", "Apuesta")
    mapping = {
        "accepted": "aceptada",
        "won": "ganada",
        "lost": "perdida",
        "void": "anulada",
    }
    for anterior, nuevo in mapping.items():
        Apuesta.objects.filter(status=anterior).update(status=nuevo)


class Migration(migrations.Migration):

    dependencies = [
        ("betting", "0002_nombres_es"),
    ]

    operations = [
        migrations.RunPython(convertir_estados_apuesta, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="apuesta",
            name="status",
            field=models.CharField(
                choices=[
                    ("aceptada", "Aceptada"),
                    ("ganada", "Ganada"),
                    ("perdida", "Perdida"),
                    ("anulada", "Anulada"),
                ],
                default="aceptada",
                max_length=16,
                verbose_name="estado",
            ),
        ),
    ]
