import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  catchError,
  throwError,
  switchMap,
  BehaviorSubject,
  filter,
  take,
} from 'rxjs';
import { AuthService } from './auth.service';

let isRefreshing = false;
let refreshTokenSubject = new BehaviorSubject<string | null>(null);

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.accessToken;

  // Add Authorization header if token exists
  if (token) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      // Handle authentication errors (401 Unauthorized)
      if (
        error.status === 401 &&
        !req.url.includes('/auth/token/') &&
        !req.url.includes('/auth/refresh/')
      ) {
        // Try to refresh the token
        if (!isRefreshing) {
          isRefreshing = true;
          refreshTokenSubject.next(null);

          const refreshObservable = auth.refresh();
          if (!refreshObservable) {
            // No refresh token available, logout
            isRefreshing = false;
            auth.logout();
            return throwError(() => error);
          }

          return refreshObservable.pipe(
            switchMap((tokens) => {
              isRefreshing = false;
              auth.setTokens(tokens);
              refreshTokenSubject.next(tokens.access);

              // Retry the failed request with new token
              const clonedReq = req.clone({
                setHeaders: { Authorization: `Bearer ${tokens.access}` },
              });
              return next(clonedReq);
            }),
            catchError((refreshError) => {
              // Refresh failed, logout
              isRefreshing = false;
              auth.logout();
              return throwError(() => refreshError);
            })
          );
        } else {
          // Wait for the token refresh to complete
          return refreshTokenSubject.pipe(
            filter((token) => token !== null),
            take(1),
            switchMap((token) => {
              // Retry the failed request with new token
              const clonedReq = req.clone({
                setHeaders: { Authorization: `Bearer ${token}` },
              });
              return next(clonedReq);
            })
          );
        }
      }

      // Handle forbidden errors (403)
      if (error.status === 403) {
        auth.logout();
      }

      return throwError(() => error);
    })
  );
};
