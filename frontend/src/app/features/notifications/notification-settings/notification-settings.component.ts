import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { CardModule } from 'primeng/card';
import { DialogModule } from 'primeng/dialog';
import { MultiSelectModule } from 'primeng/multiselect';
import { ToggleSwitchModule } from 'primeng/toggleswitch';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { Router } from '@angular/router';
import { NotificationService } from '../../../core/services/notification.service';
import {
  NotificationRule,
  NotificationRuleCreate,
} from '../../../core/models/notification.model';

@Component({
  selector: 'app-notification-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    CardModule,
    DialogModule,
    MultiSelectModule,
    ToggleSwitchModule,
    ToastModule,
  ],
  providers: [MessageService],
  templateUrl: './notification-settings.component.html',
  styleUrl: './notification-settings.component.css',
})
export class NotificationSettingsComponent implements OnInit {
  private notificationService = inject(NotificationService);
  private messageService = inject(MessageService);
  private router = inject(Router);

  rules = signal<NotificationRule[]>([]);
  loading = signal(false);
  showDialog = signal(false);
  editingRule: NotificationRule | null = null;

  // Form data
  formData: NotificationRuleCreate = {
    name: '',
    event_types: [],
    severity_levels: [],
    channels: [],
    enabled: true,
  };

  // Options for multi-selects
  eventTypeOptions = [
    { label: 'Created', value: 'created' },
    { label: 'Updated', value: 'updated' },
    { label: 'Deleted', value: 'deleted' },
    { label: 'Status Changed', value: 'status_changed' },
    { label: 'Expired', value: 'expired' },
  ];

  severityOptions = [
    { label: 'Critical', value: 'critical' },
    { label: 'High', value: 'high' },
    { label: 'Medium', value: 'medium' },
    { label: 'Low', value: 'low' },
    { label: 'Info', value: 'info' },
  ];

  channelOptions = [
    { label: 'Email', value: 'email' },
    { label: 'SMS', value: 'sms' },
    { label: 'WebSocket', value: 'websocket' },
  ];

  ngOnInit(): void {
    this.loadRules();
  }

  private normalizeRule(rule: NotificationRule): NotificationRule {
    return {
      ...rule,
      event_types: Array.isArray(rule.event_types) ? rule.event_types : [],
      severity_levels: Array.isArray(rule.severity_levels)
        ? rule.severity_levels
        : [],
      channels: Array.isArray(rule.channels) ? rule.channels : [],
    };
  }

  loadRules(): void {
    this.loading.set(true);
    this.notificationService.getNotificationRules().subscribe({
      next: (response) => {
        const rawRules: NotificationRule[] = Array.isArray(response)
          ? response
          : Array.isArray((response as any)?.results)
            ? ((response as any).results as NotificationRule[])
            : [];

        this.rules.set(
          rawRules.map((rule: NotificationRule) => this.normalizeRule(rule)),
        );
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load notification rules',
        });
      },
    });
  }

  openCreateDialog(): void {
    this.editingRule = null;
    this.formData = {
      name: '',
      event_types: [],
      severity_levels: [],
      channels: ['email'],
      enabled: true,
    };
    this.showDialog.set(true);
  }

  openNotificationsList(): void {
    this.router.navigate(['/notifications']);
  }

  openEditDialog(rule: NotificationRule): void {
    const safeRule = this.normalizeRule(rule);
    this.editingRule = safeRule;
    this.formData = {
      name: safeRule.name,
      event_types: [...safeRule.event_types],
      severity_levels: [...safeRule.severity_levels],
      channels: [...safeRule.channels],
      enabled: safeRule.enabled,
    };
    this.showDialog.set(true);
  }

  saveRule(): void {
    if (
      !this.formData.name ||
      this.formData.event_types.length === 0 ||
      this.formData.severity_levels.length === 0 ||
      this.formData.channels.length === 0
    ) {
      this.messageService.add({
        severity: 'error',
        summary: 'Validation Error',
        detail: 'Please fill all required fields',
      });
      return;
    }

    if (this.editingRule) {
      this.notificationService
        .updateNotificationRule(this.editingRule.id, this.formData)
        .subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Notification rule updated',
            });
            this.showDialog.set(false);
            this.loadRules();
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to update notification rule',
            });
          },
        });
    } else {
      this.notificationService.createNotificationRule(this.formData).subscribe({
        next: (createdRule) => {
          const normalizedRule = this.normalizeRule(createdRule);
          this.rules.update((existingRules) => [
            normalizedRule,
            ...existingRules,
          ]);
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Notification rule created',
          });
          this.showDialog.set(false);
          this.loadRules();
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to create notification rule',
          });
        },
      });
    }
  }

  toggleRule(rule: NotificationRule): void {
    this.notificationService.toggleNotificationRule(rule.id).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `Rule ${rule.enabled ? 'disabled' : 'enabled'}`,
        });
        this.loadRules();
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to toggle rule',
        });
      },
    });
  }

  deleteRule(rule: NotificationRule): void {
    if (confirm(`Are you sure you want to delete the rule "${rule.name}"?`)) {
      this.notificationService.deleteNotificationRule(rule.id).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Notification rule deleted',
          });
          this.loadRules();
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to delete notification rule',
          });
        },
      });
    }
  }
}
