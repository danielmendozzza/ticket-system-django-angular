import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule], // 👈 AQUÍ VA
  templateUrl: './login.html'
})
export class LoginComponent {

  username = '';
  password = '';

  constructor(private auth: AuthService, private router: Router) {}

 login() {
  this.auth.login(this.username, this.password).subscribe({
    next: (res) => {
      console.log(res);

      localStorage.setItem('token', res.access);
      localStorage.setItem('role', res.role);
      this.router.navigate(['/tickets']);
    },
    error: (err) => {
      console.log('ERROR:', err); // 👈 IMPORTANTE
      alert('Login incorrecto');
    }
  });
}
}