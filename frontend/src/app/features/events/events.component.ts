import {
  Component,
  inject,
  signal,
  OnInit,
  computed,
  ElementRef,
  ViewChild,
  AfterViewInit,
  OnDestroy,
} from '@angular/core';
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
import { TableModule, TableLazyLoadEvent } from 'primeng/table';

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
import {
  lazyLoadToParams,
  DEFAULT_PAGE_SIZE,
  PAGE_SIZE_OPTIONS,
} from '../../core/models/pagination.model';

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
export class EventsComponent implements OnInit, AfterViewInit, OnDestroy {
  private eventService = inject(EventService);
  private productService = inject(ProductService);
  private batchService = inject(BatchService);
  private packService = inject(PackService);
  private shipmentService = inject(ShipmentService);
  private router = inject(Router);
  private messageService = inject(MessageService);

  // Scroll sentinel for infinite scroll
  @ViewChild('scrollSentinel') scrollSentinel!: ElementRef;
  private intersectionObserver?: IntersectionObserver;

  // Reactive state
  events = this.eventService.events;
  loading = this.eventService.loading;
  totalRecords = this.eventService.totalRecords;

  // Computed: check if there are more events to load
  hasMoreEvents = computed(() => this.events().length < this.totalRecords());
  loadingMore = signal(false);

  // Track if we've loaded events to prevent unnecessary reloads on view switch
  private initialLoadDone = false;
  // Track the current page for timeline infinite scroll
  timelinePage = signal(1);

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
  rows = signal(DEFAULT_PAGE_SIZE);
  rowsPerPageOptions = PAGE_SIZE_OPTIONS;

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
    // Load events initially (timeline view doesn't trigger onLazyLoad)
    this.loadEvents();
  }

  ngAfterViewInit() {
    // Set up intersection observer for infinite scroll in timeline view
    this.setupInfiniteScroll();
  }

  ngOnDestroy() {
    // Clean up intersection observer
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
    }
  }

  private setupInfiniteScroll() {
    if (!this.scrollSentinel) return;

    this.intersectionObserver = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (
          entry.isIntersecting &&
          this.viewMode() === 'timeline' &&
          this.hasMoreEvents() &&
          !this.loading() &&
          !this.loadingMore()
        ) {
          this.loadMoreEvents();
        }
      },
      { threshold: 0.1 }
    );

    this.intersectionObserver.observe(this.scrollSentinel.nativeElement);
  }

  /**
   * Load more events for infinite scroll in timeline view
   */
  loadMoreEvents() {
    if (!this.hasMoreEvents() || this.loadingMore()) return;

    this.loadingMore.set(true);
    const nextPage = this.timelinePage() + 1;

    this.eventService
      .loadMore(this.filters(), {
        page: nextPage,
        page_size: this.rows(),
      })
      .subscribe({
        next: () => {
          this.timelinePage.set(nextPage);
          this.loadingMore.set(false);
        },
        error: (error) => {
          console.error('Error loading more events:', error);
          this.loadingMore.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to load more events',
          });
        },
      });
  }

  /**
   * Handle lazy load event from PrimeNG table for server-side pagination
   */
  onLazyLoad(event: TableLazyLoadEvent) {
    const newFirst = event.first || 0;
    const newRows = event.rows || DEFAULT_PAGE_SIZE;

    // Skip if this is just the initial table render and we already have events
    if (
      this.initialLoadDone &&
      this.events().length > 0 &&
      newFirst === this.first() &&
      newRows === this.rows()
    ) {
      return;
    }

    this.first.set(newFirst);
    this.rows.set(newRows);

    const paginationParams = lazyLoadToParams({
      first: newFirst,
      rows: newRows,
    });

    this.eventService.load(this.filters(), paginationParams).subscribe({
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

  loadEvents() {
    const paginationParams = lazyLoadToParams({
      first: this.first(),
      rows: this.rows(),
    });

    this.eventService.load(this.filters(), paginationParams).subscribe({
      next: () => {
        this.initialLoadDone = true;
        this.timelinePage.set(1);
      },
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
    this.first.set(0);
    this.loadEvents();
  }

  onEventTypeFilter() {
    this.filters.update((f) => ({
      ...f,
      event_type: (this.selectedEventType() as any) || undefined,
    }));
    this.first.set(0);
    this.loadEvents();
  }

  onEntityTypeFilter() {
    this.filters.update((f) => ({
      ...f,
      entity_type: (this.selectedEntityType() as any) || undefined,
    }));
    this.first.set(0);
    this.loadEvents();
  }

  onSeverityFilter() {
    this.filters.update((f) => ({
      ...f,
      severity: (this.selectedSeverity() as any) || undefined,
    }));
    this.first.set(0);
    this.loadEvents();
  }

  onProductFilter() {
    this.filters.update((f) => ({
      ...f,
      product: this.selectedProduct() || undefined,
    }));
    this.first.set(0);
    this.loadEvents();
  }

  onBatchFilter() {
    this.filters.update((f) => ({
      ...f,
      batch: this.selectedBatch() || undefined,
    }));
    this.first.set(0);
    this.loadEvents();
  }

  onPackFilter() {
    this.filters.update((f) => ({
      ...f,
      pack: this.selectedPack() || undefined,
    }));
    this.first.set(0);
    this.loadEvents();
  }

  onShipmentFilter() {
    this.filters.update((f) => ({
      ...f,
      shipment: this.selectedShipment() || undefined,
    }));
    this.first.set(0);
    this.loadEvents();
  }

  onRecentDaysFilter() {
    this.filters.update((f) => ({
      ...f,
      recent_days: this.selectedRecentDays() || undefined,
    }));
    this.first.set(0);
    this.loadEvents();
  }

  onCriticalOnlyFilter() {
    this.filters.update((f) => ({
      ...f,
      critical_only: this.criticalOnly() || undefined,
    }));
    this.first.set(0);
    this.loadEvents();
  }

  onAlertOnlyFilter() {
    this.filters.update((f) => ({
      ...f,
      alert_only: this.alertOnly() || undefined,
    }));
    this.first.set(0);
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
    this.first.set(0);
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
    this.first.set(0);
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
    this.loadEvents();
  }

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
