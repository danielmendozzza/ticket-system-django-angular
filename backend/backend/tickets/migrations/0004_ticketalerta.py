# Generated manually for ticket alerts.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0003_ticket_mejoras_empresa'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketAlerta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('por_vencer', 'Por vencer'), ('vencido', 'Vencido')], max_length=20)),
                ('mensaje', models.CharField(max_length=255)),
                ('leida', models.BooleanField(default=False)),
                ('fecha_generada', models.DateTimeField(auto_now_add=True)),
                ('fecha_leida', models.DateTimeField(blank=True, null=True)),
                ('tecnico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertas', to='tickets.tecnico')),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertas', to='tickets.ticket')),
            ],
            options={
                'ordering': ['leida', '-fecha_generada'],
            },
        ),
        migrations.AddConstraint(
            model_name='ticketalerta',
            constraint=models.UniqueConstraint(fields=('ticket', 'tipo'), name='unique_alerta_por_ticket_y_tipo'),
        ),
    ]
