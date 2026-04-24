from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .alerts import generar_alertas_tickets
from .models import Area, Sucursal, Tecnico, Ticket, TicketAlerta


class TicketModelTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre='Zona A')
        self.user = User.objects.create_user(username='sucursal1', password='123456')
        self.tecnico_user = User.objects.create_user(username='tecnico1', password='123456')
        self.sucursal_group, _ = Group.objects.get_or_create(name='Sucursal')
        self.tecnico_group, _ = Group.objects.get_or_create(name='Tecnico')
        self.consultor_group, _ = Group.objects.get_or_create(name='Consultor')
        self.user.groups.add(self.sucursal_group)
        self.tecnico_user.groups.add(self.tecnico_group)
        self.sucursal = Sucursal.objects.create(
            user=self.user,
            nombre='Sucursal Centro',
            area=self.area,
        )
        self.tecnico = Tecnico.objects.create(
            user=self.tecnico_user,
            area=self.area,
        )
        self.report_admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )
        self.report_admin.set_password('admin-2026')
        self.report_admin.save()
        self.api_client = APIClient()

    def test_ticket_no_asigna_admin_como_tecnico(self):
        area_reportes = Area.objects.create(nombre='Zona Reportes')
        sucursal_reportes = Sucursal.objects.create(
            nombre='Sucursal Reportes',
            area=area_reportes,
        )
        Tecnico.objects.create(
            user=self.report_admin,
            area=area_reportes,
        )

        ticket = Ticket.objects.create(
            titulo='No funciona televisor',
            descripcion='La pantalla no enciende',
            prioridad='B',
            sucursal=sucursal_reportes,
        )

        self.assertIsNone(ticket.tecnico)

    def test_ticket_asigna_tecnico_de_la_zona_de_la_sucursal(self):
        otra_area = Area.objects.create(nombre='Zona B')
        tecnico_user_2 = User.objects.create_user(username='tecnico2', password='123456')
        tecnico_user_2.groups.add(self.tecnico_group)
        Tecnico.objects.create(user=tecnico_user_2, area=otra_area)

        ticket = Ticket.objects.create(
            titulo='Nuevo ticket de zona',
            descripcion='Debe ir al tecnico de la zona de la sucursal',
            prioridad='B',
            sucursal=self.sucursal,
        )

        self.assertEqual(ticket.tecnico, self.tecnico)

    def test_zona_es_exclusiva_para_un_solo_tecnico(self):
        tecnico_user_2 = User.objects.create_user(username='tecnico2', password='123456')
        tecnico_user_2.groups.add(self.tecnico_group)

        with self.assertRaises(IntegrityError):
            Tecnico.objects.create(user=tecnico_user_2, area=self.area)

    def test_ticket_calcula_fecha_limite_segun_prioridad(self):
        inicio = timezone.now()
        ticket = Ticket.objects.create(
            titulo='Impresora sin conexion',
            descripcion='No imprime',
            prioridad='A',
            sucursal=self.sucursal,
            fecha_inicio=inicio,
        )

        self.assertIsNotNone(ticket.tecnico)
        self.assertEqual(ticket.tecnico, self.tecnico)
        self.assertIsNotNone(ticket.fecha_limite)
        self.assertLessEqual(
            abs(ticket.fecha_limite - (inicio + timedelta(hours=5))),
            timedelta(seconds=1),
        )

    def test_ticket_calcula_fecha_limite_prioridad_b_y_c(self):
        inicio = timezone.now()
        ticket_media = Ticket.objects.create(
            titulo='Sistema intermitente',
            descripcion='Prioridad media',
            prioridad='B',
            sucursal=self.sucursal,
            fecha_inicio=inicio,
        )
        ticket_baja = Ticket.objects.create(
            titulo='Ajuste menor',
            descripcion='Prioridad baja',
            prioridad='C',
            sucursal=self.sucursal,
            fecha_inicio=inicio,
        )

        self.assertLessEqual(
            abs(ticket_media.fecha_limite - (inicio + timedelta(hours=15))),
            timedelta(seconds=1),
        )
        self.assertLessEqual(
            abs(ticket_baja.fecha_limite - (inicio + timedelta(hours=24))),
            timedelta(seconds=1),
        )

    def test_ticket_realizado_registra_fecha_conclusion(self):
        ticket = Ticket.objects.create(
            titulo='PC lenta',
            descripcion='Revisar rendimiento',
            prioridad='B',
            sucursal=self.sucursal,
            estado='realizado',
        )

        self.assertIsNotNone(ticket.fecha_conclusion)

    def test_admin_actualiza_prioridad_y_recalcula_fecha_limite_si_no_fue_editada(self):
        inicio = timezone.now()
        ticket = Ticket.objects.create(
            titulo='Monitor con falla',
            descripcion='Caso para recalculo',
            prioridad='B',
            sucursal=self.sucursal,
            fecha_inicio=inicio,
        )
        fecha_limite_original = ticket.fecha_limite

        self.api_client.force_authenticate(user=self.report_admin)
        response = self.api_client.patch(
            f'/api/tickets/{ticket.id}/',
            {
                'prioridad': 'A',
                'fecha_inicio': inicio.isoformat(),
                'fecha_limite': fecha_limite_original.isoformat(),
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        ticket.refresh_from_db()
        self.assertLessEqual(
            abs(ticket.fecha_limite - (inicio + timedelta(hours=5))),
            timedelta(seconds=1),
        )

    def test_genera_alerta_por_ticket_por_vencer(self):
        ticket = Ticket.objects.create(
            titulo='Servidor con latencia',
            descripcion='Revisar conectividad',
            prioridad='A',
            sucursal=self.sucursal,
            fecha_inicio=timezone.now() - timedelta(hours=4, minutes=35),
        )

        resultado = generar_alertas_tickets()

        self.assertEqual(resultado['procesados'], 1)
        self.assertTrue(
            TicketAlerta.objects.filter(ticket=ticket, tipo='por_vencer', tecnico=self.tecnico).exists()
        )

    def test_genera_alerta_por_ticket_vencido(self):
        ticket = Ticket.objects.create(
            titulo='Caja fuera de servicio',
            descripcion='Equipo no inicia',
            prioridad='A',
            sucursal=self.sucursal,
            fecha_inicio=timezone.now() - timedelta(hours=6),
        )

        generar_alertas_tickets()

        self.assertTrue(
            TicketAlerta.objects.filter(ticket=ticket, tipo='vencido', tecnico=self.tecnico).exists()
        )

    def test_tecnico_puede_marcar_su_alerta_como_leida(self):
        ticket = Ticket.objects.create(
            titulo='Router por vencer',
            descripcion='Revisar enlace',
            prioridad='A',
            sucursal=self.sucursal,
            fecha_inicio=timezone.now() - timedelta(hours=4, minutes=35),
        )
        generar_alertas_tickets()
        alerta = TicketAlerta.objects.get(ticket=ticket, tipo='por_vencer')

        self.api_client.force_authenticate(user=self.tecnico_user)
        response = self.api_client.post(f'/api/alertas/{alerta.id}/marcar-leida/')

        self.assertEqual(response.status_code, 200)
        alerta.refresh_from_db()
        self.assertTrue(alerta.leida)
        self.assertIsNotNone(alerta.fecha_leida)

    def test_reporte_resumen_solo_disponible_para_admin(self):
        self.api_client.force_authenticate(user=self.report_admin)
        response = self.api_client.get('/api/reportes/resumen/?meses=3')

        self.assertEqual(response.status_code, 200)

    def test_admin_puede_crear_usuario_sucursal_desde_api(self):
        self.api_client.force_authenticate(user=self.report_admin)
        response = self.api_client.post(
            '/api/admin/usuarios/',
            {
                'username': 'sucursal_api',
                'password': '123456',
                'rol': 'Sucursal',
                'area': self.area.id,
                'nombre_sucursal': 'Sucursal API',
                'direccion': 'Calle API',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='sucursal_api')
        self.assertTrue(user.groups.filter(name='Sucursal').exists())
        self.assertEqual(user.sucursal.area, self.area)

    def test_admin_puede_crear_usuario_consultor_desde_api_sin_zona(self):
        self.api_client.force_authenticate(user=self.report_admin)
        response = self.api_client.post(
            '/api/admin/usuarios/',
            {
                'username': 'consultor_api',
                'password': '123456',
                'rol': 'Consultor',
                'area': None,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='consultor_api')
        self.assertTrue(user.groups.filter(name='Consultor').exists())
        self.assertFalse(hasattr(user, 'sucursal'))
        self.assertFalse(hasattr(user, 'tecnico'))

    def test_admin_puede_crear_zona_desde_api(self):
        self.api_client.force_authenticate(user=self.report_admin)
        response = self.api_client.post(
            '/api/areas/',
            {'nombre': 'Zona Nueva'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Area.objects.filter(nombre='Zona Nueva').exists())

    def test_admin_puede_crear_ticket_para_otra_sucursal(self):
        sucursal_user = User.objects.create_user(username='sucursal_api_2', password='123456')
        sucursal_user.groups.add(self.sucursal_group)
        sucursal_2 = Sucursal.objects.create(
            user=sucursal_user,
            nombre='Sucursal Norte',
            area=self.area,
        )

        self.api_client.force_authenticate(user=self.report_admin)
        response = self.api_client.post(
            '/api/tickets/',
            {
                'titulo': 'Ticket creado por admin',
                'descripcion': 'Validacion de alta administrativa',
                'prioridad': 'B',
                'sucursal': sucursal_2.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['sucursal'], sucursal_2.id)
        self.assertEqual(response.data['tecnico'], self.tecnico.id)

    def test_consultor_puede_ver_tickets_globales_sin_modificar(self):
        ticket = Ticket.objects.create(
            titulo='Consulta global',
            descripcion='Visible para consultor',
            prioridad='B',
            sucursal=self.sucursal,
        )
        consultor = User.objects.create_user(username='consultor1', password='123456')
        consultor.groups.add(self.consultor_group)

        self.api_client.force_authenticate(user=consultor)
        list_response = self.api_client.get('/api/tickets/')
        update_response = self.api_client.patch(
            f'/api/tickets/{ticket.id}/',
            {'estado': 'realizado', 'comentario_tecnico': 'No deberia modificar'},
            format='json',
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(update_response.status_code, 403)

    def test_reporte_comparativo_mensual_para_admin(self):
        Ticket.objects.create(
            titulo='Falla abril',
            descripcion='Caso abril',
            prioridad='B',
            sucursal=self.sucursal,
            fecha_inicio=timezone.make_aware(timezone.datetime(2026, 4, 10, 9, 0)),
        )
        Ticket.objects.create(
            titulo='Falla agosto',
            descripcion='Caso agosto',
            prioridad='C',
            sucursal=self.sucursal,
            fecha_inicio=timezone.make_aware(timezone.datetime(2026, 8, 12, 10, 0)),
        )

        self.api_client.force_authenticate(user=self.report_admin)
        response = self.api_client.get('/api/reportes/resumen/?base_month=4&base_year=2026&compare_month=8&compare_year=2026')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['modo'], 'comparativo_mensual')
        self.assertEqual(response.data['base']['label'], '04/2026')
        self.assertEqual(response.data['comparacion']['label'], '08/2026')
