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
    { label: 'Product Created', value: 'product_created' },
    { label: 'Product Updated', value: 'product_updated' },
    { label: 'Product Recalled', value: 'product_recalled' },
    { label: 'Batch Created', value: 'batch_created' },
    { label: 'Batch Updated', value: 'batch_updated' },
    { label: 'Batch Recalled', value: 'batch_recalled' },
    { label: 'Pack Created', value: 'pack_created' },
    { label: 'Pack Scanned', value: 'pack_scanned' },
    { label: 'Pack Damaged', value: 'pack_damaged' },
    { label: 'Pack Expired', value: 'pack_expired' },
    { label: 'Shipment Created', value: 'shipment_created' },
    { label: 'Shipment Updated', value: 'shipment_updated' },
    { label: 'Shipment Dispatched', value: 'shipment_dispatched' },
    { label: 'Shipment In Transit', value: 'shipment_in_transit' },
    { label: 'Shipment Delivered', value: 'shipment_delivered' },
    { label: 'Shipment Delayed', value: 'shipment_delayed' },
    { label: 'Temperature Alert', value: 'temperature_alert' },
    { label: 'Humidity Alert', value: 'humidity_alert' },
    { label: 'Location Update', value: 'location_update' },
    { label: 'Access Granted', value: 'access_granted' },
    { label: 'Access Denied', value: 'access_denied' },
    { label: 'Error', value: 'error' },
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
    { label: 'Webhook', value: 'webhook' },
  ];

  ngOnInit(): void {
    this.loadRules();
  }

  loadRules(): void {
    this.loading.set(true);
    this.notificationService.getNotificationRules().subscribe({
      next: (response) => {
        this.rules.set(response.results);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
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

  openEditDialog(rule: NotificationRule): void {
    this.editingRule = rule;
    this.formData = {
      name: rule.name,
      event_types: [...rule.event_types],
      severity_levels: [...rule.severity_levels],
      channels: [...rule.channels],
      enabled: rule.enabled,
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
        next: () => {
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
