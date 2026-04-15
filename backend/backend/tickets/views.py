from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Ticket
from .serializers import TicketSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()  #  ESTO SOLUCIONA 
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # tecnico que vea solo sus tickets
        if user.groups.filter(name="Tecnico").exists():
            return Ticket.objects.filter(tecnico__user=user)

        # SUCURSAL → (temporal)
        if user.groups.filter(name="Sucursal").exists():
             return Ticket.objects.filter(sucursal__user=user) # solo puede ver sus tickets
        return Ticket.objects.none()