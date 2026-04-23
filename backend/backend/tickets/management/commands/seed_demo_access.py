from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from tickets.models import Area, Sucursal, Tecnico, Ticket


class Command(BaseCommand):
    help = 'Crea usuarios demo (tecnico/sucursal/consultor) y un ticket de prueba.'

    @transaction.atomic
    def handle(self, *args, **options):
        grupo_tecnico, _ = Group.objects.get_or_create(name='Tecnico')
        grupo_sucursal, _ = Group.objects.get_or_create(name='Sucursal')
        grupo_consultor, _ = Group.objects.get_or_create(name='Consultor')

        area, _ = Area.objects.get_or_create(nombre='Zona Demo')

        tecnico, _ = User.objects.get_or_create(
            username='tecnico_demo',
            defaults={
                'email': 'tecnico@empresa.local',
                'first_name': 'Tecnico',
                'last_name': 'Demo',
                'is_active': True,
            },
        )
        tecnico.set_password('tecnico-2026')
        tecnico.save(update_fields=['password'])
        tecnico.groups.add(grupo_tecnico)
        Tecnico.objects.get_or_create(user=tecnico, defaults={'area': area})

        sucursal_user, _ = User.objects.get_or_create(
            username='sucursal_demo',
            defaults={
                'email': 'sucursal@empresa.local',
                'first_name': 'Sucursal',
                'last_name': 'Demo',
                'is_active': True,
            },
        )
        sucursal_user.set_password('sucursal-2026')
        sucursal_user.save(update_fields=['password'])
        sucursal_user.groups.add(grupo_sucursal)
        sucursal, _ = Sucursal.objects.get_or_create(
            user=sucursal_user,
            defaults={
                'nombre': 'Sucursal Demo',
                'direccion': 'Laboratorio',
                'area': area,
            },
        )

        consultor, _ = User.objects.get_or_create(
            username='consultor_demo',
            defaults={
                'email': 'consultor@empresa.local',
                'first_name': 'Consultor',
                'last_name': 'Demo',
                'is_active': True,
            },
        )
        consultor.set_password('consultor-2026')
        consultor.save(update_fields=['password'])
        consultor.groups.add(grupo_consultor)

        if not Ticket.objects.exists():
            inicio = timezone.now()
            Ticket.objects.create(
                titulo='Ticket de validacion',
                descripcion='Ticket inicial para validar acceso por roles.',
                equipo='Equipo Demo',
                prioridad='B',
                estado='pendiente',
                sucursal=sucursal,
                tecnico=Tecnico.objects.filter(user=tecnico).first(),
                fecha_inicio=inicio,
                fecha_limite=inicio + timedelta(hours=5),
            )

        self.stdout.write(self.style.SUCCESS('Datos demo creados/actualizados correctamente.'))
