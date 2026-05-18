from django.contrib.auth.hashers import make_password
from django.db import migrations


def crear_usuario_superadmin(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    user, _ = User.objects.get_or_create(
        username='superadmin',
        defaults={
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'email': 'superadmin@empresa.local',
        },
    )
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.password = make_password('dmendoza1*')
    user.save(update_fields=['is_staff', 'is_superuser', 'is_active', 'password'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0007_ticket_evidencia_cierre'),
    ]

    operations = [
        migrations.RunPython(crear_usuario_superadmin, noop_reverse),
    ]
