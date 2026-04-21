import { inject } from '@angular/core';
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, switchMap, throwError } from 'rxjs';

import { AuthService } from '../services/auth';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const token = auth.getToken();
  const isTokenEndpoint = req.url.includes('/api/token/');

  const requestWithToken = token && !isTokenEndpoint
    ? req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`,
        },
      })
    : req;

  return next(requestWithToken).pipe(
    catchError((error: HttpErrorResponse) => {
      const refresh = auth.getRefreshToken();

      if (error.status !== 401 || !refresh || isTokenEndpoint) {
        return throwError(() => error);
      }

      return auth.refreshAccessToken(refresh).pipe(
        switchMap((res) => {
          auth.saveToken(res.access);
          const retryReq = req.clone({
            setHeaders: {
              Authorization: `Bearer ${res.access}`,
            },
          });
          return next(retryReq);
        }),
        catchError((refreshError) => {
          auth.logout();
          return throwError(() => refreshError);
        })
      );
    })
  );
};
