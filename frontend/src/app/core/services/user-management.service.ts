import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs/operators';
import { Observable } from 'rxjs';

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

@Injectable({ providedIn: 'root' })
export class UserManagementService {
  private http = inject(HttpClient);
  private _users = signal<AppUser[]>([]);
  readonly users = computed(() => this._users());

  load(): Observable<AppUser[]> {
    return this.http
      .get<AppUser[]>('/api/users/')
      .pipe(tap((users) => this._users.set(users)));
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
