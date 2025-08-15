import { Component } from '@angular/core';
import { CardModule } from 'primeng/card';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-trace',
  standalone: true,
  imports: [CardModule, TranslateModule],
  templateUrl: './trace.component.html',
})
export class TraceComponent {}
