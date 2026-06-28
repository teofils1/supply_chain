import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { catchError, map, of } from 'rxjs';
import { AuthService, CurrentUser } from './auth.service';

export const operatorOrAdminGuard: CanActivateFn = (route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.isAuthenticated()) {
    return router.createUrlTree(['/login'], {
      queryParams: { returnUrl: state.url },
    });
  }

  const checkOperatorOrAdmin = (user: CurrentUser) =>
    user.active_role && ['Admin', 'Operator'].includes(user.active_role)
      ? true
      : router.createUrlTree(['/']);

  const user = auth.currentUser();
  if (user) {
    return checkOperatorOrAdmin(user);
  }

  return auth.ensureCurrentUser().pipe(
    map(checkOperatorOrAdmin),
    catchError(() =>
      of(
        router.createUrlTree(['/login'], {
          queryParams: { returnUrl: state.url },
        }),
      ),
    ),
  );
};
