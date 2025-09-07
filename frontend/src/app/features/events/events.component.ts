import { Component, inject, signal, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { TimelineModule } from 'primeng/timeline';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ToastModule } from 'primeng/toast';
import { DatePickerModule } from 'primeng/datepicker';
import { CheckboxModule } from 'primeng/checkbox';
import { BadgeModule } from 'primeng/badge';
import { PanelModule } from 'primeng/panel';
import { ToggleButtonModule } from 'primeng/togglebutton';
import { PaginatorModule } from 'primeng/paginator';
import { TableModule } from 'primeng/table';

// Services
import { TranslateModule } from '@ngx-translate/core';
import {
  EventService,
  EventListItem,
  EventFilters,
} from '../../core/services/event.service';
import { ProductService } from '../../core/services/product.service';
import { BatchService } from '../../core/services/batch.service';
import { PackService } from '../../core/services/pack.service';
import { ShipmentService } from '../../core/services/shipment.service';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-events',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    TimelineModule,
    ButtonModule,
    InputTextModule,
    SelectModule,
    TagModule,
    TooltipModule,
    ToastModule,
    DatePickerModule,
    CheckboxModule,
    BadgeModule,
    PanelModule,
    ToggleButtonModule,
    PaginatorModule,
    TableModule,
    TranslateModule,
  ],
  providers: [MessageService],
  templateUrl: './events.component.html',
})
export class EventsComponent implements OnInit {
  private eventService = inject(EventService);
  private productService = inject(ProductService);
  private batchService = inject(BatchService);
  private packService = inject(PackService);
  private shipmentService = inject(ShipmentService);
  private router = inject(Router);
  private messageService = inject(MessageService);

  // Reactive state
  events = this.eventService.events;
  loading = this.eventService.loading;

  // View state
  viewMode = signal<'timeline' | 'table'>('timeline');

  // Filter state
  filters = signal<EventFilters>({});
  searchTerm = signal('');
  selectedEventType = signal<string | null>(null);
  selectedEntityType = signal<string | null>(null);
  selectedSeverity = signal<string | null>(null);
  selectedProduct = signal<number | null>(null);
  selectedBatch = signal<number | null>(null);
  selectedPack = signal<number | null>(null);
  selectedShipment = signal<number | null>(null);
  selectedRecentDays = signal<number | null>(null);
  criticalOnly = signal(false);
  alertOnly = signal(false);
  dateFromFilter = signal<Date | null>(null);
  dateToFilter = signal<Date | null>(null);

  // Pagination state
  first = signal(0);
  rows = signal(10);

  // Options for dropdowns
  eventTypeOptions = this.eventService.getEventTypes();
  entityTypeOptions = this.eventService.getEntityTypes();
  severityOptions = this.eventService.getSeverityLevels();
  recentDaysOptions = this.eventService.getRecentDaysOptions();
  products = this.productService.products;
  batches = this.batchService.batches;
  packs = this.packService.packs;
  shipments = this.shipmentService.shipments;

  ngOnInit() {
    // Load related data for filter dropdowns
    this.productService.load().subscribe();
    this.batchService.load().subscribe();
    this.packService.load().subscribe();
    this.shipmentService.load().subscribe();
    this.loadEvents();
  }

  loadEvents() {
    // Reset pagination when loading new data
    this.first.set(0);

    const currentFilters = this.filters();
    this.eventService.load(currentFilters).subscribe({
      error: (error) => {
        console.error('Error loading events:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load events',
        });
      },
    });
  }

  onSearch() {
    this.filters.update((f) => ({
      ...f,
      search: this.searchTerm() || undefined,
    }));
    this.loadEvents();
  }

  onEventTypeFilter() {
    this.filters.update((f) => ({
      ...f,
      event_type: (this.selectedEventType() as any) || undefined,
    }));
    this.loadEvents();
  }

  onEntityTypeFilter() {
    this.filters.update((f) => ({
      ...f,
      entity_type: (this.selectedEntityType() as any) || undefined,
    }));
    this.loadEvents();
  }

  onSeverityFilter() {
    this.filters.update((f) => ({
      ...f,
      severity: (this.selectedSeverity() as any) || undefined,
    }));
    this.loadEvents();
  }

  onProductFilter() {
    this.filters.update((f) => ({
      ...f,
      product: this.selectedProduct() || undefined,
    }));
    this.loadEvents();
  }

  onBatchFilter() {
    this.filters.update((f) => ({
      ...f,
      batch: this.selectedBatch() || undefined,
    }));
    this.loadEvents();
  }

  onPackFilter() {
    this.filters.update((f) => ({
      ...f,
      pack: this.selectedPack() || undefined,
    }));
    this.loadEvents();
  }

  onShipmentFilter() {
    this.filters.update((f) => ({
      ...f,
      shipment: this.selectedShipment() || undefined,
    }));
    this.loadEvents();
  }

  onRecentDaysFilter() {
    this.filters.update((f) => ({
      ...f,
      recent_days: this.selectedRecentDays() || undefined,
    }));
    this.loadEvents();
  }

  onCriticalOnlyFilter() {
    this.filters.update((f) => ({
      ...f,
      critical_only: this.criticalOnly() || undefined,
    }));
    this.loadEvents();
  }

  onAlertOnlyFilter() {
    this.filters.update((f) => ({
      ...f,
      alert_only: this.alertOnly() || undefined,
    }));
    this.loadEvents();
  }

  onDateFilter() {
    const fromDate = this.dateFromFilter();
    const toDate = this.dateToFilter();

    this.filters.update((f) => ({
      ...f,
      date_from: fromDate ? this.formatDate(fromDate) : undefined,
      date_to: toDate ? this.formatDate(toDate) : undefined,
    }));
    this.loadEvents();
  }

  clearFilters() {
    this.searchTerm.set('');
    this.selectedEventType.set(null);
    this.selectedEntityType.set(null);
    this.selectedSeverity.set(null);
    this.selectedProduct.set(null);
    this.selectedBatch.set(null);
    this.selectedPack.set(null);
    this.selectedShipment.set(null);
    this.selectedRecentDays.set(null);
    this.criticalOnly.set(false);
    this.alertOnly.set(false);
    this.dateFromFilter.set(null);
    this.dateToFilter.set(null);
    this.filters.set({});
    this.loadEvents();
  }

  viewEvent(event: EventListItem) {
    this.router.navigate(['/events', event.id]);
  }

  toggleView() {
    this.viewMode.update((mode) =>
      mode === 'timeline' ? 'table' : 'timeline'
    );
  }

  onPageChange(event: any) {
    this.first.set(event.first);
    this.rows.set(event.rows);
  }

  // Computed property for total records (kept for compatibility)
  totalRecordsComputed = computed(() => this.events().length);

  getSeverityColor(
    severity: string
  ): 'success' | 'warning' | 'danger' | 'info' | 'secondary' {
    switch (severity) {
      case 'critical':
        return 'danger';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'secondary';
      case 'info':
      default:
        return 'success';
    }
  }

  getEventTypeIcon(eventType: string): string {
    return this.eventService.getEventTypeIcon(eventType as any);
  }

  getRelativeTime(timestamp: string): string {
    return this.eventService.getRelativeTime(timestamp);
  }

  formatTimestamp(timestamp: string): string {
    return this.eventService.formatTimestamp(timestamp);
  }

  isRecent(timestamp: string): boolean {
    return this.eventService.isRecent(timestamp);
  }

  getEntityDisplayInfo(event: EventListItem): string {
    if (event.entity_info) {
      const info = event.entity_info;
      switch (event.entity_type) {
        case 'product':
          return `${info.name} (${info.gtin || 'N/A'})`;
        case 'batch':
          return `${info.name} - ${info.product_name || 'Unknown Product'}`;
        case 'pack':
          return `${info.name} - ${info.product_name || 'Unknown Product'}`;
        case 'shipment':
          return `${info.name} (${info.carrier || 'Unknown Carrier'})`;
        default:
          return info.name;
      }
    }
    return `${event.entity_type}#${event.entity_id}`;
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  // Timeline event customization
  timelineEvents = computed(() => {
    return this.events().map((event) => ({
      ...event,
      icon: this.getEventTypeIcon(event.event_type),
      color: this.getSeverityColor(event.severity),
      relativeTime: this.getRelativeTime(event.timestamp),
      entityDisplay: this.getEntityDisplayInfo(event),
      isRecent: this.isRecent(event.timestamp),
    }));
  });
}
