from rest_framework import serializers

from .models import TicketAlerta


class TicketAlertaSerializer(serializers.ModelSerializer):
    ticket_titulo = serializers.CharField(source='ticket.titulo', read_only=True)
    ticket_prioridad = serializers.CharField(source='ticket.prioridad', read_only=True)
    ticket_estado = serializers.CharField(source='ticket.estado', read_only=True)
    fecha_limite = serializers.DateTimeField(source='ticket.fecha_limite', read_only=True)

    class Meta:
        model = TicketAlerta
        fields = (
            'id',
            'ticket',
            'ticket_titulo',
            'ticket_prioridad',
            'ticket_estado',
            'tipo',
            'mensaje',
            'leida',
            'fecha_generada',
            'fecha_leida',
            'fecha_limite',
        )
        read_only_fields = fields
