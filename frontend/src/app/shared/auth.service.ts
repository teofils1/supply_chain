import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

type Tokens = { access: string; refresh: string };

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  private readonly storageKey = 'auth.tokens';
  private _tokens = signal<Tokens | null>(this.loadTokens());

  readonly isAuthenticated = computed(() => !!this._tokens());

  private loadTokens(): Tokens | null {
    const raw = localStorage.getItem(this.storageKey);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as Tokens;
    } catch {
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
  }

  get accessToken(): string | null {
    return this._tokens()?.access ?? null;
  }

  login(username: string, password: string) {
    return this.http.post<Tokens>('/api/auth/token/', { username, password });
  }

  logout() {
    this._tokens.set(null);
    localStorage.removeItem(this.storageKey);
    this.router.navigateByUrl('/login');
  }

  refresh() {
    const refresh = this._tokens()?.refresh;
    if (!refresh) return null;
    return this.http.post<Tokens>('/api/auth/refresh/', { refresh });
  }

  me() {
    return this.http.get<{ id: number; username: string; email: string }>(
      '/api/auth/me/'
    );
  }
}
