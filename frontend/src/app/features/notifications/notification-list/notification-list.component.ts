import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { SelectModule } from 'primeng/select';
import { InputTextModule } from 'primeng/inputtext';
import { CardModule } from 'primeng/card';
import { TooltipModule } from 'primeng/tooltip';
import { NotificationService } from '../../../core/services/notification.service';
import { NotificationLog } from '../../../core/models/notification.model';

@Component({
  selector: 'app-notification-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    TagModule,
    SelectModule,
    InputTextModule,
    CardModule,
    TooltipModule,
  ],
  templateUrl: './notification-list.component.html',
  styleUrl: './notification-list.component.css',
})
export class NotificationListComponent implements OnInit {
  private notificationService = inject(NotificationService);

  notifications = signal<NotificationLog[]>([]);
  totalRecords = signal(0);
  loading = signal(false);

  // Filters
  statusFilter: string | undefined;
  channelFilter: string | undefined;
  unreadFilter: boolean | undefined;

  statusOptions = [
    { label: 'All', value: undefined },
    { label: 'Pending', value: 'pending' },
    { label: 'Sent', value: 'sent' },
    { label: 'Failed', value: 'failed' },
    { label: 'Acknowledged', value: 'acknowledged' },
  ];

  channelOptions = [
    { label: 'All', value: undefined },
    { label: 'Email', value: 'email' },
    { label: 'SMS', value: 'sms' },
    { label: 'Webhook', value: 'webhook' },
  ];

  unreadOptions = [
    { label: 'All', value: undefined },
    { label: 'Unread only', value: true },
    { label: 'Read only', value: false },
  ];

  ngOnInit(): void {
    this.loadNotifications();
  }

  loadNotifications(event?: any): void {
    this.loading.set(true);
    const page = event ? Math.floor(event.first / event.rows) + 1 : 1;

    this.notificationService
      .getNotifications({
        status: this.statusFilter,
        channel: this.channelFilter,
        unread: this.unreadFilter,
        page,
      })
      .subscribe({
        next: (response) => {
          this.notifications.set(response.results);
          this.totalRecords.set(response.count);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  acknowledgeNotification(notification: NotificationLog): void {
    this.notificationService
      .acknowledgeNotification(notification.id)
      .subscribe({
        next: () => {
          this.loadNotifications();
        },
      });
  }

  acknowledgeAll(): void {
    this.notificationService.acknowledgeAll().subscribe({
      next: () => {
        this.loadNotifications();
      },
    });
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

  getStatusClass(status: string): string {
    const statusMap: { [key: string]: string } = {
      pending: 'warning',
      sent: 'info',
      failed: 'danger',
      acknowledged: 'success',
    };
    return statusMap[status] || 'secondary';
  }

  formatDate(dateString: string | null): string {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  }
}
