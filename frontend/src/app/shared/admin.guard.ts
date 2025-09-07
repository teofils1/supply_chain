import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

export const adminGuard: CanActivateFn = (route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.isAuthenticated()) {
    return router.createUrlTree(['/login'], {
      queryParams: { returnUrl: state.url },
    });
  }

  const user = auth.currentUser();
  if (!user) {
    return router.createUrlTree(['/login'], {
      queryParams: { returnUrl: state.url },
    });
  }

  // Check if user has Admin role
  const hasAdminRole =
    user.active_role === 'Admin'

  if (!hasAdminRole) {
    // Redirect to home page if not admin
    return router.createUrlTree(['/']);
  }

  return true;
};
