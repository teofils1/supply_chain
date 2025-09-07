import { Injectable, inject } from '@angular/core';
import { AuthService } from './auth.service';

export type UserRole = 'Admin' | 'Operator' | 'Auditor';

@Injectable({ providedIn: 'root' })
export class RoleService {
  private auth = inject(AuthService);

  // Check if user has specific role
  hasRole(role: UserRole): boolean {
    const user = this.auth.currentUser();
    if (!user) return false;

    return user.active_role === role || user.roles?.includes(role) || false;
  }

  // Check if user has any of the specified roles
  hasAnyRole(roles: UserRole[]): boolean {
    const user = this.auth.currentUser();
    if (!user) return false;

    return (
      roles.includes(user.active_role as UserRole) ||
      user.roles?.some((role) => roles.includes(role as UserRole)) ||
      false
    );
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
