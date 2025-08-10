import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { RippleModule } from 'primeng/ripple';

@Component({
  selector: 'app-welcome',
  standalone: true,
  imports: [RouterLink, ButtonModule, CardModule, RippleModule],
  templateUrl: './welcome.component.html',
})
export class WelcomeComponent {}
