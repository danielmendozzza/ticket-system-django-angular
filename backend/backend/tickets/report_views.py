from datetime import timedelta

from django.http import HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from .excel_export import build_ticket_report_workbook
from .models import Sucursal, Tecnico, Ticket
from .permissions_reports import SoloUsuarioAdminReportesPermission


class ReporteResumenAPIView(APIView):
    permission_classes = [SoloUsuarioAdminReportesPermission]

    def _build_summary(self, tickets, label, desde, hasta):
        tickets_vencidos = tickets.filter(
            estado='pendiente',
            fecha_limite__lt=timezone.now(),
        ).count()

        sucursales = list(
            tickets.values('sucursal__nombre')
            .annotate(total=Count('id'))
            .order_by('-total', 'sucursal__nombre')[:5]
        )
        tecnicos_resueltos = list(
            tickets.filter(estado='realizado')
            .values('tecnico__user__username')
            .annotate(total=Count('id'))
            .order_by('-total', 'tecnico__user__username')
        )
        tecnicos_totales = list(
            tickets.values('tecnico__user__username')
            .annotate(
                total=Count('id'),
                resueltos=Count('id', filter=Q(estado='realizado')),
                pendientes=Count('id', filter=Q(estado='pendiente')),
            )
            .order_by('total', 'tecnico__user__username')
        )

        return {
            'label': label,
            'desde': desde,
            'hasta': hasta,
            'total_tickets': tickets.count(),
            'tickets_vencidos': tickets_vencidos,
            'sucursales_con_mas_incidencias': sucursales,
            'tecnico_con_mas_incidencias_resueltas': tecnicos_resueltos[0] if tecnicos_resueltos else None,
            'tecnico_con_menos_incidencias': tecnicos_totales[0] if tecnicos_totales else None,
            'ranking_tecnicos': tecnicos_totales,
        }

    def _month_range(self, year, month):
        start = timezone.datetime(year=year, month=month, day=1, tzinfo=timezone.get_current_timezone())
        if month == 12:
            end = timezone.datetime(year=year + 1, month=1, day=1, tzinfo=timezone.get_current_timezone())
        else:
            end = timezone.datetime(year=year, month=month + 1, day=1, tzinfo=timezone.get_current_timezone())
        return start, end

    def get(self, request):
        base_month = request.query_params.get('base_month')
        base_year = request.query_params.get('base_year')
        compare_month = request.query_params.get('compare_month')
        compare_year = request.query_params.get('compare_year')
        if base_month and base_year:
            try:
                base_month = int(base_month)
                base_year = int(base_year)
                if base_month < 1 or base_month > 12:
                    raise ValueError
            except ValueError:
                return Response({'detail': 'Mes o año base inválido.'}, status=400)

            base_desde, base_hasta = self._month_range(base_year, base_month)
            base_tickets = Ticket.objects.filter(fecha_inicio__gte=base_desde, fecha_inicio__lt=base_hasta)
            base_summary = self._build_summary(
                base_tickets,
                f'{base_month:02d}/{base_year}',
                base_desde,
                base_hasta,
            )

            compare_summary = None
            if compare_month and compare_year:
                try:
                    compare_month = int(compare_month)
                    compare_year = int(compare_year)
                    if compare_month < 1 or compare_month > 12:
                        raise ValueError
                except ValueError:
                    return Response({'detail': 'Mes o año de comparación inválido.'}, status=400)

                compare_desde, compare_hasta = self._month_range(compare_year, compare_month)
                compare_tickets = Ticket.objects.filter(
                    fecha_inicio__gte=compare_desde,
                    fecha_inicio__lt=compare_hasta,
                )
                compare_summary = self._build_summary(
                    compare_tickets,
                    f'{compare_month:02d}/{compare_year}',
                    compare_desde,
                    compare_hasta,
                )

            return Response(
                {
                    'modo': 'comparativo_mensual',
                    'base': base_summary,
                    'comparacion': compare_summary,
                }
            )

        meses = request.query_params.get('meses', '3')
        try:
            meses = int(meses)
        except ValueError:
            meses = 3

        if meses not in (3, 6, 12):
            meses = 3

        desde = timezone.now() - timedelta(days=30 * meses)
        tickets = Ticket.objects.filter(fecha_inicio__gte=desde)
        summary = self._build_summary(tickets, f'Ultimos {meses} meses', desde, timezone.now())
        summary['periodo_meses'] = meses
        summary['modo'] = 'rango_meses'
        return Response(summary)


class ReporteTicketsExcelAPIView(APIView):
    permission_classes = [SoloUsuarioAdminReportesPermission]

    def _month_start(self, year, month):
        return timezone.datetime(year=year, month=month, day=1, tzinfo=timezone.get_current_timezone())

    def _month_end(self, year, month):
        if month == 12:
            return self._month_start(year + 1, 1)
        return self._month_start(year, month + 1)

    def _parse_month_year(self, request, month_key, year_key, label):
        try:
            month = int(request.query_params.get(month_key, ''))
            year = int(request.query_params.get(year_key, ''))
            if month < 1 or month > 12:
                raise ValueError
        except ValueError:
            return None, Response({'detail': f'Mes o ano {label} invalido.'}, status=400)

        return (month, year), None

    def get(self, request):
        desde_data, error = self._parse_month_year(request, 'desde_mes', 'desde_anio', 'desde')
        if error is not None:
            return error

        hasta_data, error = self._parse_month_year(request, 'hasta_mes', 'hasta_anio', 'hasta')
        if error is not None:
            return error

        desde_mes, desde_anio = desde_data
        hasta_mes, hasta_anio = hasta_data
        desde = self._month_start(desde_anio, desde_mes)
        hasta = self._month_end(hasta_anio, hasta_mes)

        if desde >= hasta:
            return Response({'detail': 'El rango de fechas no es valido.'}, status=400)

        tickets = Ticket.objects.select_related(
            'sucursal',
            'sucursal__area',
            'tecnico',
            'tecnico__user',
        ).filter(fecha_inicio__gte=desde, fecha_inicio__lt=hasta)

        filtros = {}
        tecnico_id = request.query_params.get('tecnico')
        if tecnico_id:
            try:
                tecnico = Tecnico.objects.select_related('user').get(pk=int(tecnico_id))
            except (ValueError, Tecnico.DoesNotExist):
                return Response({'detail': 'Tecnico invalido.'}, status=400)
            tickets = tickets.filter(tecnico_id=tecnico.id)
            filtros['tecnico'] = tecnico.user.username

        sucursal_id = request.query_params.get('sucursal')
        if sucursal_id:
            try:
                sucursal = Sucursal.objects.get(pk=int(sucursal_id))
            except (ValueError, Sucursal.DoesNotExist):
                return Response({'detail': 'Sucursal invalida.'}, status=400)
            tickets = tickets.filter(sucursal_id=sucursal.id)
            filtros['sucursal'] = sucursal.nombre

        estado = request.query_params.get('estado')
        if estado:
            if estado not in ('pendiente', 'realizado'):
                return Response({'detail': 'Estado invalido.'}, status=400)
            tickets = tickets.filter(estado=estado)
            filtros['estado'] = 'Pendiente' if estado == 'pendiente' else 'Realizado'

        tickets = tickets.order_by('fecha_inicio', 'id')
        workbook = build_ticket_report_workbook(tickets, desde, hasta, filtros)
        filename = f'tickets_{desde_mes:02d}-{desde_anio}_a_{hasta_mes:02d}-{hasta_anio}.xlsx'
        response = HttpResponse(
            workbook,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
