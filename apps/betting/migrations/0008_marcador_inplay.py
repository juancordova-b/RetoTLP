from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("betting", "0007_combinada_mismo_partido_soles"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventodeportivo",
            name="goles_local",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="eventodeportivo",
            name="goles_visitante",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
