import { Routes } from '@angular/router';
import { WelcomeComponent } from './features/welcome/welcome.component';
import { LoginComponent } from './features/login/login.component';
import { ProductsComponent } from './features/products/products.component';
import { ProductDetailComponent } from './features/products/product-detail.component';
import { BatchesComponent } from './features/batches/batches.component';
import { BatchDetailComponent } from './features/batches/batch-detail.component';
import { PacksComponent } from './features/packs/packs.component';
import { PackDetailComponent } from './features/packs/pack-detail.component';
import { ShipmentsComponent } from './features/shipments/shipments.component';
import { ShipmentDetailComponent } from './features/shipments/shipment-detail.component';
import { EventsComponent } from './features/events/events.component';
import { EventDetailComponent } from './features/events/event-detail.component';
import { TraceComponent } from './features/trace/trace.component';
import { DevicesComponent } from './features/devices/devices.component';
import { ExcursionsComponent } from './features/excursions/excursions.component';
import { UsersComponent } from './features/users/users.component';
import { authGuard } from './shared/auth.guard';

export const routes: Routes = [
  { path: '', component: WelcomeComponent, canActivate: [authGuard] },
  { path: 'users', component: UsersComponent, canActivate: [authGuard] },
  { path: 'products', component: ProductsComponent, canActivate: [authGuard] },
  {
    path: 'products/new',
    component: ProductDetailComponent,
    canActivate: [authGuard],
  },
  {
    path: 'products/:id',
    component: ProductDetailComponent,
    canActivate: [authGuard],
  },
  {
    path: 'products/:id/edit',
    component: ProductDetailComponent,
    canActivate: [authGuard],
  },
  { path: 'batches', component: BatchesComponent, canActivate: [authGuard] },
  {
    path: 'batches/new',
    component: BatchDetailComponent,
    canActivate: [authGuard],
  },
  {
    path: 'batches/:id',
    component: BatchDetailComponent,
    canActivate: [authGuard],
  },
  {
    path: 'batches/:id/edit',
    component: BatchDetailComponent,
    canActivate: [authGuard],
  },
  { path: 'packs', component: PacksComponent, canActivate: [authGuard] },
  {
    path: 'packs/new',
    component: PackDetailComponent,
    canActivate: [authGuard],
  },
  {
    path: 'packs/:id',
    component: PackDetailComponent,
    canActivate: [authGuard],
  },
  {
    path: 'packs/:id/edit',
    component: PackDetailComponent,
    canActivate: [authGuard],
  },
  {
    path: 'shipments',
    component: ShipmentsComponent,
    canActivate: [authGuard],
  },
  {
    path: 'shipments/new',
    component: ShipmentDetailComponent,
    canActivate: [authGuard],
  },
  {
    path: 'shipments/:id',
    component: ShipmentDetailComponent,
    canActivate: [authGuard],
  },
  {
    path: 'shipments/:id/edit',
    component: ShipmentDetailComponent,
    canActivate: [authGuard],
  },
  { path: 'events', component: EventsComponent, canActivate: [authGuard] },
  {
    path: 'events/new',
    component: EventDetailComponent,
    canActivate: [authGuard],
  },
  {
    path: 'events/:id',
    component: EventDetailComponent,
    canActivate: [authGuard],
  },
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
