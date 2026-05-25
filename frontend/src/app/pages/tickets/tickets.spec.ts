import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { Tickets } from './tickets';
import { TicketService } from '../../services/ticket';
import { AuthService } from '../../services/auth';
import { ActivatedRoute, Router } from '@angular/router';

describe('Tickets', () => {
  let component: Tickets;
  let fixture: ComponentFixture<Tickets>;

  beforeEach(async () => {
    const storageMock = {
      getItem: () => null,
      setItem: () => undefined,
      removeItem: () => undefined,
    };
    Object.defineProperty(globalThis, 'localStorage', {
      value: storageMock,
      configurable: true,
    });
    Object.defineProperty(globalThis, 'sessionStorage', {
      value: storageMock,
      configurable: true,
    });

    await TestBed.configureTestingModule({
      imports: [Tickets],
      providers: [
        {
          provide: TicketService,
          useValue: {
            getTickets: () => of([]),
            getAlertas: () => of([]),
            marcarAlertaLeida: () => of(null),
            getResumenReportes: () =>
              of({
                periodo_meses: 3,
                total_tickets: 0,
                tickets_vencidos: 0,
                tecnico_con_mas_incidencias_resueltas: null,
                tecnico_con_menos_incidencias: null,
                sucursales_con_mas_incidencias: [],
                ranking_tecnicos: [],
              }),
          },
        },
        {
          provide: AuthService,
          useValue: {
            getRole: () => 'Tecnico',
            getToken: () => 'token',
            logout: () => undefined,
          },
        },
        {
          provide: Router,
          useValue: {
            navigate: () => Promise.resolve(true),
          },
        },
        {
          provide: ActivatedRoute,
          useValue: {
            data: of({ vista: 'lista' }),
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Tickets);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
