import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, NgForm } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import {
  AdminUser,
  AdminUserPayload,
  Area,
  AreaPayload,
  ReportSummary,
  ReporteComparativoMensual,
  ReporteResumen,
  SucursalOption,
  Ticket,
  TicketAdminCreatePayload,
  TicketAdminUpdatePayload,
  TicketAlerta,
  TicketExcelReportParams,
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
  private readonly flashMessageKey = 'tickets.flash.success';
  private messageTimer: ReturnType<typeof setTimeout> | null = null;
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
  guardandoUsuario = false;
  guardandoZona = false;
  cargandoAlertas = false;
  cargandoUsuarios = false;
  cargandoSucursales = false;
  exportandoTickets = false;
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
  filtroZona = '';
  filtroTecnico = '';
  nuevoTicket = {
    titulo: '',
    descripcion: '',
    equipo: '',
    prioridad: 'B' as 'A' | 'B' | 'C',
  };
  nuevoUsuario: AdminUserPayload = {
    username: '',
    password: '',
    rol: 'Sucursal',
    area: null,
    first_name: '',
    last_name: '',
    email: '',
    nombre_sucursal: '',
    direccion: '',
  };
  nuevaZona: AreaPayload = {
    nombre: '',
  };
  nuevoTicketAdmin: TicketAdminCreatePayload = {
    titulo: '',
    descripcion: '',
    equipo: '',
    prioridad: 'B',
    sucursal: 0,
  };
  areas: Area[] = [];
  sucursales: SucursalOption[] = [];
  usuariosAdmin: AdminUser[] = [];
  usuarioEdiciones: Record<number, AdminUserPayload> = {};
  usuariosAbiertos: Record<number, boolean> = {};
  guardandoUsuarioId: number | null = null;
  eliminandoUsuarioId: number | null = null;
  actualizaciones: Record<number, TicketUpdatePayload> = {};
  adminActualizaciones: Record<number, TicketAdminUpdatePayload> = {};
  evidenciasSeleccionadas: Record<number, File | null> = {};
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
  exportDesdeMes = 1;
  exportDesdeAnio = new Date().getFullYear();
  exportHastaMes = new Date().getMonth() + 1;
  exportHastaAnio = new Date().getFullYear();
  exportTecnico: number | null = null;
  exportSucursal: number | null = null;
  exportEstado: '' | 'pendiente' | 'realizado' = '';
  panelesAbiertos: Record<number, boolean> = {};
  vista: 'inicio' | 'lista' | 'nuevo' | 'usuarios' | 'alertas' | 'resumen' | 'comparativo' | 'configuraciones' = 'inicio';
  configuracionActiva: 'zonas' | 'usuarios' | 'tickets' = 'usuarios';
  temaAdminOscuro = localStorage.getItem('adminTheme') === 'dark';

  ngOnInit() {
    if (!this.authService.getToken()) {
      this.router.navigate(['/login']);
      return;
    }

    this.restaurarMensajeFlash();

    this.route.data.subscribe((data) => {
      this.vista = (data['vista'] ?? 'inicio') as 'inicio' | 'lista' | 'nuevo' | 'usuarios' | 'alertas' | 'resumen' | 'comparativo' | 'configuraciones';
      if (this.vista === 'configuraciones') {
        this.configuracionActiva = (data['seccion'] ?? 'usuarios') as 'zonas' | 'usuarios' | 'tickets';
        this.cargarDatosConfiguracion();
      }
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
      if (this.esAdmin()) {
        this.cargarDatosConfiguracion();
      }
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
        this.mostrarError(this.extraerMensajeError(err, 'No se pudieron cargar los tickets.'), false);
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
        this.mostrarError('No se pudo cargar el resumen del periodo.', false);
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
          this.mostrarError('No se pudo cargar el comparativo mensual.', false);
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
        this.mostrarError('No se pudieron cargar las alertas.', false);
        this.cargandoAlertas = false;
        this.actualizarPantalla();
      },
    });
  }

  cargarAreas() {
    this.ticketService.getAreas().subscribe({
      next: (res) => {
        this.areas = res;
        if (!this.nuevoUsuario.area && this.areas.length > 0) {
          this.nuevoUsuario.area = this.areas[0].id;
        }
        if (!this.nuevoTicketAdmin.sucursal && this.sucursales.length > 0) {
          this.nuevoTicketAdmin.sucursal = this.sucursales[0].id;
        }
        this.actualizarPantalla();
      },
      error: () => {
        this.mostrarError('No se pudieron cargar las zonas.', false);
        this.actualizarPantalla();
      },
    });
  }

  cargarSucursales() {
    if (!this.esAdmin()) {
      this.sucursales = [];
      return;
    }

    this.cargandoSucursales = true;
    this.ticketService.getSucursales().subscribe({
      next: (res) => {
        this.sucursales = res;
        if (!this.nuevoTicketAdmin.sucursal && this.sucursales.length > 0) {
          this.nuevoTicketAdmin.sucursal = this.sucursales[0].id;
        }
        this.cargandoSucursales = false;
        this.actualizarPantalla();
      },
      error: () => {
        this.mostrarError('No se pudieron cargar las sucursales.', false);
        this.cargandoSucursales = false;
        this.actualizarPantalla();
      },
    });
  }

  cargarDatosConfiguracion() {
    if (!this.esAdmin()) {
      return;
    }

    this.cargarAreas();
    this.cargarUsuariosAdmin();
    this.cargarSucursales();
  }

  cargarUsuariosAdmin() {
    if (!this.esAdmin()) {
      this.usuariosAdmin = [];
      return;
    }

    this.cargandoUsuarios = true;
    this.ticketService.getAdminUsers().subscribe({
      next: (res) => {
        this.usuariosAdmin = res;
        this.usuarioEdiciones = res.reduce((acc, usuario) => {
          if (this.usuarioEditable(usuario)) {
            acc[usuario.id] = {
              username: usuario.username,
              password: '',
              rol: usuario.rol,
              area: usuario.area,
              first_name: usuario.first_name,
              last_name: usuario.last_name,
              email: usuario.email,
              is_active: usuario.is_active,
              nombre_sucursal: usuario.nombre_sucursal,
              direccion: usuario.direccion,
            };
          }
          return acc;
        }, {} as Record<number, AdminUserPayload>);
        this.cargandoUsuarios = false;
        this.actualizarPantalla();
      },
      error: () => {
        this.mostrarError('No se pudieron cargar los usuarios.', false);
        this.cargandoUsuarios = false;
        this.actualizarPantalla();
      },
    });
  }

  crearTicket(form?: NgForm) {
    this.guardando = true;
    this.limpiarMensajes();

    this.ticketService.createTicket(this.nuevoTicket).subscribe({
      next: (ticketCreado) => {
        this.aplicarTicketEnEstadoLocal(ticketCreado);
        this.nuevoTicket = {
          titulo: '',
          descripcion: '',
          equipo: '',
          prioridad: 'B',
        };
        form?.resetForm(this.nuevoTicket);
        this.guardando = false;
        this.guardarMensajeFlash('Ticket generado correctamente.');
        this.router.navigate(['/tickets/lista']);
        if (this.puedeVerReportes()) {
          this.cargarResumen();
          this.cargarComparativoMensual();
        }
        this.actualizarPantalla();
      },
      error: (err) => {
        this.mostrarError(this.extraerMensajeError(err, 'No se pudo crear el ticket.'));
        this.guardando = false;
        this.actualizarPantalla();
      },
    });
  }

  crearUsuario(form?: NgForm) {
    if (!this.nuevoUsuario.area && this.nuevoUsuario.rol !== 'Consultor') {
      this.mostrarError('Selecciona una zona para el usuario.');
      return;
    }

    this.guardandoUsuario = true;
    this.limpiarMensajes();

    const payload: AdminUserPayload = {
      ...this.nuevoUsuario,
      area: this.nuevoUsuario.rol === 'Consultor' ? null : this.nuevoUsuario.area,
      nombre_sucursal: this.nuevoUsuario.rol === 'Sucursal' ? this.nuevoUsuario.nombre_sucursal : '',
      direccion: this.nuevoUsuario.rol === 'Sucursal' ? this.nuevoUsuario.direccion : '',
    };

    this.ticketService.createAdminUser(payload).subscribe({
      next: () => {
        const area = this.nuevoUsuario.area;
        this.nuevoUsuario = {
          username: '',
          password: '',
          rol: 'Sucursal',
          area,
          first_name: '',
          last_name: '',
          email: '',
          nombre_sucursal: '',
          direccion: '',
        };
        form?.resetForm(this.nuevoUsuario);
        this.guardandoUsuario = false;
        this.mostrarExito('Usuario creado correctamente.');
        this.cargarUsuariosAdmin();
        this.actualizarPantalla();
      },
      error: (err) => {
        this.mostrarError(this.extraerMensajeError(err, 'No se pudo crear el usuario.'));
        this.guardandoUsuario = false;
        this.actualizarPantalla();
      },
    });
  }

  crearZona(form?: NgForm) {
    if (!this.nuevaZona.nombre.trim()) {
      this.mostrarError('Escribe un nombre para la zona.');
      return;
    }

    this.guardandoZona = true;
    this.limpiarMensajes();
    this.ticketService.createArea(this.nuevaZona).subscribe({
      next: (zonaCreada) => {
        this.areas = [...this.areas, zonaCreada].sort((a, b) => a.nombre.localeCompare(b.nombre));
        this.nuevaZona = { nombre: '' };
        form?.resetForm(this.nuevaZona);
        if (!this.nuevoUsuario.area) {
          this.nuevoUsuario.area = zonaCreada.id;
        }
        this.guardandoZona = false;
        this.mostrarExito('Zona creada correctamente.');
        this.actualizarPantalla();
      },
      error: (err) => {
        this.guardandoZona = false;
        this.mostrarError(this.extraerMensajeError(err, 'No se pudo crear la zona.'));
        this.actualizarPantalla();
      },
    });
  }

  crearTicketAdmin(form?: NgForm) {
    if (!this.nuevoTicketAdmin.sucursal) {
      this.mostrarError('Selecciona una sucursal para el ticket.');
      return;
    }

    this.guardando = true;
    this.limpiarMensajes();
    this.ticketService.createAdminTicket(this.nuevoTicketAdmin).subscribe({
      next: (ticketCreado) => {
        this.aplicarTicketEnEstadoLocal(ticketCreado);
        this.nuevoTicketAdmin = {
          titulo: '',
          descripcion: '',
          equipo: '',
          prioridad: 'B',
          sucursal: this.sucursales[0]?.id ?? 0,
        };
        form?.resetForm(this.nuevoTicketAdmin);
        this.guardando = false;
        this.mostrarExito('Ticket administrativo generado correctamente.');
        if (this.puedeVerReportes()) {
          this.cargarResumen();
          this.cargarComparativoMensual();
        }
        this.router.navigate(['/tickets/lista']);
        this.actualizarPantalla();
      },
      error: (err) => {
        this.guardando = false;
        this.mostrarError(this.extraerMensajeError(err, 'No se pudo crear el ticket administrativo.'));
        this.actualizarPantalla();
      },
    });
  }

  guardarUsuario(usuarioId: number) {
    const payload = this.usuarioEdiciones[usuarioId];
    if (!payload) {
      return;
    }

    if (!payload.area && payload.rol !== 'Consultor') {
      this.mostrarError('Selecciona una zona para el usuario.');
      return;
    }

    this.guardandoUsuarioId = usuarioId;
    this.limpiarMensajes();

    this.ticketService.updateAdminUser(usuarioId, this.construirPayloadUsuario(payload)).subscribe({
      next: () => {
        this.guardandoUsuarioId = null;
        this.mostrarExito('Usuario actualizado correctamente.');
        this.cargarUsuariosAdmin();
        this.actualizarPantalla();
      },
      error: (err) => {
        this.mostrarError(this.extraerMensajeError(err, 'No se pudo actualizar el usuario.'));
        this.guardandoUsuarioId = null;
        this.actualizarPantalla();
      },
    });
  }

  borrarUsuario(usuario: AdminUser) {
    if (!window.confirm(`Borrar el usuario ${usuario.username}?`)) {
      return;
    }

    this.eliminandoUsuarioId = usuario.id;
    this.limpiarMensajes();

    this.ticketService.deleteAdminUser(usuario.id).subscribe({
      next: () => {
        this.eliminandoUsuarioId = null;
        this.mostrarExito('Usuario borrado correctamente.');
        this.cargarUsuariosAdmin();
        this.actualizarPantalla();
      },
      error: (err) => {
        this.mostrarError(this.extraerMensajeError(err, 'No se pudo borrar el usuario.'));
        this.eliminandoUsuarioId = null;
        this.actualizarPantalla();
      },
    });
  }

  guardarTicket(ticketId: number) {
    const payload = this.esAdmin() ? this.construirPayloadAdmin(ticketId) : this.construirPayloadTecnico(ticketId);
    if (!payload) {
      return;
    }

    this.guardando = true;
    this.limpiarMensajes();

    this.ticketService.updateTicket(ticketId, payload).subscribe({
      next: (ticketActualizado) => {
        this.aplicarTicketEnEstadoLocal(ticketActualizado);
        this.evidenciasSeleccionadas[ticketId] = null;
        this.guardando = false;
        this.mostrarExito('Ticket actualizado correctamente.');
        if (this.puedeVerReportes()) {
          this.cargarResumen();
          this.cargarComparativoMensual();
        }
        if (this.esTecnico()) {
          this.cargarAlertas();
        }
        this.actualizarPantalla();
      },
      error: (err) => {
        this.mostrarError(this.extraerMensajeError(err, 'No se pudo actualizar el ticket.'));
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

  exportarTicketsExcel() {
    if (!this.puedeVerReportes() || this.exportandoTickets) {
      return;
    }

    if (this.exportDesdeAnio > this.exportHastaAnio || (
      this.exportDesdeAnio === this.exportHastaAnio && this.exportDesdeMes > this.exportHastaMes
    )) {
      this.mostrarError('Selecciona un rango de meses valido.');
      return;
    }

    this.exportandoTickets = true;
    this.ticketService.exportTicketsExcel(this.filtrosExportacionExcel()).subscribe({
      next: (blob) => {
        const filename = `tickets_${this.exportDesdeMes}-${this.exportDesdeAnio}_a_${this.exportHastaMes}-${this.exportHastaAnio}.xlsx`;
        this.descargarBlob(blob, filename);
        this.exportandoTickets = false;
        this.actualizarPantalla();
      },
      error: (err) => {
        this.exportandoTickets = false;
        this.mostrarError(this.extraerMensajeError(err, 'No se pudo exportar el reporte de tickets.'));
        this.actualizarPantalla();
      },
    });
  }

  toggleTicketPanel(ticketId: number) {
    this.panelesAbiertos[ticketId] = !this.panelesAbiertos[ticketId];
  }

  ticketPanelAbierto(ticketId: number) {
    return !!this.panelesAbiertos[ticketId];
  }

  toggleUsuarioPanel(usuarioId: number) {
    this.usuariosAbiertos[usuarioId] = !this.usuariosAbiertos[usuarioId];
  }

  usuarioPanelAbierto(usuarioId: number) {
    return !!this.usuariosAbiertos[usuarioId];
  }

  cerrarSesion() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  alternarTemaAdmin() {
    this.temaAdminOscuro = !this.temaAdminOscuro;
    localStorage.setItem('adminTheme', this.temaAdminOscuro ? 'dark' : 'light');
  }

  estadoLabel(estado: Ticket['estado']) {
    return estado === 'realizado' ? 'Realizado' : 'Pendiente';
  }

  estadoClass(estado: Ticket['estado']) {
    return `status-${estado}`;
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
    return this.tickets.filter((ticket) => ticket.prioridad === prioridad && ticket.estado !== 'realizado').length;
  }

  ticketsPorEstado(estado: Ticket['estado']) {
    return this.tickets.filter((ticket) => ticket.estado === estado).length;
  }

  ticketsPendientes() {
    return this.ticketsPorEstado('pendiente');
  }

  ticketsVencidos() {
    return this.tickets.filter((ticket) => ticket.estado !== 'realizado' && ticket.estado_alerta === 'vencido').length;
  }

  cumplimientoGeneral() {
    if (this.tickets.length === 0) {
      return 0;
    }

    return Math.round((this.ticketsPorEstado('realizado') / this.tickets.length) * 100);
  }

  slaLabel(prioridad: Ticket['prioridad']) {
    return {
      A: '5 horas',
      B: '15 horas',
      C: '24 horas',
    }[prioridad];
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
      const coincideZona = !this.filtroZona || ticket.area_nombre === this.filtroZona;
      const coincideTecnico = !this.filtroTecnico || (ticket.tecnico_nombre ?? 'Sin asignar') === this.filtroTecnico;

      return coincideTexto && coincidePrioridad && coincideEstado && coincideAlerta && coincideZona && coincideTecnico;
    });
  }

  get zonasTickets() {
    return Array.from(new Set(this.tickets.map((ticket) => ticket.area_nombre).filter(Boolean))).sort();
  }

  get tecnicosTickets() {
    return Array.from(
      new Set(this.tickets.map((ticket) => ticket.tecnico_nombre || 'Sin asignar'))
    ).sort();
  }

  get tecnicosParaExportar() {
    const tecnicos = new Map<number, string>();
    this.tickets.forEach((ticket) => {
      if (ticket.tecnico && ticket.tecnico_nombre) {
        tecnicos.set(ticket.tecnico, ticket.tecnico_nombre);
      }
    });
    return Array.from(tecnicos.entries())
      .map(([id, nombre]) => ({ id, nombre }))
      .sort((a, b) => a.nombre.localeCompare(b.nombre));
  }

  get sucursalesParaExportar() {
    const sucursales = new Map<number, string>();
    this.tickets.forEach((ticket) => {
      if (ticket.sucursal && ticket.sucursal_nombre) {
        sucursales.set(ticket.sucursal, ticket.sucursal_nombre);
      }
    });
    return Array.from(sucursales.entries())
      .map(([id, nombre]) => ({ id, nombre }))
      .sort((a, b) => a.nombre.localeCompare(b.nombre));
  }

  limpiarFiltros() {
    this.busqueda = '';
    this.filtroPrioridad = '';
    this.filtroEstado = '';
    this.filtroAlerta = '';
    this.filtroZona = '';
    this.filtroTecnico = '';
  }

  hayFiltrosActivos() {
    return !!(
      this.busqueda.trim() ||
      this.filtroPrioridad ||
      this.filtroEstado ||
      this.filtroAlerta ||
      this.filtroZona ||
      this.filtroTecnico
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

  seleccionarEvidencia(ticketId: number, event: Event) {
    const input = event.target as HTMLInputElement;
    this.evidenciasSeleccionadas[ticketId] = input.files?.[0] ?? null;
  }

  borrarEvidencia(ticketId: number) {
    if (!this.esAdmin()) {
      return;
    }

    this.guardando = true;
    this.limpiarMensajes();

    this.ticketService.borrarEvidenciaTicket(ticketId).subscribe({
      next: (ticketActualizado) => {
        this.aplicarTicketEnEstadoLocal(ticketActualizado);
        this.guardando = false;
        this.mostrarExito('Evidencia borrada correctamente.');
        this.actualizarPantalla();
      },
      error: (err) => {
        this.guardando = false;
        this.mostrarError(this.extraerMensajeError(err, 'No se pudo borrar la evidencia.'));
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

  esConsultor() {
    return this.role === 'Consultor';
  }

  puedeUsarTemaOscuro() {
    return this.esAdmin() || this.esConsultor();
  }

  puedeVerReportes() {
    return this.esAdmin() || this.esConsultor();
  }

  usuarioEditable(usuario: AdminUser): usuario is AdminUser & { rol: 'Consultor' | 'Tecnico' | 'Sucursal' } {
    return usuario.rol === 'Consultor' || usuario.rol === 'Tecnico' || usuario.rol === 'Sucursal';
  }

  mostrarInicio() {
    return this.vista === 'inicio';
  }

  mostrarLista() {
    return this.vista === 'lista';
  }

  mostrarCreacion() {
    return this.vista === 'nuevo';
  }

  mostrarUsuarios() {
    return this.vista === 'usuarios';
  }

  mostrarConfiguraciones() {
    return this.vista === 'configuraciones';
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

  activarConfiguracion(seccion: 'zonas' | 'usuarios' | 'tickets') {
    this.configuracionActiva = seccion;
  }

  mostrarConfigZonas() {
    return this.mostrarConfiguraciones() && this.configuracionActiva === 'zonas';
  }

  mostrarConfigUsuarios() {
    return this.mostrarConfiguraciones() && this.configuracionActiva === 'usuarios';
  }

  mostrarConfigTickets() {
    return this.mostrarConfiguraciones() && this.configuracionActiva === 'tickets';
  }

  resumenComparativoTarjeta(summary: ReportSummary | null) {
    if (!summary) {
      return [];
    }

    return [
      { label: 'Total tickets', value: summary.total_tickets },
      { label: 'Tickets vencidos', value: summary.tickets_vencidos },
      {
        label: 'Tecnico top',
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

  private construirPayloadUsuario(payload: AdminUserPayload): AdminUserPayload {
    return {
      ...payload,
      password: payload.password || undefined,
      area: payload.rol === 'Consultor' ? null : payload.area,
      nombre_sucursal: payload.rol === 'Sucursal' ? payload.nombre_sucursal : '',
      direccion: payload.rol === 'Sucursal' ? payload.direccion : '',
    };
  }

  private filtrosExportacionExcel(): TicketExcelReportParams {
    return {
      desde_mes: this.exportDesdeMes,
      desde_anio: this.exportDesdeAnio,
      hasta_mes: this.exportHastaMes,
      hasta_anio: this.exportHastaAnio,
      tecnico: this.exportTecnico,
      sucursal: this.exportSucursal,
      estado: this.exportEstado,
    };
  }

  private construirPayloadTecnico(ticketId: number): TicketUpdatePayload | FormData | null {
    const payload = this.actualizaciones[ticketId];
    if (!payload) {
      return null;
    }

    const evidencia = this.evidenciasSeleccionadas[ticketId];
    if (!evidencia) {
      return payload;
    }

    const formData = new FormData();
    formData.append('estado', payload.estado);
    formData.append('comentario_tecnico', payload.comentario_tecnico ?? '');
    formData.append('evidencia_cierre', evidencia);
    return formData;
  }

  private descargarBlob(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  private aplicarTicketEnEstadoLocal(ticketActualizado: Ticket) {
    this.tickets = [ticketActualizado, ...this.tickets.filter((ticket) => ticket.id !== ticketActualizado.id)];
    this.actualizaciones[ticketActualizado.id] = {
      estado: ticketActualizado.estado,
      comentario_tecnico: ticketActualizado.comentario_tecnico ?? '',
    };
    this.adminActualizaciones[ticketActualizado.id] = {
      titulo: ticketActualizado.titulo,
      descripcion: ticketActualizado.descripcion,
      equipo: ticketActualizado.equipo ?? '',
      prioridad: ticketActualizado.prioridad,
      estado: ticketActualizado.estado,
      tecnico: ticketActualizado.tecnico,
      fecha_inicio: this.toDatetimeLocal(ticketActualizado.fecha_inicio),
      fecha_limite: this.toDatetimeLocal(ticketActualizado.fecha_limite),
      fecha_conclusion: this.toDatetimeLocal(ticketActualizado.fecha_conclusion),
      comentario_tecnico: ticketActualizado.comentario_tecnico ?? '',
    };
    this.prepararVistaInicial();
  }

  private guardarMensajeFlash(message: string) {
    sessionStorage.setItem(this.flashMessageKey, message);
  }

  private restaurarMensajeFlash() {
    const message = sessionStorage.getItem(this.flashMessageKey);
    if (!message) {
      return;
    }

    this.mostrarExito(message);
    sessionStorage.removeItem(this.flashMessageKey);
  }

  private limpiarMensajes() {
    this.error = '';
    this.exito = '';
    if (this.messageTimer) {
      clearTimeout(this.messageTimer);
      this.messageTimer = null;
    }
  }

  private mostrarExito(message: string, autoOcultar = true) {
    this.limpiarMensajes();
    this.exito = message;
    if (autoOcultar) {
      this.messageTimer = setTimeout(() => {
        this.exito = '';
        this.actualizarPantalla();
      }, 4000);
    }
  }

  private mostrarError(message: string, autoOcultar = true) {
    this.limpiarMensajes();
    this.error = message;
    if (autoOcultar) {
      this.messageTimer = setTimeout(() => {
        this.error = '';
        this.actualizarPantalla();
      }, 5000);
    }
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
    const fieldErrors = err?.error && typeof err.error === 'object'
      ? Object.values(err.error).filter((value) => Array.isArray(value)).flat()
      : [];

    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(nonFieldErrors) && nonFieldErrors.length > 0) {
      return nonFieldErrors.join(' ');
    }

    if (fieldErrors.length > 0) {
      return fieldErrors.join(' ');
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
