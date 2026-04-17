import { Routes } from '@angular/router';
import { LoginComponent } from './pages/login/login';

export const routes: Routes = [
  { path: '', component: LoginComponent },
  { path: 'login', component: LoginComponent },
    // 🔥 NUEVO
  { path: 'tickets', loadComponent: () => import('./pages/tickets/tickets').then(m => m.Tickets) }
];
