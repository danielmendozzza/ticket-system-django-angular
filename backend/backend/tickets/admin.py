from django.contrib import admin
from .models import Area, Tecnico, Ticket, Sucursal

admin.site.register(Area)
admin.site.register(Tecnico)
admin.site.register(Sucursal)
admin.site.register(Ticket)