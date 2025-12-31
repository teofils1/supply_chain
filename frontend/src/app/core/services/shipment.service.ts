import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, map } from 'rxjs';
import {
  PaginatedResponse,
  PaginationParams,
  DEFAULT_PAGE_SIZE,
} from '../models/pagination.model';
import { CacheService } from './cache.service';

export type ShipmentStatus =
  | 'pending'
  | 'confirmed'
  | 'picked_up'
  | 'in_transit'
  | 'out_for_delivery'
  | 'delivered'
  | 'returned'
  | 'cancelled'
  | 'lost'
  | 'damaged';
export type Carrier =
  | 'fedex'
  | 'ups'
  | 'dhl'
  | 'usps'
  | 'amazon'
  | 'local'
  | 'internal'
  | 'other';
export type ServiceType =
  | 'standard'
  | 'express'
  | 'overnight'
  | 'same_day'
  | 'ground'
  | 'air'
  | 'freight'
  | 'cold_chain';
export type TemperatureRequirement =
  | 'ambient'
  | 'cool'
  | 'frozen'
  | 'ultra_cold'
  | 'controlled';

export interface ShipmentPack {
  id: number;
  pack: number;
  pack_serial_number: string;
  pack_size: number;
  pack_type: string;
  batch_lot_number: string;
  product_name: string;
  product_gtin: string;
  quantity_shipped: number;
  notes?: string;
  created_at: string;
}

export interface PackSummary {
  product: string;
  count: number;
}

export interface Shipment {
  id: number;
  tracking_number: string;
  status: ShipmentStatus;
  carrier: Carrier;
  service_type: ServiceType;
  origin_name: string;
  origin_address_line1: string;
  origin_address_line2?: string;
  origin_city: string;
  origin_state: string;
  origin_postal_code: string;
  origin_country: string;
  origin_address: string;
  destination_name: string;
  destination_address_line1: string;
  destination_address_line2?: string;
  destination_city: string;
  destination_state: string;
  destination_postal_code: string;
  destination_country: string;
  destination_address: string;
  shipped_date?: string;
  estimated_delivery_date?: string;
  actual_delivery_date?: string;
  temperature_requirement: TemperatureRequirement;
  special_handling_required: boolean;
  special_instructions?: string;
  shipping_cost?: number;
  currency: string;
  billing_reference?: string;
  notes?: string;
  external_tracking_url?: string;
  pack_count: number;
  total_pack_size: number;
  shipment_packs: ShipmentPack[];
  is_delivered: boolean;
  is_in_transit: boolean;
  is_completed: boolean;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
}

export interface ShipmentListItem {
  id: number;
  tracking_number: string;
  status: ShipmentStatus;
  carrier: Carrier;
  service_type: ServiceType;
  origin_name: string;
  origin_address: string;
  destination_name: string;
  destination_address: string;
  shipped_date?: string;
  estimated_delivery_date?: string;
  actual_delivery_date?: string;
  temperature_requirement: TemperatureRequirement;
  shipping_cost?: number;
  currency: string;
  pack_count: number;
  total_pack_size: number;
  pack_summary: PackSummary[];
  is_delivered: boolean;
  is_in_transit: boolean;
  is_completed: boolean;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
}

export interface ShipmentFilters {
  search?: string;
  status?: ShipmentStatus;
  carrier?: Carrier;
  service_type?: ServiceType;
  temperature_requirement?: TemperatureRequirement;
  origin_city?: string;
  origin_state?: string;
  destination_city?: string;
  destination_state?: string;
  shipped_from?: string;
  shipped_to?: string;
  estimated_delivery_from?: string;
  estimated_delivery_to?: string;
  pack?: number;
  batch?: number;
  product?: number;
  delivery_status?: 'delivered' | 'in_transit' | 'pending' | 'overdue';
  special_handling?: boolean;
}

export interface CreateShipmentData {
  tracking_number: string;
  status?: ShipmentStatus;
  carrier: Carrier;
  service_type: ServiceType;
  origin_name: string;
  origin_address_line1: string;
  origin_address_line2?: string;
  origin_city: string;
  origin_state: string;
  origin_postal_code: string;
  origin_country: string;
  destination_name: string;
  destination_address_line1: string;
  destination_address_line2?: string;
  destination_city: string;
  destination_state: string;
  destination_postal_code: string;
  destination_country: string;
  shipped_date?: string;
  estimated_delivery_date?: string;
  actual_delivery_date?: string;
  temperature_requirement?: TemperatureRequirement;
  special_handling_required?: boolean;
  special_instructions?: string;
  shipping_cost?: number;
  currency?: string;
  billing_reference?: string;
  notes?: string;
  external_tracking_url?: string;
  pack_ids: number[];
}

@Injectable({ providedIn: 'root' })
export class ShipmentService {
  private http = inject(HttpClient);
  private cacheService = inject(CacheService);
  private _shipments = signal<ShipmentListItem[]>([]);
  private _loading = signal(false);
  private _totalRecords = signal(0);
  private _currentPage = signal(1);
  private _pageSize = signal(DEFAULT_PAGE_SIZE);

  readonly shipments = computed(() => this._shipments());
  readonly loading = computed(() => this._loading());
  readonly totalRecords = computed(() => this._totalRecords());
  readonly currentPage = computed(() => this._currentPage());
  readonly pageSize = computed(() => this._pageSize());

  /**
   * Load shipments with optional filters and pagination
   */
  load(
    filters?: ShipmentFilters,
    pagination?: PaginationParams
  ): Observable<PaginatedResponse<ShipmentListItem>> {
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
    if (filters?.status) {
      params = params.set('status', filters.status);
    }
    if (filters?.carrier) {
      params = params.set('carrier', filters.carrier);
    }
    if (filters?.service_type) {
      params = params.set('service_type', filters.service_type);
    }
    if (filters?.temperature_requirement) {
      params = params.set(
        'temperature_requirement',
        filters.temperature_requirement
      );
    }
    if (filters?.origin_city) {
      params = params.set('origin_city', filters.origin_city);
    }
    if (filters?.origin_state) {
      params = params.set('origin_state', filters.origin_state);
    }
    if (filters?.destination_city) {
      params = params.set('destination_city', filters.destination_city);
    }
    if (filters?.destination_state) {
      params = params.set('destination_state', filters.destination_state);
    }
    if (filters?.shipped_from) {
      params = params.set('shipped_from', filters.shipped_from);
    }
    if (filters?.shipped_to) {
      params = params.set('shipped_to', filters.shipped_to);
    }
    if (filters?.estimated_delivery_from) {
      params = params.set(
        'estimated_delivery_from',
        filters.estimated_delivery_from
      );
    }
    if (filters?.estimated_delivery_to) {
      params = params.set(
        'estimated_delivery_to',
        filters.estimated_delivery_to
      );
    }
    if (filters?.pack) {
      params = params.set('pack', filters.pack.toString());
    }
    if (filters?.batch) {
      params = params.set('batch', filters.batch.toString());
    }
    if (filters?.product) {
      params = params.set('product', filters.product.toString());
    }
    if (filters?.delivery_status) {
      params = params.set('delivery_status', filters.delivery_status);
    }
    if (filters?.special_handling !== undefined) {
      params = params.set(
        'special_handling',
        filters.special_handling.toString()
      );
    }

    return this.http
      .get<PaginatedResponse<ShipmentListItem>>('/api/shipments/', { params })
      .pipe(
        tap((response) => {
          this._shipments.set(response.results);
          this._totalRecords.set(response.count);
          this._currentPage.set(response.current_page);
          this._pageSize.set(response.page_size);
          this._loading.set(false);
        })
      );
  }

  /**
   * Load all shipments (legacy method for backward compatibility)
   */
  loadAll(filters?: ShipmentFilters): Observable<ShipmentListItem[]> {
    return this.load(filters, { page: 1, page_size: 100 }).pipe(
      map((response) => response.results)
    );
  }

  /**
   * Refresh shipments data and invalidate cache
   */
  refresh(filters?: ShipmentFilters): void {
    this.cacheService.invalidateEntity('shipments');
    this.load(filters).subscribe();
  }

  /**
   * Get a single shipment by ID
   */
  getById(id: number): Observable<Shipment> {
    return this.http.get<Shipment>(`/api/shipments/${id}/`);
  }

  /**
   * Create a new shipment
   */
  create(data: CreateShipmentData): Observable<Shipment> {
    return this.http.post<Shipment>('/api/shipments/', data).pipe(
      tap((shipment) => {
        this.cacheService.invalidateEntity('shipments');
        // Add the new shipment to the list (convert to list item format)
        const listItem: ShipmentListItem = {
          id: shipment.id,
          tracking_number: shipment.tracking_number,
          status: shipment.status,
          carrier: shipment.carrier,
          service_type: shipment.service_type,
          origin_name: shipment.origin_name,
          origin_address: shipment.origin_address,
          destination_name: shipment.destination_name,
          destination_address: shipment.destination_address,
          shipped_date: shipment.shipped_date,
          estimated_delivery_date: shipment.estimated_delivery_date,
          actual_delivery_date: shipment.actual_delivery_date,
          temperature_requirement: shipment.temperature_requirement,
          shipping_cost: shipment.shipping_cost,
          currency: shipment.currency,
          pack_count: shipment.pack_count,
          total_pack_size: shipment.total_pack_size,
          pack_summary: this.generatePackSummary(shipment.shipment_packs),
          is_delivered: shipment.is_delivered,
          is_in_transit: shipment.is_in_transit,
          is_completed: shipment.is_completed,
          created_at: shipment.created_at,
          updated_at: shipment.updated_at,
          is_deleted: shipment.is_deleted,
        };
        this._shipments.update((list) => [...list, listItem]);
      })
    );
  }

  /**
   * Update an existing shipment
   */
  update(id: number, data: Partial<CreateShipmentData>): Observable<Shipment> {
    return this.http.patch<Shipment>(`/api/shipments/${id}/`, data).pipe(
      tap((shipment) => {
        this.cacheService.invalidateEntity('shipments');
        // Update the shipment in the list
        const listItem: ShipmentListItem = {
          id: shipment.id,
          tracking_number: shipment.tracking_number,
          status: shipment.status,
          carrier: shipment.carrier,
          service_type: shipment.service_type,
          origin_name: shipment.origin_name,
          origin_address: shipment.origin_address,
          destination_name: shipment.destination_name,
          destination_address: shipment.destination_address,
          shipped_date: shipment.shipped_date,
          estimated_delivery_date: shipment.estimated_delivery_date,
          actual_delivery_date: shipment.actual_delivery_date,
          temperature_requirement: shipment.temperature_requirement,
          shipping_cost: shipment.shipping_cost,
          currency: shipment.currency,
          pack_count: shipment.pack_count,
          total_pack_size: shipment.total_pack_size,
          pack_summary: this.generatePackSummary(shipment.shipment_packs),
          is_delivered: shipment.is_delivered,
          is_in_transit: shipment.is_in_transit,
          is_completed: shipment.is_completed,
          created_at: shipment.created_at,
          updated_at: shipment.updated_at,
          is_deleted: shipment.is_deleted,
        };
        this._shipments.update((list) =>
          list.map((s) => (s.id === id ? listItem : s))
        );
      })
    );
  }

  /**
   * Delete a shipment (soft delete)
   */
  delete(id: number): Observable<{ message: string }> {
    return this.http
      .delete<{ message: string }>(`/api/shipments/${id}/delete/`)
      .pipe(
        tap(() => {
          this.cacheService.invalidateEntity('shipments');
          // Remove the shipment from the list or mark as deleted
          this._shipments.update((list) =>
            list.map((s) => (s.id === id ? { ...s, is_deleted: true } : s))
          );
        })
      );
  }

  /**
   * Generate pack summary from shipment packs
   */
  private generatePackSummary(shipmentPacks: ShipmentPack[]): PackSummary[] {
    const products: { [key: string]: number } = {};

    shipmentPacks.forEach((sp) => {
      if (products[sp.product_name]) {
        products[sp.product_name]++;
      } else {
        products[sp.product_name] = 1;
      }
    });

    return Object.entries(products).map(([product, count]) => ({
      product,
      count,
    }));
  }

  /**
   * Get available shipment statuses
   */
  getShipmentStatuses(): { value: ShipmentStatus; label: string }[] {
    return [
      { value: 'pending', label: 'Pending' },
      { value: 'confirmed', label: 'Confirmed' },
      { value: 'picked_up', label: 'Picked Up' },
      { value: 'in_transit', label: 'In Transit' },
      { value: 'out_for_delivery', label: 'Out for Delivery' },
      { value: 'delivered', label: 'Delivered' },
      { value: 'returned', label: 'Returned' },
      { value: 'cancelled', label: 'Cancelled' },
      { value: 'lost', label: 'Lost' },
      { value: 'damaged', label: 'Damaged' },
    ];
  }

  /**
   * Get available carriers
   */
  getCarriers(): { value: Carrier; label: string }[] {
    return [
      { value: 'fedex', label: 'FedEx' },
      { value: 'ups', label: 'UPS' },
      { value: 'dhl', label: 'DHL' },
      { value: 'usps', label: 'USPS' },
      { value: 'amazon', label: 'Amazon Logistics' },
      { value: 'local', label: 'Local Courier' },
      { value: 'internal', label: 'Internal Transport' },
      { value: 'other', label: 'Other' },
    ];
  }

  /**
   * Get available service types
   */
  getServiceTypes(): { value: ServiceType; label: string }[] {
    return [
      { value: 'standard', label: 'Standard' },
      { value: 'express', label: 'Express' },
      { value: 'overnight', label: 'Overnight' },
      { value: 'same_day', label: 'Same Day' },
      { value: 'ground', label: 'Ground' },
      { value: 'air', label: 'Air' },
      { value: 'freight', label: 'Freight' },
      { value: 'cold_chain', label: 'Cold Chain' },
    ];
  }

  /**
   * Get available temperature requirements
   */
  getTemperatureRequirements(): {
    value: TemperatureRequirement;
    label: string;
  }[] {
    return [
      { value: 'ambient', label: 'Ambient (15-25°C)' },
      { value: 'cool', label: 'Cool (2-8°C)' },
      { value: 'frozen', label: 'Frozen (-15 to -25°C)' },
      { value: 'ultra_cold', label: 'Ultra Cold (-70 to -80°C)' },
      { value: 'controlled', label: 'Controlled Temperature' },
    ];
  }

  /**
   * Get delivery status options for filtering
   */
  getDeliveryStatusOptions(): { value: string; label: string }[] {
    return [
      { value: 'pending', label: 'Pending' },
      { value: 'in_transit', label: 'In Transit' },
      { value: 'delivered', label: 'Delivered' },
      { value: 'overdue', label: 'Overdue' },
    ];
  }

  /**
   * Get special handling options
   */
  getSpecialHandlingOptions(): { value: boolean; label: string }[] {
    return [
      { value: true, label: 'Required' },
      { value: false, label: 'Not Required' },
    ];
  }
}
