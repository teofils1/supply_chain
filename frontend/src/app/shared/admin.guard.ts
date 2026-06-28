import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { catchError, map, of } from 'rxjs';
import { AuthService, CurrentUser } from './auth.service';

export const adminGuard: CanActivateFn = (route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.isAuthenticated()) {
    return router.createUrlTree(['/login'], {
      queryParams: { returnUrl: state.url },
    });
  }

  const checkAdmin = (user: CurrentUser) =>
    user.active_role === 'Admin' ? true : router.createUrlTree(['/']);

  const user = auth.currentUser();
  if (user) {
    return checkAdmin(user);
  }

  return auth.ensureCurrentUser().pipe(
    map(checkAdmin),
    catchError(() =>
      of(
        router.createUrlTree(['/login'], {
          queryParams: { returnUrl: state.url },
        }),
      ),
    ),
  );
};
