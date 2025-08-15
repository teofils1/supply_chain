import { Routes } from '@angular/router';
import { WelcomeComponent } from './features/welcome/welcome.component';
import { LoginComponent } from './features/login/login.component';
import { ProductsComponent } from './features/products/products.component';
import { BatchesComponent } from './features/batches/batches.component';
import { PacksComponent } from './features/packs/packs.component';
import { ShipmentsComponent } from './features/shipments/shipments.component';
import { EventsComponent } from './features/events/events.component';
import { TraceComponent } from './features/trace/trace.component';
import { DevicesComponent } from './features/devices/devices.component';
import { ExcursionsComponent } from './features/excursions/excursions.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { authGuard } from './shared/auth.guard';

export const routes: Routes = [
  { path: '', component: WelcomeComponent, canActivate: [authGuard] },
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [authGuard],
  },
  { path: 'products', component: ProductsComponent, canActivate: [authGuard] },
  { path: 'batches', component: BatchesComponent, canActivate: [authGuard] },
  { path: 'packs', component: PacksComponent, canActivate: [authGuard] },
  {
    path: 'shipments',
    component: ShipmentsComponent,
    canActivate: [authGuard],
  },
  { path: 'events', component: EventsComponent, canActivate: [authGuard] },
  {
    path: 'trace/:serial',
    component: TraceComponent,
    canActivate: [authGuard],
  },
  { path: 'devices', component: DevicesComponent, canActivate: [authGuard] },
  {
    path: 'excursions',
    component: ExcursionsComponent,
    canActivate: [authGuard],
  },
  { path: 'login', component: LoginComponent },
  { path: '**', redirectTo: '' },
];
