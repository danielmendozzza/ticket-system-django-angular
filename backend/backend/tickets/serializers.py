from rest_framework import serializers
from .models import Ticket, usuario_es_tecnico


class TicketSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    tecnico_nombre = serializers.CharField(source='tecnico.user.username', read_only=True)
    area_nombre = serializers.CharField(source='sucursal.area.nombre', read_only=True)
    esta_vencido = serializers.BooleanField(read_only=True)
    estado_alerta = serializers.CharField(read_only=True)

    class Meta:
        model = Ticket
        fields = (
            'id',
            'titulo',
            'descripcion',
            'equipo',
            'prioridad',
            'estado',
            'sucursal',
            'sucursal_nombre',
            'tecnico',
            'tecnico_nombre',
            'area_nombre',
            'fecha_creacion',
            'fecha_inicio',
            'fecha_limite',
            'fecha_conclusion',
            'comentario_tecnico',
            'esta_vencido',
            'estado_alerta',
        )
        read_only_fields = (
            'tecnico',
            'fecha_creacion',
            'fecha_limite',
            'fecha_conclusion',
            'esta_vencido',
            'estado_alerta',
            'sucursal_nombre',
            'tecnico_nombre',
            'area_nombre',
        )


class TicketCreateSerializer(TicketSerializer):
    class Meta(TicketSerializer.Meta):
        read_only_fields = TicketSerializer.Meta.read_only_fields + ('estado', 'sucursal')


class TicketUpdateSerializer(TicketSerializer):
    class Meta(TicketSerializer.Meta):
        read_only_fields = TicketSerializer.Meta.read_only_fields + (
            'titulo',
            'descripcion',
            'equipo',
            'prioridad',
            'sucursal',
            'fecha_inicio',
        )


class TicketAdminUpdateSerializer(TicketSerializer):
    def validate_tecnico(self, tecnico):
        if tecnico is not None and not usuario_es_tecnico(tecnico.user):
            raise serializers.ValidationError('Solo se pueden asignar usuarios con rol Tecnico.')
        return tecnico

    class Meta(TicketSerializer.Meta):
        read_only_fields = (
            'fecha_creacion',
            'esta_vencido',
            'estado_alerta',
            'sucursal_nombre',
            'tecnico_nombre',
            'area_nombre',
        )
