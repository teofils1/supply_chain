import { Component, signal, inject, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { ToolbarModule } from 'primeng/toolbar';
import { ButtonModule } from 'primeng/button';
import { TieredMenuModule } from 'primeng/tieredmenu';
import { MenuItem } from 'primeng/api';
import { AuthService } from './shared/auth.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    ToolbarModule,
    ButtonModule,
    TieredMenuModule,
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

  goUsers() {
    this.router.navigateByUrl('/users');
  }

  logout() {
    this.auth.logout();
  }

  switchRole(newRole: string) {
    this.auth.switchRole(newRole).subscribe({
      next: () => {
        // Optionally show a success message or refresh data
        console.log(`Switched to ${newRole} role`);
      },
      error: (err) => {
        console.error('Failed to switch role:', err);
        // You could show an error toast here
      },
    });
  }

  constructor() {
    const saved = (localStorage.getItem('app.language') as 'en' | 'ro') || 'en';
    this.translate.setDefaultLang('en');
    this.translate.use(saved);
    this.buildUserMenu();
    this.translate.onLangChange.subscribe(() => this.buildUserMenu());

    // Initialize theme preference
    const themePref = localStorage.getItem('app.theme') || 'light';
    if (themePref === 'dark') {
      document.documentElement.classList.add('dark');
      this._dark.set(true);
    } else {
      document.documentElement.classList.remove('dark');
    }

    // Watch for user changes to rebuild menu
    effect(() => {
      // This effect will run whenever currentUser signal changes
      this.auth.currentUser();
      this.buildUserMenu();
    });
  }

  private buildUserMenu() {
    const currentUser = this.auth.currentUser();

    this.userMenuModel = [
      {
        label: this.translate.instant('user.users'),
        icon: 'pi pi-users',
        command: () => this.goUsers(),
      },
    ];

    // Add role switcher if user has multiple roles
    if (currentUser?.roles && currentUser.roles.length > 1) {
      const roleItems: MenuItem[] = currentUser.roles.map((role) => ({
        label: role,
        icon: currentUser.active_role === role ? 'pi pi-check' : '',
        command: () => {
          if (role !== currentUser.active_role) {
            this.switchRole(role);
          }
        },
      }));

      this.userMenuModel.push({
        label: this.translate.instant('user.switchRole'),
        icon: 'pi pi-user',
        items: roleItems,
      });
    }

    // Add current role display if available
    if (currentUser?.active_role) {
      this.userMenuModel.push({
        label: `${this.translate.instant('user.currentRole')}: ${
          currentUser.active_role
        }`,
        icon: 'pi pi-id-card',
        disabled: true,
      });
    }

    this.userMenuModel.push(
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
      }
    );
  }

  // Whether current route is the login page (hide sidebar & adjust layout)
  isLoginRoute(): boolean {
    return this.router.url.startsWith('/login');
  }

  // Theme toggling
  private _dark = signal(false);
  isDark() {
    return this._dark();
  }
  toggleTheme() {
    this._dark.update((v) => !v);
    const dark = this._dark();
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('app.theme', dark ? 'dark' : 'light');
  }
}
