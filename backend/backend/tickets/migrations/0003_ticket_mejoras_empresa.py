# Generated manually for enterprise ticket enhancements.

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0002_sucursal_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='equipo',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='fecha_conclusion',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='fecha_inicio',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='fecha_limite',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
