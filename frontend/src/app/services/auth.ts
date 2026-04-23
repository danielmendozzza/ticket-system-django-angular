import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { getApiBase } from './api-base';

export interface LoginResponse {
  access: string;
  refresh: string;
  role: string;
  username: string;
}

export interface RefreshResponse {
  access: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiBase = getApiBase();
  private api = `${this.apiBase}/token/`;
  private refreshApi = `${this.apiBase}/token/refresh/`;

  constructor(private http: HttpClient) {}

  login(username: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(this.api, {
      username,
      password
    });
  }

  refreshAccessToken(refresh: string): Observable<RefreshResponse> {
    return this.http.post<RefreshResponse>(this.refreshApi, { refresh });
  }

  saveSession(session: LoginResponse) {
    localStorage.setItem('token', session.access);
    localStorage.setItem('refresh', session.refresh);
    localStorage.setItem('role', session.role);
    localStorage.setItem('username', session.username);
  }

  saveToken(token: string) {
    localStorage.setItem('token', token);
  }

  getToken() {
    return localStorage.getItem('token');
  }

  getRole() {
    return localStorage.getItem('role');
  }

  getRefreshToken() {
    return localStorage.getItem('refresh');
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh');
    localStorage.removeItem('role');
    localStorage.removeItem('username');
  }
}
