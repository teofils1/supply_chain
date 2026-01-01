import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { BadgeModule } from 'primeng/badge';
import { ButtonModule } from 'primeng/button';
import { PopoverModule } from 'primeng/popover';
import { ScrollPanelModule } from 'primeng/scrollpanel';
import { TagModule } from 'primeng/tag';
import { NotificationService } from '../../../core/services/notification.service';
import { NotificationLog } from '../../../core/models/notification.model';

@Component({
  selector: 'app-notification-bell',
  standalone: true,
  imports: [
    CommonModule,
    BadgeModule,
    ButtonModule,
    PopoverModule,
    ScrollPanelModule,
    TagModule,
  ],
  templateUrl: './notification-bell.component.html',
  styleUrl: './notification-bell.component.css',
})
export class NotificationBellComponent implements OnInit {
  private notificationService = inject(NotificationService);
  private router = inject(Router);

  unreadCount = this.notificationService.unreadCount;
  recentNotifications = signal<NotificationLog[]>([]);
  loading = signal(false);

  ngOnInit(): void {
    this.notificationService.getUnreadCount().subscribe({
      next: (response) => {
        console.log('Unread count response:', response);
      },
      error: (err) => {
        console.error('Failed to get unread count:', err);
      },
    });
  }

  loadRecent(): void {
    this.loading.set(true);
    this.notificationService.getRecentNotifications().subscribe({
      next: (notifications) => {
        console.log('Loaded notifications:', notifications);
        this.recentNotifications.set(notifications);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Failed to load recent notifications:', err);
        this.loading.set(false);
      },
    });
  }

  acknowledgeNotification(notification: NotificationLog, event: Event): void {
    event.stopPropagation();
    this.notificationService
      .acknowledgeNotification(notification.id)
      .subscribe({
        next: () => {
          this.loadRecent();
        },
      });
  }

  acknowledgeAll(): void {
    this.notificationService.acknowledgeAll().subscribe({
      next: () => {
        this.loadRecent();
      },
    });
  }

  viewAllNotifications(): void {
    this.router.navigate(['/notifications']);
  }

  getSeverityClass(severity: string): string {
    const severityMap: { [key: string]: string } = {
      critical: 'danger',
      high: 'warning',
      medium: 'info',
      low: 'success',
      info: 'secondary',
    };
    return severityMap[severity] || 'secondary';
  }

  getChannelIcon(channel: string): string {
    const iconMap: { [key: string]: string } = {
      email: 'pi-envelope',
      sms: 'pi-mobile',
      websocket: 'pi-wifi',
      webhook: 'pi-globe',
    };
    return iconMap[channel] || 'pi-bell';
  }

  getTimeSince(timestamp: string): string {
    const now = new Date();
    const past = new Date(timestamp);
    const seconds = Math.floor((now.getTime() - past.getTime()) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  }
}
