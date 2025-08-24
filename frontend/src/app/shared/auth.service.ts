import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';
import { Observable } from 'rxjs';

type Tokens = { access: string; refresh: string };

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  active_role?: string;
  roles?: string[];
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  private readonly storageKey = 'auth.tokens';
  private _tokens = signal<Tokens | null>(this.loadTokens());
  private _currentUser = signal<CurrentUser | null>(null);
  private _initialized = signal<boolean>(false);

  readonly isAuthenticated = computed(() => !!this._tokens());
  readonly currentUser = computed(() => this._currentUser());
  readonly initialized = computed(() => this._initialized());

  private loadTokens(): Tokens | null {
    const raw = localStorage.getItem(this.storageKey);
    if (!raw) return null;
    try {
      const tokens = JSON.parse(raw) as Tokens;
      // Basic validation - check if tokens have the expected structure
      if (!tokens.access || !tokens.refresh) {
        console.warn('Invalid token structure found, clearing storage');
        localStorage.removeItem(this.storageKey);
        return null;
      }
      return tokens;
    } catch {
      console.warn('Failed to parse stored tokens, clearing storage');
      localStorage.removeItem(this.storageKey);
      return null;
    }
  }

  private saveTokens(tokens: Tokens) {
    this._tokens.set(tokens);
    localStorage.setItem(this.storageKey, JSON.stringify(tokens));
  }

  // Expose a safe public method to set tokens after login
  setTokens(tokens: Tokens) {
    this.saveTokens(tokens);
    // Load user info after setting tokens, with proper error handling
    this.loadCurrentUser().subscribe({
      error: (error) => {
        console.error('Failed to load user after setting tokens:', error);
        // Don't clear auth here as we just set valid tokens
        // This might be a temporary network issue
      },
    });
  }

  get accessToken(): string | null {
    return this._tokens()?.access ?? null;
  }

  login(username: string, password: string) {
    return this.http.post<Tokens>('/api/auth/token/', { username, password });
  }

  logout() {
    this._tokens.set(null);
    this._currentUser.set(null);
    localStorage.removeItem(this.storageKey);
    // Only navigate to login if not already there to avoid infinite loops
    if (!this.router.url.startsWith('/login')) {
      this.router.navigateByUrl('/login');
    }
  }

  // Method to clear authentication without navigation (used by interceptor)
  clearAuth() {
    this._tokens.set(null);
    this._currentUser.set(null);
    localStorage.removeItem(this.storageKey);
  }

  refresh() {
    const refresh = this._tokens()?.refresh;
    if (!refresh) return null;
    return this.http.post<Tokens>('/api/auth/refresh/', { refresh });
  }

  me(): Observable<CurrentUser> {
    return this.http.get<CurrentUser>('/api/auth/me/');
  }

  loadCurrentUser(): Observable<CurrentUser> {
    return this.me().pipe(tap((user) => this._currentUser.set(user)));
  }

  switchRole(newRole: string): Observable<CurrentUser> {
    return this.http
      .patch<CurrentUser>('/api/auth/me/', { active_role: newRole })
      .pipe(tap((user) => this._currentUser.set(user)));
  }

  // Initialize user info if tokens exist
  constructor() {
    // Add a small delay to ensure the app is fully initialized
    setTimeout(() => {
      if (this.isAuthenticated()) {
        this.loadCurrentUser().subscribe({
          next: (user) => {
            this._initialized.set(true);
          },
          error: (error) => {
            // If loading user fails due to authentication error, clear auth and redirect
            console.warn('Failed to load user info, clearing auth:', error);
            this._initialized.set(true);
            this.logout(); // Use logout instead of clearAuth to ensure navigation
          },
        });
      } else {
        this._initialized.set(true);
      }
    }, 0);
  }
}
