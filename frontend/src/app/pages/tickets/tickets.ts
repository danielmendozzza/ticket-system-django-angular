import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TicketService } from '../../services/ticket';

@Component({
  selector: 'app-tickets',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tickets.html',
  styleUrls: ['./tickets.scss'],
})
export class Tickets implements OnInit {

  tickets: any[] = [];
constructor(private ticketService: TicketService) {}
ngOnInit() {
  this.ticketService.getTickets().subscribe({
    next: (res) => {
      this.tickets = res;
      console.log('RESPUESTA BACKEND:', this.tickets);
    }
  });
}
}