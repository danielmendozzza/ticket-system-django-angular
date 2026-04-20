import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';

import { TicketService } from './ticket';

describe('TicketService', () => {
  let service: TicketService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient()],
    });
    service = TestBed.inject(TicketService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
