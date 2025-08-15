import { Component } from '@angular/core';
import { CardModule } from 'primeng/card';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CardModule, TranslateModule],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent {}
