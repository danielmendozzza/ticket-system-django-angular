from datetime import timedelta

from django.utils import timezone

from .models import Ticket, TicketAlerta


def construir_mensaje_alerta(ticket: Ticket, tipo: str) -> str:
    limite = ticket.fecha_limite.strftime('%d/%m/%Y %H:%M') if ticket.fecha_limite else 'sin fecha'
    if tipo == 'vencido':
        return f'Ticket vencido: {ticket.titulo}. Fecha limite: {limite}.'
    return f'Ticket por vencer: {ticket.titulo}. Fecha limite: {limite}.'


def generar_alertas_tickets():
    ahora = timezone.now()
    ventana = ahora + timedelta(minutes=30)

    tickets = Ticket.objects.select_related('tecnico', 'tecnico__user').filter(
        estado='pendiente',
        tecnico__isnull=False,
        fecha_limite__isnull=False,
        fecha_limite__lte=ventana,
    )

    creadas = 0
    for ticket in tickets:
        tipo = 'vencido' if ticket.fecha_limite <= ahora else 'por_vencer'
        _, created = TicketAlerta.objects.update_or_create(
            ticket=ticket,
            tipo=tipo,
            defaults={
                'tecnico': ticket.tecnico,
                'mensaje': construir_mensaje_alerta(ticket, tipo),
                'leida': False,
                'fecha_leida': None,
            },
        )
        if created:
            creadas += 1

    return {
        'procesados': tickets.count(),
        'creadas': creadas,
    }
