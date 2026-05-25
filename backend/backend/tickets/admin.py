from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django import forms
from django.http import HttpResponse

from .excel_export import build_tickets_workbook
from .models import Area, Sucursal, Tecnico, Ticket, TicketAlerta


class SistemaUserCreationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('Tecnico', 'Tecnico'),
        ('Sucursal', 'Sucursal'),
        ('Consultor', 'Consultor'),
    )

    rol = forms.ChoiceField(choices=ROLE_CHOICES, label='Rol')
    area = forms.ModelChoiceField(queryset=Area.objects.order_by('nombre'), label='Zona', required=False)
    nombre_sucursal = forms.CharField(
        label='Nombre de sucursal',
        required=False,
        help_text='Solo se usa cuando el rol es Sucursal. Si queda vacio se usa el usuario.',
    )
    direccion = forms.CharField(label='Dirección', required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        area = cleaned_data.get('area')

        if rol in ('Tecnico', 'Sucursal') and not area:
            self.add_error('area', 'Selecciona una zona para este rol.')

        if rol == 'Tecnico' and area and Tecnico.objects.filter(area=area).exists():
            self.add_error('area', 'Esta zona ya tiene un técnico asignado.')

        return cleaned_data


admin.site.unregister(User)


@admin.register(User)
class SistemaUserAdmin(UserAdmin):
    add_form = SistemaUserCreationForm
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'password1',
                    'password2',
                    'rol',
                    'area',
                    'nombre_sucursal',
                    'direccion',
                ),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if change or not isinstance(form, SistemaUserCreationForm):
            return

        rol = form.cleaned_data['rol']
        area = form.cleaned_data['area']
        group, _ = Group.objects.get_or_create(name=rol)
        obj.groups.add(group)

        if rol == 'Tecnico':
            Tecnico.objects.create(user=obj, area=area)
            return

        if rol == 'Consultor':
            return

        Sucursal.objects.create(
            user=obj,
            nombre=form.cleaned_data.get('nombre_sucursal') or obj.username,
            direccion=form.cleaned_data.get('direccion') or '',
            area=area,
        )


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'zona', 'user')
    list_filter = ('area',)
    search_fields = ('nombre', 'direccion', 'user__username')

    @admin.display(ordering='area__nombre', description='Zona')
    def zona(self, obj):
        return obj.area


@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ('user', 'zona')
    list_filter = ('area',)
    search_fields = ('user__username', 'area__nombre')

    @admin.display(ordering='area__nombre', description='Zona exclusiva')
    def zona(self, obj):
        return obj.area


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
