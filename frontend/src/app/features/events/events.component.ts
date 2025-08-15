import { Component } from '@angular/core';
import { CardModule } from 'primeng/card';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-events',
  standalone: true,
  imports: [CardModule, TranslateModule],
  templateUrl: './events.component.html',
})
export class EventsComponent {}
