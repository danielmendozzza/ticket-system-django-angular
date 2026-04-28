from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0006_area_como_zona_tecnico_exclusivo'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='evidencia_cierre',
            field=models.FileField(blank=True, null=True, upload_to='tickets/evidencias/'),
        ),
    ]
