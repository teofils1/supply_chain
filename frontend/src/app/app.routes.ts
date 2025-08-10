import { Routes } from '@angular/router';
import { ButtonDemo } from './button-demo';
import { WelcomeComponent } from './features/welcome/welcome.component';
import { LoginComponent } from './features/login/login.component';
import { authGuard } from './shared/auth.guard';

export const routes: Routes = [
  { path: '', component: WelcomeComponent, canActivate: [authGuard] },
  { path: 'login', component: LoginComponent },
  { path: 'demo', component: ButtonDemo },
  { path: '**', redirectTo: '' },
];
