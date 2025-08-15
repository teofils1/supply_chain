import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { RippleModule } from 'primeng/ripple';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-welcome',
  standalone: true,
  imports: [
    RouterLink,
    ButtonModule,
    CardModule,
    RippleModule,
    TranslateModule,
  ],
  templateUrl: './welcome.component.html',
})
export class WelcomeComponent {}
