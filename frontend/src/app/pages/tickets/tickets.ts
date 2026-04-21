import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, NgForm } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import {
  ReportSummary,
  ReporteComparativoMensual,
  ReporteResumen,
  Ticket,
  TicketAdminUpdatePayload,
  TicketAlerta,
  TicketService,
  TicketUpdatePayload,
} from '../../services/ticket';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-tickets',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './tickets.html',
  styleUrl: './tickets.scss',
})
export class Tickets implements OnInit {
  private readonly ticketService = inject(TicketService);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);

  tickets: Ticket[] = [];
  role = this.authService.getRole() ?? 'SinRol';
  username = localStorage.getItem('username') ?? '';
  cargando = false;
  guardando = false;
  cargandoAlertas = false;
  error = '';
  exito = '';
  mesesReporte: 3 | 6 | 12 = 3;
  resumen: ReporteResumen | null = null;
  comparativoMensual: ReporteComparativoMensual | null = null;
  alertas: TicketAlerta[] = [];
  busqueda = '';
  filtroPrioridad = '';
  filtroEstado = '';
  filtroAlerta = '';
  nuevoTicket = {
    titulo: '',
    descripcion: '',
    equipo: '',
    prioridad: 'B' as 'A' | 'B' | 'C',
  };
  actualizaciones: Record<number, TicketUpdatePayload> = {};
  adminActualizaciones: Record<number, TicketAdminUpdatePayload> = {};
  mesesDisponibles = [
    { value: 1, label: 'Enero' },
    { value: 2, label: 'Febrero' },
    { value: 3, label: 'Marzo' },
    { value: 4, label: 'Abril' },
    { value: 5, label: 'Mayo' },
    { value: 6, label: 'Junio' },
    { value: 7, label: 'Julio' },
    { value: 8, label: 'Agosto' },
    { value: 9, label: 'Septiembre' },
    { value: 10, label: 'Octubre' },
    { value: 11, label: 'Noviembre' },
    { value: 12, label: 'Diciembre' },
  ];
  aniosDisponibles = [2025, 2026, 2027, 2028];
  comparadorMesBase = 4;
  comparadorAnioBase = 2026;
  comparadorMesComparacion = 8;
  comparadorAnioComparacion = 2026;
  panelesAbiertos: Record<number, boolean> = {};
  vista: 'lista' | 'nuevo' | 'alertas' | 'resumen' | 'comparativo' = 'lista';

  ngOnInit() {
    if (!this.authService.getToken()) {
      this.router.navigate(['/login']);
      return;
    }

    this.route.data.subscribe((data) => {
      this.vista = (data['vista'] ?? 'lista') as 'lista' | 'nuevo' | 'alertas' | 'resumen' | 'comparativo';
      if (this.vista === 'alertas') {
        this.cargarAlertas();
      }
      if (this.vista === 'resumen') {
        this.cargarResumen();
      }
      if (this.vista === 'comparativo') {
        this.cargarComparativoMensual();
      }
      this.actualizarPantalla();
    });

    this.limpiarFiltros();
    this.cargarTickets();
    if (this.puedeVerReportes()) {
      this.cargarResumen();
      this.cargarComparativoMensual();
    }
    if (this.esTecnico()) {
      this.cargarAlertas();
    }
  }

  cargarTickets() {
    this.cargando = true;
    this.error = '';

    this.ticketService.getTickets().subscribe({
      next: (res) => {
        this.tickets = res;
        this.actualizaciones = this.tickets.reduce(
          (acc, ticket) => ({
            ...acc,
            [ticket.id]: {
              estado: ticket.estado,
              comentario_tecnico: ticket.comentario_tecnico ?? '',
            },
          }),
          {} as Record<number, TicketUpdatePayload>
        );
        this.adminActualizaciones = this.tickets.reduce(
          (acc, ticket) => ({
            ...acc,
            [ticket.id]: {
              titulo: ticket.titulo,
              descripcion: ticket.descripcion,
              equipo: ticket.equipo ?? '',
              prioridad: ticket.prioridad,
              estado: ticket.estado,
              tecnico: ticket.tecnico,
              fecha_inicio: this.toDatetimeLocal(ticket.fecha_inicio),
              fecha_limite: this.toDatetimeLocal(ticket.fecha_limite),
              fecha_conclusion: this.toDatetimeLocal(ticket.fecha_conclusion),
              comentario_tecnico: ticket.comentario_tecnico ?? '',
            },
          }),
          {} as Record<number, TicketAdminUpdatePayload>
        );
        this.prepararVistaInicial();
        this.cargando = false;
        if (this.esTecnico()) {
          this.cargarAlertas();
        }
        this.actualizarPantalla();
      },
      error: (err) => {
        this.error = this.extraerMensajeError(err, 'No se pudieron cargar los tickets.');
        this.cargando = false;
        this.actualizarPantalla();
      },
    });
  }

  cargarResumen() {
    if (!this.puedeVerReportes()) {
      this.resumen = null;
      return;
    }

    this.ticketService.getResumenReportes(this.mesesReporte).subscribe({
      next: (res) => {
        this.resumen = res;
        this.actualizarPantalla();
      },
      error: () => {
        this.error = 'No se pudo cargar el resumen del periodo.';
        this.actualizarPantalla();
      },
    });
  }

  cargarComparativoMensual() {
    if (!this.puedeVerReportes()) {
      this.comparativoMensual = null;
      return;
    }

    this.ticketService
      .getComparativoMensual(
        this.comparadorMesBase,
        this.comparadorAnioBase,
        this.comparadorMesComparacion,
        this.comparadorAnioComparacion
      )
      .subscribe({
        next: (res) => {
          this.comparativoMensual = res;
          this.actualizarPantalla();
        },
        error: () => {
          this.error = 'No se pudo cargar el comparativo mensual.';
          this.actualizarPantalla();
        },
      });
  }

  cargarAlertas() {
    if (!this.esTecnico()) {
      this.alertas = [];
      this.actualizarPantalla();
      return;
    }

    this.cargandoAlertas = true;
    this.actualizarPantalla();
    this.ticketService.getAlertas().subscribe({
      next: (res) => {
        this.alertas = res;
        this.cargandoAlertas = false;
        this.actualizarPantalla();
      },
      error: () => {
        this.error = 'No se pudieron cargar las alertas.';
        this.cargandoAlertas = false;
        this.actualizarPantalla();
      },
    });
  }

  crearTicket(form?: NgForm) {
    this.guardando = true;
    this.error = '';
    this.exito = '';

    this.ticketService.createTicket(this.nuevoTicket).subscribe({
      next: (ticketCreado) => {
        this.tickets = [ticketCreado, ...this.tickets.filter((ticket) => ticket.id !== ticketCreado.id)];
        this.nuevoTicket = {
          titulo: '',
          descripcion: '',
          equipo: '',
          prioridad: 'B',
        };
        form?.resetForm(this.nuevoTicket);
        this.guardando = false;
        this.exito = 'Ticket generado correctamente.';
        this.cargarTickets();
        this.router.navigate(['/tickets']);
        if (this.puedeVerReportes()) {
          this.cargarResumen();
          this.cargarComparativoMensual();
        }
        this.actualizarPantalla();
      },
      error: (err) => {
        this.error = this.extraerMensajeError(err, 'No se pudo crear el ticket.');
        this.guardando = false;
        this.actualizarPantalla();
      },
    });
  }

  guardarTicket(ticketId: number) {
    const payload = this.esAdmin() ? this.construirPayloadAdmin(ticketId) : this.actualizaciones[ticketId];
    if (!payload) {
      return;
    }

    this.guardando = true;
    this.error = '';
    this.exito = '';

    this.ticketService.updateTicket(ticketId, payload).subscribe({
      next: () => {
        this.guardando = false;
        this.exito = 'Ticket actualizado correctamente.';
        this.cargarTickets();
        if (this.puedeVerReportes()) {
          this.cargarResumen();
          this.cargarComparativoMensual();
        }
        this.cargarAlertas();
        this.actualizarPantalla();
      },
      error: (err) => {
        this.error = this.extraerMensajeError(err, 'No se pudo actualizar el ticket.');
        this.guardando = false;
        this.actualizarPantalla();
      },
    });
  }

  cambiarPeriodo(meses: 3 | 6 | 12) {
    this.mesesReporte = meses;
    this.cargarResumen();
  }

  aplicarComparativoMensual() {
    this.cargarComparativoMensual();
  }

  toggleTicketPanel(ticketId: number) {
    this.panelesAbiertos[ticketId] = !this.panelesAbiertos[ticketId];
  }

  ticketPanelAbierto(ticketId: number) {
    return !!this.panelesAbiertos[ticketId];
  }

  cerrarSesion() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  estadoLabel(estado: Ticket['estado']) {
    return estado === 'realizado' ? 'Realizado' : 'Pendiente';
  }

  prioridadLabel(prioridad: Ticket['prioridad']) {
    return {
      A: 'Alta',
      B: 'Media',
      C: 'Baja',
    }[prioridad];
  }

  alertaLabel(alerta: Ticket['estado_alerta']) {
    return {
      en_tiempo: 'En tiempo',
      por_vencer: 'Por vencer',
      vencido: 'Vencido',
      resuelto: 'Resuelto',
      sin_limite: 'Sin limite',
    }[alerta];
  }

  ticketsPorPrioridad(prioridad: Ticket['prioridad']) {
    return this.tickets.filter((ticket) => ticket.prioridad === prioridad).length;
  }

  ticketsPorEstado(estado: Ticket['estado']) {
    return this.tickets.filter((ticket) => ticket.estado === estado).length;
  }

  get ticketsFiltrados() {
    const texto = this.busqueda.trim().toLowerCase();

    return this.tickets.filter((ticket) => {
      const coincideTexto =
        !texto ||
        ticket.titulo.toLowerCase().includes(texto) ||
        ticket.descripcion.toLowerCase().includes(texto) ||
        (ticket.equipo ?? '').toLowerCase().includes(texto) ||
        ticket.sucursal_nombre.toLowerCase().includes(texto) ||
        (ticket.tecnico_nombre ?? '').toLowerCase().includes(texto);

      const coincidePrioridad = !this.filtroPrioridad || ticket.prioridad === this.filtroPrioridad;
      const coincideEstado = !this.filtroEstado || ticket.estado === this.filtroEstado;
      const coincideAlerta = !this.filtroAlerta || ticket.estado_alerta === this.filtroAlerta;

      return coincideTexto && coincidePrioridad && coincideEstado && coincideAlerta;
    });
  }

  limpiarFiltros() {
    this.busqueda = '';
    this.filtroPrioridad = '';
    this.filtroEstado = '';
    this.filtroAlerta = '';
  }

  hayFiltrosActivos() {
    return !!(
      this.busqueda.trim() ||
      this.filtroPrioridad ||
      this.filtroEstado ||
      this.filtroAlerta
    );
  }

  badgeClass(alerta: Ticket['estado_alerta'] | TicketAlerta['tipo']) {
    return `badge-${alerta}`;
  }

  prioridadClass(prioridad: Ticket['prioridad']) {
    return `priority-${prioridad.toLowerCase()}`;
  }

  tipoAlertaLabel(tipo: TicketAlerta['tipo']) {
    return tipo === 'vencido' ? 'Vencido' : 'Por vencer';
  }

  alertasNoLeidas() {
    return this.alertas.filter((alerta) => !alerta.leida);
  }

  marcarAlertaLeida(alertaId: number) {
    this.ticketService.marcarAlertaLeida(alertaId).subscribe({
      next: () => {
        this.alertas = this.alertas.map((alerta) =>
          alerta.id === alertaId
            ? {
                ...alerta,
                leida: true,
                fecha_leida: new Date().toISOString(),
              }
            : alerta
        );
        this.actualizarPantalla();
      },
    });
  }

  esTecnico() {
    return this.role === 'Tecnico';
  }

  esSucursal() {
    return this.role === 'Sucursal';
  }

  esAdmin() {
    return this.role === 'Admin' || this.username === 'admin';
  }

  puedeVerReportes() {
    return this.esAdmin();
  }

  mostrarLista() {
    return this.vista === 'lista';
  }

  mostrarCreacion() {
    return this.vista === 'nuevo';
  }

  mostrarAlertas() {
    return this.vista === 'alertas';
  }

  mostrarResumen() {
    return this.vista === 'resumen';
  }

  mostrarReportes() {
    return this.vista === 'comparativo';
  }

  resumenComparativoTarjeta(summary: ReportSummary | null) {
    if (!summary) {
      return [];
    }

    return [
      { label: 'Total tickets', value: summary.total_tickets },
      { label: 'Tickets vencidos', value: summary.tickets_vencidos },
      {
        label: 'Técnico top',
        value: summary.tecnico_con_mas_incidencias_resueltas?.tecnico__user__username || 'Sin datos',
      },
      {
        label: 'Menor carga',
        value: summary.tecnico_con_menos_incidencias?.tecnico__user__username || 'Sin datos',
      },
    ];
  }

  trackByTicket(_: number, ticket: Ticket) {
    return ticket.id;
  }

  private toDatetimeLocal(value: string | null) {
    if (!value) {
      return null;
    }
    return value.slice(0, 16);
  }

  private construirPayloadAdmin(ticketId: number): TicketAdminUpdatePayload | null {
    const payload = this.adminActualizaciones[ticketId];
    if (!payload) {
      return null;
    }

    return {
      ...payload,
      fecha_inicio: payload.fecha_inicio || undefined,
      fecha_limite: payload.fecha_limite || null,
      fecha_conclusion: payload.fecha_conclusion || null,
    };
  }

  private prepararVistaInicial() {
    if (this.tickets.length > 0 && this.ticketsFiltrados.length === 0) {
      this.limpiarFiltros();
    }

    if (this.esTecnico()) {
      this.panelesAbiertos = this.tickets.reduce((acc, ticket) => {
        acc[ticket.id] = ticket.estado === 'pendiente';
        return acc;
      }, {} as Record<number, boolean>);
    }
  }

  private extraerMensajeError(err: any, fallback: string) {
    const detail = err?.error?.detail;
    const nonFieldErrors = err?.error?.non_field_errors;

    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(nonFieldErrors) && nonFieldErrors.length > 0) {
      return nonFieldErrors.join(' ');
    }

    if (Array.isArray(err?.error) && err.error.length > 0) {
      return err.error.join(' ');
    }

    return fallback;
  }

  private actualizarPantalla() {
    this.cdr.detectChanges();
  }
}
