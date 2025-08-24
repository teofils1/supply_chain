import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      // Handle different types of errors
      switch (error.status) {
        case 0:
          // Network error - could be server down or no internet
          console.error('Network error - server may be unreachable');
          break;
        case 500:
          // Internal server error
          console.error('Internal server error');
          break;
        case 404:
          // Not found - might want to handle this differently based on endpoint
          console.error('Resource not found');
          break;
        default:
          console.error(`HTTP Error ${error.status}:`, error.error);
      }

      // Re-throw the error so components can handle it appropriately
      return throwError(() => error);
    })
  );
};
