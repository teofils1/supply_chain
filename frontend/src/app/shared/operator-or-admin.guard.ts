import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

export const operatorOrAdminGuard: CanActivateFn = (route, state) => {
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

  // Check if user has Operator or Admin role
  const hasOperatorOrAdminRole =
    ['Admin', 'Operator'].includes(user.active_role!)

  if (!hasOperatorOrAdminRole) {
    // Redirect to home page if not operator or admin
    return router.createUrlTree(['/']);
  }

  return true;
};
