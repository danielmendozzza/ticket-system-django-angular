import { Routes } from '@angular/router';
import { LoginComponent } from './pages/login/login';

export const routes: Routes = [
  { path: '', component: LoginComponent },
  { path: 'login', component: LoginComponent },
  {
    path: 'tickets',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'inicio' },
  },
  {
    path: 'tickets/lista',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'lista' },
  },
  {
    path: 'tickets/nuevo',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'nuevo' },
  },
  {
    path: 'tickets/usuarios',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'configuraciones', seccion: 'usuarios' },
  },
  {
    path: 'tickets/configuraciones',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'configuraciones', seccion: 'usuarios' },
  },
  {
    path: 'tickets/alertas',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'alertas' },
  },
  {
    path: 'tickets/resumen',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'resumen' },
  },
  {
    path: 'tickets/reportes',
    loadComponent: () => import('./pages/tickets/tickets').then((m) => m.Tickets),
    data: { vista: 'comparativo' },
  },
  { path: '**', redirectTo: 'login' },
];
