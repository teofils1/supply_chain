import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, map } from 'rxjs';
import {
  PaginatedResponse,
  PaginationParams,
  DEFAULT_PAGE_SIZE,
} from '../models/pagination.model';
import { CacheService } from './cache.service';

export type EventType =
  | 'created'
  | 'updated'
  | 'deleted'
  | 'status_changed'
  | 'location_changed'
  | 'quality_check'
  | 'temperature_alert'
  | 'shipped'
  | 'delivered'
  | 'returned'
  | 'damaged'
  | 'expired'
  | 'recalled'
  | 'inventory_count'
  | 'maintenance'
  | 'calibration'
  | 'user_action'
  | 'system_action'
  | 'alert'
  | 'warning'
  | 'error'
  | 'other';

export type EntityType =
  | 'product'
  | 'batch'
  | 'pack'
  | 'shipment'
  | 'user'
  | 'device'
  | 'location'
  | 'system';

export type SeverityLevel = 'info' | 'low' | 'medium' | 'high' | 'critical';

export type IntegrityStatus = 'pending' | 'anchored' | 'failed';

export interface EntityInfo {
  type: string;
  id: number;
  name: string;
  gtin?: string;
  product_name?: string;
  batch_lot_number?: string;
  carrier?: string;
  status?: string;
}

export interface RelatedProduct {
  id: number;
  name: string;
  gtin: string;
  form: string;
  strength: string;
}

export interface RelatedBatch {
  id: number;
  lot_number: string;
  manufacturing_date: string;
  expiry_date: string;
  status: string;
  quantity_produced: number;
}

export interface RelatedPack {
  id: number;
  serial_number: string;
  pack_size: number;
  pack_type: string;
  status: string;
  location: string;
}

export interface RelatedShipment {
  id: number;
  tracking_number: string;
  status: string;
  carrier: string;
  service_type: string;
  origin_name: string;
  destination_name: string;
}

export interface Event {
  id: number;
  event_type: EventType;
  event_type_display: string;
  entity_type: EntityType;
  entity_type_display: string;
  entity_id: number;
  entity_display_name: string;
  entity_info: EntityInfo | null;
  timestamp: string;
  description: string;
  metadata: any;
  severity: SeverityLevel;
  severity_display: string;
  location: string;
  user: number | null;
  user_username: string | null;
  user_full_name: string | null;
  user_email?: string | null;
  ip_address: string | null;
  user_agent: string;
  system_info: any;
  is_critical: boolean;
  is_alert: boolean;
  // Blockchain integrity fields
  blockchain_tx_hash: string | null;
  blockchain_block_number: number | null;
  integrity_status: IntegrityStatus;
  event_hash: string | null;
  is_blockchain_anchored: boolean;
  blockchain_explorer_url: string | null;
  related_product: RelatedProduct | null;
  related_batch: RelatedBatch | null;
  related_pack: RelatedPack | null;
  related_shipment: RelatedShipment | null;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
}

export interface EventListItem {
  id: number;
  event_type: EventType;
  event_type_display: string;
  entity_type: EntityType;
  entity_type_display: string;
  entity_id: number;
  entity_display_name: string;
  entity_info: EntityInfo | null;
  timestamp: string;
  description: string;
  severity: SeverityLevel;
  severity_display: string;
  location: string;
  user: number | null;
  user_username: string | null;
  user_full_name: string | null;
  is_critical: boolean;
  is_alert: boolean;
  // Blockchain integrity fields
  blockchain_tx_hash: string | null;
  blockchain_block_number: number | null;
  integrity_status: IntegrityStatus;
  event_hash: string | null;
  is_blockchain_anchored: boolean;
  blockchain_explorer_url: string | null;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
}

export interface EventFilters {
  search?: string;
  event_type?: EventType;
  entity_type?: EntityType;
  entity_id?: number;
  severity?: SeverityLevel;
  user?: number;
  location?: string;
  timestamp_from?: string;
  timestamp_to?: string;
  date_from?: string;
  date_to?: string;
  product?: number;
  batch?: number;
  pack?: number;
  shipment?: number;
  critical_only?: boolean;
  alert_only?: boolean;
  recent_days?: number;
}

export interface CreateEventData {
  event_type: EventType;
  entity_type: EntityType;
  entity_id: number;
  description: string;
  metadata?: any;
  severity?: SeverityLevel;
  location?: string;
  user?: number;
  ip_address?: string;
  user_agent?: string;
  system_info?: any;
}

@Injectable({ providedIn: 'root' })
export class EventService {
  private http = inject(HttpClient);
  private cacheService = inject(CacheService);
  private _events = signal<EventListItem[]>([]);
  private _loading = signal(false);
  private _totalRecords = signal(0);
  private _currentPage = signal(1);
  private _pageSize = signal(DEFAULT_PAGE_SIZE);

  readonly events = computed(() => this._events());
  readonly loading = computed(() => this._loading());
  readonly totalRecords = computed(() => this._totalRecords());
  readonly currentPage = computed(() => this._currentPage());
  readonly pageSize = computed(() => this._pageSize());

  /**
   * Load events with optional filters and pagination
   */
  load(
    filters?: EventFilters,
    pagination?: PaginationParams
  ): Observable<PaginatedResponse<EventListItem>> {
    this._loading.set(true);

    let params = new HttpParams();

    // Pagination params
    const page = pagination?.page || 1;
    const pageSize = pagination?.page_size || DEFAULT_PAGE_SIZE;
    params = params.set('page', page.toString());
    params = params.set('page_size', pageSize.toString());

    // Filter params
    if (filters?.search) {
      params = params.set('search', filters.search);
    }
    if (filters?.event_type) {
      params = params.set('event_type', filters.event_type);
    }
    if (filters?.entity_type) {
      params = params.set('entity_type', filters.entity_type);
    }
    if (filters?.entity_id) {
      params = params.set('entity_id', filters.entity_id.toString());
    }
    if (filters?.severity) {
      params = params.set('severity', filters.severity);
    }
    if (filters?.user) {
      params = params.set('user', filters.user.toString());
    }
    if (filters?.location) {
      params = params.set('location', filters.location);
    }
    if (filters?.timestamp_from) {
      params = params.set('timestamp_from', filters.timestamp_from);
    }
    if (filters?.timestamp_to) {
      params = params.set('timestamp_to', filters.timestamp_to);
    }
    if (filters?.date_from) {
      params = params.set('date_from', filters.date_from);
    }
    if (filters?.date_to) {
      params = params.set('date_to', filters.date_to);
    }
    if (filters?.product) {
      params = params.set('product', filters.product.toString());
    }
    if (filters?.batch) {
      params = params.set('batch', filters.batch.toString());
    }
    if (filters?.pack) {
      params = params.set('pack', filters.pack.toString());
    }
    if (filters?.shipment) {
      params = params.set('shipment', filters.shipment.toString());
    }
    if (filters?.critical_only !== undefined) {
      params = params.set('critical_only', filters.critical_only.toString());
    }
    if (filters?.alert_only !== undefined) {
      params = params.set('alert_only', filters.alert_only.toString());
    }
    if (filters?.recent_days) {
      params = params.set('recent_days', filters.recent_days.toString());
    }

    return this.http
      .get<PaginatedResponse<EventListItem>>('/api/events/', { params })
      .pipe(
        tap((response) => {
          this._events.set(response.results);
          this._totalRecords.set(response.count);
          this._currentPage.set(response.current_page);
          this._pageSize.set(response.page_size);
          this._loading.set(false);
        })
      );
  }

  /**
   * Load more events and append to existing list (for infinite scroll)
   */
  loadMore(
    filters?: EventFilters,
    pagination?: PaginationParams
  ): Observable<PaginatedResponse<EventListItem>> {
    // Don't set _loading to true - we use a separate loadingMore signal in the component
    // to avoid hiding the existing events

    let params = new HttpParams();

    // Pagination params
    const page = pagination?.page || 1;
    const pageSize = pagination?.page_size || DEFAULT_PAGE_SIZE;
    params = params.set('page', page.toString());
    params = params.set('page_size', pageSize.toString());

    // Filter params (same as load)
    if (filters?.search) {
      params = params.set('search', filters.search);
    }
    if (filters?.event_type) {
      params = params.set('event_type', filters.event_type);
    }
    if (filters?.entity_type) {
      params = params.set('entity_type', filters.entity_type);
    }
    if (filters?.entity_id) {
      params = params.set('entity_id', filters.entity_id.toString());
    }
    if (filters?.severity) {
      params = params.set('severity', filters.severity);
    }
    if (filters?.user) {
      params = params.set('user', filters.user.toString());
    }
    if (filters?.location) {
      params = params.set('location', filters.location);
    }
    if (filters?.timestamp_from) {
      params = params.set('timestamp_from', filters.timestamp_from);
    }
    if (filters?.timestamp_to) {
      params = params.set('timestamp_to', filters.timestamp_to);
    }
    if (filters?.date_from) {
      params = params.set('date_from', filters.date_from);
    }
    if (filters?.date_to) {
      params = params.set('date_to', filters.date_to);
    }
    if (filters?.product) {
      params = params.set('product', filters.product.toString());
    }
    if (filters?.batch) {
      params = params.set('batch', filters.batch.toString());
    }
    if (filters?.pack) {
      params = params.set('pack', filters.pack.toString());
    }
    if (filters?.shipment) {
      params = params.set('shipment', filters.shipment.toString());
    }
    if (filters?.critical_only !== undefined) {
      params = params.set('critical_only', filters.critical_only.toString());
    }
    if (filters?.alert_only !== undefined) {
      params = params.set('alert_only', filters.alert_only.toString());
    }
    if (filters?.recent_days) {
      params = params.set('recent_days', filters.recent_days.toString());
    }

    return this.http
      .get<PaginatedResponse<EventListItem>>('/api/events/', { params })
      .pipe(
        tap((response) => {
          // Append new events to existing list
          this._events.update((existing) => [...existing, ...response.results]);
          this._totalRecords.set(response.count);
          this._currentPage.set(response.current_page);
          this._pageSize.set(response.page_size);
          // Don't modify _loading here - component manages loadingMore signal
        })
      );
  }

  /**
   * Reset events list (for when filters change)
   */
  resetEvents(): void {
    this._events.set([]);
    this._currentPage.set(1);
  }

  /**
   * Load all events (for backwards compatibility)
   */
  loadAll(filters?: EventFilters): Observable<EventListItem[]> {
    return this.load(filters, { page: 1, page_size: 100 }).pipe(
      map((response) => response.results)
    );
  }

  /**
   * Refresh events data and invalidate cache
   */
  refresh(filters?: EventFilters): void {
    this.cacheService.invalidateEntity('events');
    this.load(filters).subscribe();
  }

  /**
   * Get a single event by ID
   */
  getById(id: number): Observable<Event> {
    return this.http.get<Event>(`/api/events/${id}/`);
  }

  /**
   * Create a new event
   */
  create(data: CreateEventData): Observable<Event> {
    return this.http.post<Event>('/api/events/', data).pipe(
      tap((event) => {
        this.cacheService.invalidateEntity('events');
        // Add the new event to the list (convert to list item format)
        const listItem: EventListItem = {
          id: event.id,
          event_type: event.event_type,
          event_type_display: event.event_type_display,
          entity_type: event.entity_type,
          entity_type_display: event.entity_type_display,
          entity_id: event.entity_id,
          entity_display_name: event.entity_display_name,
          entity_info: event.entity_info,
          timestamp: event.timestamp,
          description: event.description,
          severity: event.severity,
          severity_display: event.severity_display,
          location: event.location,
          user: event.user,
          user_username: event.user_username,
          user_full_name: event.user_full_name,
          is_critical: event.is_critical,
          is_alert: event.is_alert,
          blockchain_tx_hash: event.blockchain_tx_hash,
          blockchain_block_number: event.blockchain_block_number,
          integrity_status: event.integrity_status,
          event_hash: event.event_hash,
          is_blockchain_anchored: event.is_blockchain_anchored,
          blockchain_explorer_url: event.blockchain_explorer_url,
          created_at: event.created_at,
          updated_at: event.updated_at,
          is_deleted: event.is_deleted,
        };
        this._events.update((list) => [listItem, ...list]);
      })
    );
  }

  /**
   * Update an existing event
   */
  update(id: number, data: Partial<CreateEventData>): Observable<Event> {
    return this.http.patch<Event>(`/api/events/${id}/`, data).pipe(
      tap((event) => {
        // Update the event in the list
        const listItem: EventListItem = {
          id: event.id,
          event_type: event.event_type,
          event_type_display: event.event_type_display,
          entity_type: event.entity_type,
          entity_type_display: event.entity_type_display,
          entity_id: event.entity_id,
          entity_display_name: event.entity_display_name,
          entity_info: event.entity_info,
          timestamp: event.timestamp,
          description: event.description,
          severity: event.severity,
          severity_display: event.severity_display,
          location: event.location,
          user: event.user,
          user_username: event.user_username,
          user_full_name: event.user_full_name,
          is_critical: event.is_critical,
          is_alert: event.is_alert,
          blockchain_tx_hash: event.blockchain_tx_hash,
          blockchain_block_number: event.blockchain_block_number,
          integrity_status: event.integrity_status,
          event_hash: event.event_hash,
          is_blockchain_anchored: event.is_blockchain_anchored,
          blockchain_explorer_url: event.blockchain_explorer_url,
          created_at: event.created_at,
          updated_at: event.updated_at,
          is_deleted: event.is_deleted,
        };
        this.cacheService.invalidateEntity('events');
        this._events.update((list) =>
          list.map((e) => (e.id === id ? listItem : e))
        );
      })
    );
  }

  /**
   * Delete an event (soft delete)
   */
  delete(id: number): Observable<{ message: string }> {
    return this.http
      .delete<{ message: string }>(`/api/events/${id}/delete/`)
      .pipe(
        tap(() => {
          this.cacheService.invalidateEntity('events');
          // Remove the event from the list or mark as deleted
          this._events.update((list) =>
            list.map((e) => (e.id === id ? { ...e, is_deleted: true } : e))
          );
        })
      );
  }

  /**
   * Get available event types
   */
  getEventTypes(): { value: EventType; label: string }[] {
    return [
      { value: 'created', label: 'Created' },
      { value: 'updated', label: 'Updated' },
      { value: 'deleted', label: 'Deleted' },
      { value: 'status_changed', label: 'Status Changed' },
      { value: 'location_changed', label: 'Location Changed' },
      { value: 'quality_check', label: 'Quality Check' },
      { value: 'temperature_alert', label: 'Temperature Alert' },
      { value: 'shipped', label: 'Shipped' },
      { value: 'delivered', label: 'Delivered' },
      { value: 'returned', label: 'Returned' },
      { value: 'damaged', label: 'Damaged' },
      { value: 'expired', label: 'Expired' },
      { value: 'recalled', label: 'Recalled' },
      { value: 'inventory_count', label: 'Inventory Count' },
      { value: 'maintenance', label: 'Maintenance' },
      { value: 'calibration', label: 'Calibration' },
      { value: 'user_action', label: 'User Action' },
      { value: 'system_action', label: 'System Action' },
      { value: 'alert', label: 'Alert' },
      { value: 'warning', label: 'Warning' },
      { value: 'error', label: 'Error' },
      { value: 'other', label: 'Other' },
    ];
  }

  /**
   * Get available entity types
   */
  getEntityTypes(): { value: EntityType; label: string }[] {
    return [
      { value: 'product', label: 'Product' },
      { value: 'batch', label: 'Batch' },
      { value: 'pack', label: 'Pack' },
      { value: 'shipment', label: 'Shipment' },
      { value: 'user', label: 'User' },
      { value: 'device', label: 'Device' },
      { value: 'location', label: 'Location' },
      { value: 'system', label: 'System' },
    ];
  }

  /**
   * Get available severity levels
   */
  getSeverityLevels(): { value: SeverityLevel; label: string }[] {
    return [
      { value: 'info', label: 'Information' },
      { value: 'low', label: 'Low' },
      { value: 'medium', label: 'Medium' },
      { value: 'high', label: 'High' },
      { value: 'critical', label: 'Critical' },
    ];
  }

  /**
   * Get recent days options for filtering
   */
  getRecentDaysOptions(): { value: number; label: string }[] {
    return [
      { value: 1, label: 'Last 24 hours' },
      { value: 3, label: 'Last 3 days' },
      { value: 7, label: 'Last week' },
      { value: 14, label: 'Last 2 weeks' },
      { value: 30, label: 'Last month' },
      { value: 90, label: 'Last 3 months' },
    ];
  }

  /**
   * Get severity color for UI display
   */
  getSeverityColor(severity: SeverityLevel): string {
    switch (severity) {
      case 'critical':
        return 'red';
      case 'high':
        return 'orange';
      case 'medium':
        return 'yellow';
      case 'low':
        return 'blue';
      case 'info':
      default:
        return 'gray';
    }
  }

  /**
   * Get event type icon
   */
  getEventTypeIcon(eventType: EventType): string {
    switch (eventType) {
      case 'created':
        return 'pi-plus-circle';
      case 'updated':
        return 'pi-pencil';
      case 'deleted':
        return 'pi-trash';
      case 'status_changed':
        return 'pi-refresh';
      case 'location_changed':
        return 'pi-map-marker';
      case 'quality_check':
        return 'pi-check-circle';
      case 'temperature_alert':
        return 'pi-exclamation-triangle';
      case 'shipped':
        return 'pi-truck';
      case 'delivered':
        return 'pi-check';
      case 'returned':
        return 'pi-undo';
      case 'damaged':
        return 'pi-exclamation-circle';
      case 'expired':
        return 'pi-clock';
      case 'recalled':
        return 'pi-ban';
      case 'inventory_count':
        return 'pi-list';
      case 'maintenance':
        return 'pi-wrench';
      case 'calibration':
        return 'pi-cog';
      case 'user_action':
        return 'pi-user';
      case 'system_action':
        return 'pi-server';
      case 'alert':
        return 'pi-bell';
      case 'warning':
        return 'pi-exclamation-triangle';
      case 'error':
        return 'pi-times-circle';
      case 'other':
      default:
        return 'pi-info-circle';
    }
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleString();
  }

  /**
   * Get relative time string (e.g., "2 hours ago")
   */
  getRelativeTime(timestamp: string): string {
    const now = new Date();
    const eventTime = new Date(timestamp);
    const diffMs = now.getTime() - eventTime.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) {
      return 'Just now';
    } else if (diffMinutes < 60) {
      return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      return eventTime.toLocaleDateString();
    }
  }

  /**
   * Check if an event is recent (within last 24 hours)
   */
  isRecent(timestamp: string): boolean {
    const now = new Date();
    const eventTime = new Date(timestamp);
    const diffMs = now.getTime() - eventTime.getTime();
    const diffHours = diffMs / (1000 * 60 * 60);
    return diffHours <= 24;
  }

  // Blockchain integrity methods

  /**
   * Anchor an event to blockchain
   */
  anchorEvent(id: number): Observable<{
    message: string;
    tx_hash: string;
    block_number: number;
    explorer_url: string;
  }> {
    return this.http.post<{
      message: string;
      tx_hash: string;
      block_number: number;
      explorer_url: string;
    }>(`/api/events/${id}/anchor/`, {});
  }

  /**
   * Verify blockchain anchoring for an event
   */
  verifyBlockchainAnchoring(id: number): Observable<{
    verified: boolean;
    integrity_verified: boolean;
    tx_hash: string;
    block_number: number;
    stored_hash: string;
    computed_hash: string;
    network: string;
    timestamp: string;
    error?: string;
  }> {
    return this.http.get<{
      verified: boolean;
      integrity_verified: boolean;
      tx_hash: string;
      block_number: number;
      stored_hash: string;
      computed_hash: string;
      network: string;
      timestamp: string;
      error?: string;
    }>(`/api/events/${id}/verify/`);
  }

  /**
   * Verify event data integrity (without blockchain check)
   */
  verifyIntegrity(id: number): Observable<{
    integrity_verified: boolean;
    stored_hash: string;
    computed_hash: string;
    event_id: number;
    blockchain_anchored: boolean;
    integrity_status: IntegrityStatus;
  }> {
    return this.http.get<{
      integrity_verified: boolean;
      stored_hash: string;
      computed_hash: string;
      event_id: number;
      blockchain_anchored: boolean;
      integrity_status: IntegrityStatus;
    }>(`/api/events/${id}/integrity/`);
  }

  /**
   * Get integrity status color for UI display
   */
  getIntegrityStatusColor(
    status: IntegrityStatus
  ): 'success' | 'warning' | 'danger' | 'info' {
    switch (status) {
      case 'anchored':
        return 'success';
      case 'failed':
        return 'danger';
      case 'pending':
      default:
        return 'warning';
    }
  }

  /**
   * Get integrity status icon
   */
  getIntegrityStatusIcon(status: IntegrityStatus): string {
    switch (status) {
      case 'anchored':
        return 'pi-shield';
      case 'failed':
        return 'pi-times-circle';
      case 'pending':
      default:
        return 'pi-clock';
    }
  }

  /**
   * Get integrity status display text
   */
  getIntegrityStatusText(status: IntegrityStatus): string {
    switch (status) {
      case 'anchored':
        return 'Blockchain Verified';
      case 'failed':
        return 'Verification Failed';
      case 'pending':
      default:
        return 'Verification Pending';
    }
  }
}
