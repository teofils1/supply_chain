import { Component } from '@angular/core';
import { CardModule } from 'primeng/card';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-products',
  standalone: true,
  imports: [CardModule, TranslateModule],
  templateUrl: './products.component.html',
})
export class ProductsComponent {}
