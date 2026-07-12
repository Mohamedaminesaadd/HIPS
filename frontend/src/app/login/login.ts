import { Component } from '@angular/core';

import { BrandPanel } from './components/brand-panel/brand-panel'
import { LoginForm } from './components/login-form/login-form';
import { LoginCredentials } from './models/login-credentials.model';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [BrandPanel, LoginForm],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  onLogin(credentials: LoginCredentials): void {
    // TODO: brancher sur AuthService (FastAPI backend HPIS)
    console.log('login', credentials);
  }

  onGoogleLogin(): void {
    // TODO: flux OAuth Google
    console.log('google login');
  }

  onForgotPassword(): void {
    // TODO: navigation vers /mot-de-passe-oublie
    console.log('forgot password');
  }

  onCreateAccount(): void {
    // TODO: navigation vers /inscription
    console.log('create account');
  }
}