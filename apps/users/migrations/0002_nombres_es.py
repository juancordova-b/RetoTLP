from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name="UserProfile",
            new_name="PerfilUsuario",
        ),
        migrations.AlterField(
            model_name="perfilusuario",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="perfil",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="perfilusuario",
            name="status",
            field=models.CharField(
                choices=[
                    ("pendiente_verificacion", "Pendiente de verificación"),
                    ("verificado", "Verificado"),
                    ("bloqueado", "Bloqueado"),
                    ("autoexcluido", "Autoexcluido"),
                ],
                default="pendiente_verificacion",
                max_length=32,
                verbose_name="estado",
            ),
        ),
    ]
