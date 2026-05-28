from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("betting", "0006_nivel2"),
    ]

    operations = [
        migrations.AddField(
            model_name="mercado",
            name="seleccion_ganadora",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="mercados_ganados",
                to="betting.seleccionmercado",
                verbose_name="selección ganadora del mercado",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="piernacombinada",
            unique_together={("combinada", "seleccion")},
        ),
    ]
