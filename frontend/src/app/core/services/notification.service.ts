import { Injectable, signal, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject, interval, of, EMPTY } from 'rxjs';
import { tap, switchMap, catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import {
  NotificationLog,
  NotificationRule,
  NotificationRuleCreate,
} from '../models/notification.model';
import { AuthService } from '../../shared/auth.service';

@Injectable({
  providedIn: 'root',
})
export class NotificationService {
  private apiUrl = `${environment.apiUrl}/notifications`;
  private unreadCountSubject = new BehaviorSubject<number>(0);
  public unreadCount$ = this.unreadCountSubject.asObservable();
  private auth = inject(AuthService);

  // Signal for unread count (modern Angular approach)
  unreadCount = signal(0);

  constructor(private http: HttpClient) {
    // Poll for unread count every 30 seconds, but only when authenticated
    this.startPolling();
  }

  private startPolling(): void {
    interval(30000)
      .pipe(
        switchMap(() => {
          // Only fetch if user is authenticated
          if (this.auth.isAuthenticated()) {
            return this.getUnreadCount();
          }
          return EMPTY; // Return empty observable when not authenticated
        }),
        catchError((error) => {
          // Silently handle errors to prevent console spam
          console.debug('Failed to fetch unread count:', error);
          return EMPTY; // Return empty observable on error
        })
      )
      .subscribe();
  }

  // Notification Logs
  getNotifications(params?: {
    status?: string;
    channel?: string;
    unread?: boolean;
    page?: number;
  }): Observable<{ count: number; results: NotificationLog[] }> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.status) httpParams = httpParams.set('status', params.status);
      if (params.channel)
        httpParams = httpParams.set('channel', params.channel);
      if (params.unread !== undefined)
        httpParams = httpParams.set('unread', params.unread.toString());
      if (params.page)
        httpParams = httpParams.set('page', params.page.toString());
    }
    return this.http.get<{ count: number; results: NotificationLog[] }>(
      `${this.apiUrl}/logs/`,
      { params: httpParams }
    );
  }

  getNotification(id: number): Observable<NotificationLog> {
    return this.http.get<NotificationLog>(`${this.apiUrl}/logs/${id}/`);
  }

  getRecentNotifications(): Observable<NotificationLog[]> {
    return this.http.get<NotificationLog[]>(`${this.apiUrl}/logs/recent/`).pipe(
      catchError((error) => {
        console.error('Failed to load recent notifications:', error);
        return of([]);
      })
    );
  }

  acknowledgeNotification(id: number): Observable<NotificationLog> {
    return this.http
      .post<NotificationLog>(`${this.apiUrl}/logs/${id}/acknowledge/`, {})
      .pipe(tap(() => this.refreshUnreadCount()));
  }

  acknowledgeAll(): Observable<{ acknowledged_count: number }> {
    return this.http
      .post<{ acknowledged_count: number }>(
        `${this.apiUrl}/logs/acknowledge-all/`,
        {}
      )
      .pipe(tap(() => this.refreshUnreadCount()));
  }

  getUnreadCount(): Observable<{ unread_count: number }> {
    return this.http
      .get<{ unread_count: number }>(`${this.apiUrl}/logs/unread-count/`)
      .pipe(
        tap((response) => {
          this.unreadCountSubject.next(response.unread_count);
          this.unreadCount.set(response.unread_count);
        })
      );
  }

  refreshUnreadCount(): void {
    this.getUnreadCount().subscribe();
  }

  // Notification Rules
  getNotificationRules(): Observable<{
    count: number;
    results: NotificationRule[];
  }> {
    return this.http.get<{ count: number; results: NotificationRule[] }>(
      `${this.apiUrl}/rules/`
    );
  }

  getNotificationRule(id: number): Observable<NotificationRule> {
    return this.http.get<NotificationRule>(`${this.apiUrl}/rules/${id}/`);
  }

  createNotificationRule(
    rule: NotificationRuleCreate
  ): Observable<NotificationRule> {
    return this.http.post<NotificationRule>(`${this.apiUrl}/rules/`, rule);
  }

  updateNotificationRule(
    id: number,
    rule: Partial<NotificationRuleCreate>
  ): Observable<NotificationRule> {
    return this.http.patch<NotificationRule>(
      `${this.apiUrl}/rules/${id}/`,
      rule
    );
  }

  deleteNotificationRule(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/rules/${id}/`);
  }

  toggleNotificationRule(id: number): Observable<NotificationRule> {
    return this.http.post<NotificationRule>(
      `${this.apiUrl}/rules/${id}/toggle/`,
      {}
    );
  }
}
