import { Component } from '@angular/core';
import { CardModule } from 'primeng/card';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-excursions',
  standalone: true,
  imports: [CardModule, TranslateModule],
  templateUrl: './excursions.component.html',
})
export class ExcursionsComponent {}
