import { Component } from '@angular/core';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'button-demo',
  standalone: true,
  templateUrl: './button-demo.html',
  imports: [ButtonModule],
})
export class ButtonDemo {}
