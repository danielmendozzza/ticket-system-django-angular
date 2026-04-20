from django.core.management.base import BaseCommand

from tickets.alerts import generar_alertas_tickets


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        resultado = generar_alertas_tickets()
        self.stdout.write(
            self.style.SUCCESS(
                f"Alertas verificadas. Tickets evaluados: {resultado['procesados']}. Alertas nuevas: {resultado['creadas']}."
            )
        )
