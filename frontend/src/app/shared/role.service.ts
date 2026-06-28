import { Injectable, inject } from '@angular/core';
import { AuthService } from './auth.service';

export type UserRole = 'Admin' | 'Operator' | 'Auditor';

@Injectable({ providedIn: 'root' })
export class RoleService {
  private auth = inject(AuthService);

  // Check if the user's currently selected role matches the required role
  hasRole(role: UserRole): boolean {
    const user = this.auth.currentUser();
    if (!user) return false;

    return user.active_role === role;
  }

  // Check if the user's currently selected role matches any required role
  hasAnyRole(roles: UserRole[]): boolean {
    const user = this.auth.currentUser();
    if (!user) return false;

    return roles.includes(user.active_role as UserRole);
  }

  // Role-specific checks
  isAdmin(): boolean {
    return this.hasRole('Admin');
  }

  isOperator(): boolean {
    return this.hasRole('Operator');
  }

  isAuditor(): boolean {
    return this.hasRole('Auditor');
  }

  isOperatorOrAdmin(): boolean {
    return this.hasAnyRole(['Admin', 'Operator']);
  }

  isAuditorOrHigher(): boolean {
    return this.hasAnyRole(['Admin', 'Operator', 'Auditor']);
  }

  // Permission checks for UI actions
  canCreate(): boolean {
    return this.hasAnyRole(['Admin', 'Operator']);
  }

  canUpdate(): boolean {
    return this.hasAnyRole(['Admin', 'Operator']);
  }

  canDelete(): boolean {
    return this.hasAnyRole(['Admin', 'Operator']);
  }

  canViewUsers(): boolean {
    return this.isAdmin();
  }

  canManageUsers(): boolean {
    return this.isAdmin();
  }

  canRead(): boolean {
    return this.hasAnyRole(['Admin', 'Operator', 'Auditor']);
  }

  // Get current user's role for display
  getCurrentRole(): string | null {
    const user = this.auth.currentUser();
    return user?.active_role || null;
  }

  // Get all available roles for the current user
  getAvailableRoles(): string[] {
    const user = this.auth.currentUser();
    return user?.roles || [];
  }
}
