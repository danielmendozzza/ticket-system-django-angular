from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0005_crear_usuario_admin_reportes'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='area',
            options={'verbose_name': 'Zona', 'verbose_name_plural': 'Zonas'},
        ),
        migrations.AlterField(
            model_name='sucursal',
            name='area',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tickets.area', verbose_name='zona'),
        ),
        migrations.AlterField(
            model_name='tecnico',
            name='area',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='tickets.area', verbose_name='zona'),
        ),
    ]
