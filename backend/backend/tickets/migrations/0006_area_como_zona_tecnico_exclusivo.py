from django.db import migrations, models
import django.db.models.deletion


def preparar_zonas_unicas_para_tecnicos(apps, schema_editor):
    Area = apps.get_model('tickets', 'Area')
    Tecnico = apps.get_model('tickets', 'Tecnico')

    for area in Area.objects.all().order_by('id'):
        tecnicos = list(Tecnico.objects.filter(area_id=area.id).order_by('id'))
        if len(tecnicos) <= 1:
            continue

        for tecnico in tecnicos[1:]:
            zona_duplicada = Area.objects.create(
                nombre=f'{area.nombre} - tecnico {tecnico.id}'
            )
            tecnico.area = zona_duplicada
            tecnico.save(update_fields=['area'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0005_crear_usuario_admin_reportes'),
    ]

    operations = [
        migrations.RunPython(preparar_zonas_unicas_para_tecnicos, noop_reverse),
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
