import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Ticket {
  id: number;
  titulo: string;
  descripcion: string;
  equipo: string | null;
  prioridad: 'A' | 'B' | 'C';
  estado: 'pendiente' | 'realizado';
  sucursal: number;
  sucursal_nombre: string;
  tecnico: number | null;
  tecnico_nombre: string | null;
  area_nombre: string;
  fecha_creacion: string;
  fecha_inicio: string;
  fecha_limite: string | null;
  fecha_conclusion: string | null;
  comentario_tecnico: string | null;
  esta_vencido: boolean;
  estado_alerta: 'en_tiempo' | 'por_vencer' | 'vencido' | 'resuelto' | 'sin_limite';
}

export interface TicketPayload {
  titulo: string;
  descripcion: string;
  equipo?: string;
  prioridad: 'A' | 'B' | 'C';
}

export interface TicketUpdatePayload {
  estado: 'pendiente' | 'realizado';
  comentario_tecnico: string;
}

export interface TicketAdminUpdatePayload {
  titulo?: string;
  descripcion?: string;
  equipo?: string;
  prioridad?: 'A' | 'B' | 'C';
  estado?: 'pendiente' | 'realizado';
  tecnico?: number | null;
  fecha_inicio?: string | null;
  fecha_limite?: string | null;
  fecha_conclusion?: string | null;
  comentario_tecnico?: string;
}

export interface ReportSummary {
  label: string;
  desde: string;
  hasta: string;
  total_tickets: number;
  tickets_vencidos: number;
  tecnico_con_mas_incidencias_resueltas: {
    tecnico__user__username: string;
    total: number;
  } | null;
  tecnico_con_menos_incidencias: {
    tecnico__user__username: string;
    total: number;
    resueltos: number;
    pendientes: number;
  } | null;
  sucursales_con_mas_incidencias: Array<{
    sucursal__nombre: string;
    total: number;
  }>;
  ranking_tecnicos: Array<{
    tecnico__user__username: string | null;
    total: number;
    resueltos: number;
    pendientes: number;
  }>;
}

export interface ReporteResumen extends ReportSummary {
  modo: 'rango_meses';
  periodo_meses: number;
}

export interface ReporteComparativoMensual {
  modo: 'comparativo_mensual';
  base: ReportSummary;
  comparacion: ReportSummary | null;
}

export interface TicketAlerta {
  id: number;
  ticket: number;
  ticket_titulo: string;
  ticket_prioridad: 'A' | 'B' | 'C';
  ticket_estado: 'pendiente' | 'realizado';
  tipo: 'por_vencer' | 'vencido';
  mensaje: string;
  leida: boolean;
  fecha_generada: string;
  fecha_leida: string | null;
  fecha_limite: string | null;
}

export interface Area {
  id: number;
  nombre: string;
}

export interface AdminUser {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_active: boolean;
  rol: 'Admin' | 'Consultor' | 'Tecnico' | 'Sucursal' | 'SinRol';
  area: number | null;
  zona: string | null;
  nombre_sucursal: string;
  direccion: string;
}

export interface AdminUserPayload {
  username: string;
  password?: string;
  rol: 'Consultor' | 'Tecnico' | 'Sucursal';
  area: number | null;
  first_name?: string;
  last_name?: string;
  email?: string;
  is_active?: boolean;
  nombre_sucursal?: string;
  direccion?: string;
}

@Injectable({
  providedIn: 'root',
})
export class TicketService {
  private api = 'http://127.0.0.1:8000/api/tickets/';
  private reportApi = 'http://127.0.0.1:8000/api/reportes/resumen/';
  private alertsApi = 'http://127.0.0.1:8000/api/alertas/';
  private areasApi = 'http://127.0.0.1:8000/api/areas/';
  private adminUsersApi = 'http://127.0.0.1:8000/api/admin/usuarios/';

  constructor(private http: HttpClient) {}

  getTickets(): Observable<Ticket[]> {
    return this.http.get<Ticket[]>(this.api);
  }

  createTicket(payload: TicketPayload): Observable<Ticket> {
    return this.http.post<Ticket>(this.api, payload);
  }

  updateTicket(id: number, payload: TicketUpdatePayload | TicketAdminUpdatePayload): Observable<Ticket> {
    return this.http.patch<Ticket>(`${this.api}${id}/`, payload);
  }

  getResumenReportes(meses: 3 | 6 | 12): Observable<ReporteResumen> {
    return this.http.get<ReporteResumen>(`${this.reportApi}?meses=${meses}`);
  }

  getComparativoMensual(
    baseMonth: number,
    baseYear: number,
    compareMonth?: number,
    compareYear?: number
  ): Observable<ReporteComparativoMensual> {
    let query = `${this.reportApi}?base_month=${baseMonth}&base_year=${baseYear}`;
    if (compareMonth && compareYear) {
      query += `&compare_month=${compareMonth}&compare_year=${compareYear}`;
    }
    return this.http.get<ReporteComparativoMensual>(query);
  }

  getAlertas(): Observable<TicketAlerta[]> {
    return this.http.get<TicketAlerta[]>(this.alertsApi);
  }

  marcarAlertaLeida(id: number): Observable<TicketAlerta> {
    return this.http.post<TicketAlerta>(`${this.alertsApi}${id}/marcar-leida/`, {});
  }

  getAreas(): Observable<Area[]> {
    return this.http.get<Area[]>(this.areasApi);
  }

  getAdminUsers(): Observable<AdminUser[]> {
    return this.http.get<AdminUser[]>(this.adminUsersApi);
  }

  createAdminUser(payload: AdminUserPayload): Observable<AdminUser> {
    return this.http.post<AdminUser>(this.adminUsersApi, payload);
  }

  updateAdminUser(id: number, payload: AdminUserPayload): Observable<AdminUser> {
    return this.http.patch<AdminUser>(`${this.adminUsersApi}${id}/`, payload);
  }

  deleteAdminUser(id: number): Observable<void> {
    return this.http.delete<void>(`${this.adminUsersApi}${id}/`);
  }
}
