from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from .models import Ticket, usuario_es_admin, usuario_es_tecnico
from .permissions import TicketPermission
from .serializers import (
    TicketAdminUpdateSerializer,
    TicketCreateSerializer,
    TicketSerializer,
    TicketUpdateSerializer,
)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related('sucursal', 'sucursal__area', 'tecnico', 'tecnico__user')
    serializer_class = TicketSerializer
    permission_classes = [TicketPermission]

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer

        if self.action in ('update', 'partial_update'):
            if usuario_es_admin(self.request.user):
                return TicketAdminUpdateSerializer
            return TicketUpdateSerializer

        return TicketSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = self.queryset.all()

        if usuario_es_admin(user):
            return queryset

        # tecnico que vea solo sus tickets
        if usuario_es_tecnico(user):
            return queryset.filter(tecnico__user=user)

        if user.groups.filter(name="Sucursal").exists():
            return queryset.filter(sucursal__user=user)

        return Ticket.objects.none()

    def perform_create(self, serializer):
        sucursal = getattr(self.request.user, 'sucursal', None)
        if sucursal is None:
            raise ValidationError('El usuario autenticado no tiene una sucursal asociada.')

        tecnico = Ticket.seleccionar_tecnico_para_sucursal(sucursal)
        if tecnico is None:
            raise ValidationError(
                'No hay tecnicos activos disponibles para el area de esta sucursal.'
            )

        serializer.save(sucursal=sucursal, tecnico=tecnico)
