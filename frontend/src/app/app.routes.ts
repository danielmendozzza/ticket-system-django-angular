import { Routes } from '@angular/router';
import { LoginComponent } from './pages/login/login';

export const routes: Routes = [
  { path: '', component: LoginComponent },
  { path: 'login', component: LoginComponent },
  {
    path: 'tickets',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'lista' },
  },
  {
    path: 'tickets/nuevo',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'nuevo' },
  },
  {
    path: 'tickets/alertas',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'alertas' },
  },
  {
    path: 'tickets/reportes',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'reportes' },
  },
  { path: '**', redirectTo: 'login' },
];
