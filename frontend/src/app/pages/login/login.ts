import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class LoginComponent {
  username = '';
  password = '';
  error = '';
  entrando = false;

  constructor(private auth: AuthService, private router: Router) {}

  login() {
    if (this.entrando) {
      return;
    }

    this.error = '';
    this.entrando = true;
    this.auth.login(this.username, this.password).subscribe({
      next: (res) => {
        this.auth.saveSession(res);
        setTimeout(() => {
          this.router.navigate(['/tickets']);
        }, 420);
      },
      error: () => {
        this.error = 'Usuario o contraseña incorrectos.';
        this.entrando = false;
      }
    });
  }
}
