from django.contrib import admin
from django.http import HttpResponse

from .excel_export import build_tickets_workbook
from .models import Area, Sucursal, Tecnico, Ticket, TicketAlerta


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'area', 'user')
    list_filter = ('area',)
    search_fields = ('nombre', 'direccion', 'user__username')


@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ('user', 'area')
    list_filter = ('area',)
    search_fields = ('user__username', 'area__nombre')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'titulo',
        'prioridad',
        'estado',
        'sucursal',
        'tecnico',
        'fecha_inicio',
        'fecha_limite',
    )
    list_filter = ('prioridad', 'estado', 'sucursal__area', 'tecnico')
    search_fields = ('titulo', 'descripcion', 'equipo', 'sucursal__nombre', 'tecnico__user__username')
    actions = ('exportar_tickets_excel',)

    @admin.action(description='Exportar tickets seleccionados a Excel')
    def exportar_tickets_excel(self, request, queryset):
        tickets = queryset.select_related('sucursal', 'sucursal__area', 'tecnico', 'tecnico__user').order_by('-fecha_inicio')
        workbook = build_tickets_workbook(tickets)
        response = HttpResponse(
            workbook,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename="tickets_admin.xlsx"'
        return response


@admin.register(TicketAlerta)
class TicketAlertaAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'tecnico', 'tipo', 'leida', 'fecha_generada')
    list_filter = ('tipo', 'leida')
    search_fields = ('ticket__titulo', 'tecnico__user__username', 'mensaje')
