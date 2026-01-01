import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap, catchError, map } from 'rxjs/operators';
import { Observable, of } from 'rxjs';

export type UserRole = 'Operator' | 'Auditor' | 'Admin';

export interface AppUser {
  id: number;
  username: string;
  first_name?: string;
  last_name?: string;
  email: string;
  active_role: UserRole;
  roles: UserRole[];
  created_at?: string;
  is_deleted?: boolean;
}

export interface UsersPaginatedResponse {
  count: number;
  total_pages: number;
  current_page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: AppUser[];
}

@Injectable({ providedIn: 'root' })
export class UserManagementService {
  private http = inject(HttpClient);
  private _users = signal<AppUser[]>([]);
  private _totalCount = signal<number>(0);
  private _currentPage = signal<number>(1);
  private _totalPages = signal<number>(1);

  readonly users = computed(() => this._users());
  readonly totalCount = computed(() => this._totalCount());
  readonly currentPage = computed(() => this._currentPage());
  readonly totalPages = computed(() => this._totalPages());

  load(
    page: number = 1,
    pageSize: number = 25
  ): Observable<UsersPaginatedResponse> {
    return this.http
      .get<UsersPaginatedResponse>(
        `/api/users/?page=${page}&page_size=${pageSize}`
      )
      .pipe(
        tap((response) => {
          this._users.set(response.results);
          this._totalCount.set(response.count);
          this._currentPage.set(response.current_page);
          this._totalPages.set(response.total_pages);
        }),
        catchError((error) => {
          console.error('Failed to load users:', error);
          this._users.set([]);
          this._totalCount.set(0);
          return of({
            count: 0,
            total_pages: 0,
            current_page: 1,
            page_size: pageSize,
            next: null,
            previous: null,
            results: [],
          });
        })
      );
  }

  create(data: {
    username: string;
    email: string;
    first_name?: string;
    last_name?: string;
    initial_role: UserRole;
    password?: string;
  }): Observable<AppUser> {
    return this.http
      .post<AppUser>('/api/users/', data)
      .pipe(tap((u) => this._users.update((list) => [...list, u])));
  }

  update(
    id: number,
    data: {
      first_name?: string;
      last_name?: string;
      email?: string;
      active_role?: UserRole;
      roles?: UserRole[];
      password?: string;
    }
  ): Observable<AppUser> {
    return this.http
      .patch<AppUser>(`/api/users/${id}/`, {
        ...data,
        roles_input: data.roles, // Send roles as roles_input to backend
        active_role: data.active_role,
      })
      .pipe(
        tap((updated) =>
          this._users.update((list) =>
            list.map((u) => (u.id === id ? updated : u))
          )
        )
      );
  }

  delete(id: number): Observable<{ message: string }> {
    return this.http
      .delete<{ message: string }>(`/api/users/${id}/delete/`)
      .pipe(
        tap(() => this._users.update((list) => list.filter((u) => u.id !== id)))
      );
  }
}
