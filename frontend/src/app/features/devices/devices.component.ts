import { Component } from '@angular/core';
import { CardModule } from 'primeng/card';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-devices',
  standalone: true,
  imports: [CardModule, TranslateModule],
  templateUrl: './devices.component.html',
})
export class DevicesComponent {}
