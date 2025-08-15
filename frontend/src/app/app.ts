import { Component, signal, inject } from '@angular/core';
import {
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { ToolbarModule } from 'primeng/toolbar';
import { ButtonModule } from 'primeng/button';
import { MenuModule } from 'primeng/menu';
import { MenuItem } from 'primeng/api';
import { AuthService } from './shared/auth.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    ToolbarModule,
    ButtonModule,
    MenuModule,
    TranslateModule,
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly title = signal('frontend');
  protected auth = inject(AuthService);
  private router = inject(Router);
  private translate = inject(TranslateService);

  // Drawer state: collapsed vs expanded and hover expansion
  collapsed = signal(false);
  hovering = signal(false);
  get isExpanded() {
    return !this.collapsed() || this.hovering();
  }

  // Persistent sidebar now; no toggle needed
  userMenuModel: MenuItem[] = [];

  // Persistent sidebar now; no toggle needed
  toggleDrawer() {
    this.collapsed.update((v) => !v);
  }

  setLang(lang: 'en' | 'ro') {
    localStorage.setItem('app.language', lang);
    this.translate.use(lang);
    this.buildUserMenu();
  }

  goDashboard() {
    this.router.navigateByUrl('/dashboard');
  }

  logout() {
    this.auth.logout();
  }

  constructor() {
    const saved = (localStorage.getItem('app.language') as 'en' | 'ro') || 'en';
    this.translate.setDefaultLang('en');
    this.translate.use(saved);
    this.buildUserMenu();
    this.translate.onLangChange.subscribe(() => this.buildUserMenu());
  }

  private buildUserMenu() {
    this.userMenuModel = [
      {
        label: this.translate.instant('user.dashboard'),
        icon: 'pi pi-user',
        command: () => this.goDashboard(),
      },
      {
        label: this.translate.instant('user.language'),
        icon: 'pi pi-globe',
        items: [
          {
            label: this.translate.instant('user.lang.en'),
            command: () => this.setLang('en'),
          },
          {
            label: this.translate.instant('user.lang.ro'),
            command: () => this.setLang('ro'),
          },
        ],
      },
      { separator: true },
      {
        label: this.translate.instant('user.logout'),
        icon: 'pi pi-sign-out',
        command: () => this.logout(),
      },
    ];
  }
}
