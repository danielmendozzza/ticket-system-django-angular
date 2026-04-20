from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .alert_serializers import TicketAlertaSerializer
from .alerts import generar_alertas_tickets
from .models import TicketAlerta


class TicketAlertaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TicketAlertaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        generar_alertas_tickets()
        user = self.request.user
        if user.groups.filter(name='Tecnico').exists():
            return TicketAlerta.objects.select_related('ticket', 'tecnico', 'tecnico__user').filter(
                tecnico__user=user
            )
        return TicketAlerta.objects.none()

    @action(detail=True, methods=['post'], url_path='marcar-leida')
    def marcar_leida(self, request, pk=None):
        alerta = self.get_object()
        alerta.marcar_leida()
        serializer = self.get_serializer(alerta)
        return Response(serializer.data, status=status.HTTP_200_OK)
