from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from .models import Ticket
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
            if self.request.user.username == 'admin':
                return TicketAdminUpdateSerializer
            return TicketUpdateSerializer

        return TicketSerializer

    def get_queryset(self):
        user = self.request.user

        if user.username == 'admin':
            return Ticket.objects.all()

        # tecnico que vea solo sus tickets
        if user.groups.filter(name="Tecnico").exists():
            return Ticket.objects.filter(tecnico__user=user)

        if user.groups.filter(name="Sucursal").exists():
            return Ticket.objects.filter(sucursal__user=user)

        return Ticket.objects.none()

    def perform_create(self, serializer):
        sucursal = getattr(self.request.user, 'sucursal', None)
        if sucursal is None:
            raise ValidationError('El usuario autenticado no tiene una sucursal asociada.')
        serializer.save(sucursal=sucursal)
