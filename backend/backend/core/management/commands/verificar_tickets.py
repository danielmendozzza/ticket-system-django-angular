from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.models import Ticket

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        ahora = timezone.now()

        tickets = Ticket.objects.filter(
            estado='pendiente',
            fecha_limite__lte=ahora
        )

        if tickets.exists():
            for ticket in tickets:
                print(f"⚠️ Ticket vencido: {ticket.titulo}")
        else:
            print("✅ No hay tickets vencidos")   

  