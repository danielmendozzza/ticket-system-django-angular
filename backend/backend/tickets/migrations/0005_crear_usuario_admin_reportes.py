from django.contrib.auth.hashers import make_password
from django.db import migrations


def crear_usuario_admin(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    User.objects.get_or_create(
        username='admin',
        defaults={
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'email': 'admin@empresa.local',
            'password': make_password('admin-2026'),
        },
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0004_ticketalerta'),
    ]

    operations = [
        migrations.RunPython(crear_usuario_admin, noop_reverse),
    ]
