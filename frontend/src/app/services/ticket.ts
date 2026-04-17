import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class TicketService {

  private api = 'http://127.0.0.1:8000/api/tickets/';

  constructor(private http: HttpClient) {}
getTickets() {
  const token = localStorage.getItem('token');

  if (!token) {
    throw new Error('No token found in localStorage');
  }

  return this.http.get<any>(this.api, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
}
}