import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, map } from 'rxjs';
import {
  PaginatedResponse,
  PaginationParams,
  DEFAULT_PAGE_SIZE,
} from '../models/pagination.model';
import { CacheService } from './cache.service';

export type PackStatus =
  | 'active'
  | 'damaged'
  | 'recalled'
  | 'shipped'
  | 'delivered'
  | 'returned'
  | 'quarantined'
  | 'destroyed';
export type PackType =
  | 'bottle'
  | 'box'
  | 'blister'
  | 'vial'
  | 'tube'
  | 'sachet'
  | 'ampoule'
  | 'syringe'
  | 'inhaler'
  | 'other';

export interface Pack {
  id: number;
  batch: number;
  batch_lot_number: string;
  product_name: string;
  product_gtin: string;
  serial_number: string;
  pack_size: number;
  pack_type: PackType;
  manufacturing_date?: string;
  expiry_date?: string;
  effective_manufacturing_date: string;
  effective_expiry_date: string;
  status: PackStatus;
  location?: string;
  warehouse_section?: string;
  quality_control_notes?: string;
  quality_control_passed: boolean;
  regulatory_code?: string;
  customer_reference?: string;
  shipped_date?: string;
  delivered_date?: string;
  tracking_number?: string;
  is_expired: boolean;
  days_until_expiry: number;
  is_shipped: boolean;
  is_delivered: boolean;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
}

export interface PackListItem {
  id: number;
  batch: number;
  batch_lot_number: string;
  product_name: string;
  product_gtin: string;
  serial_number: string;
  pack_size: number;
  pack_type: PackType;
  status: PackStatus;
  location?: string;
  effective_manufacturing_date: string;
  effective_expiry_date: string;
  is_expired: boolean;
  days_until_expiry: number;
  quality_control_passed: boolean;
  is_shipped: boolean;
  is_delivered: boolean;
  shipped_date?: string;
  delivered_date?: string;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
}

export interface PackFilters {
  search?: string;
  batch?: number;
  product?: number;
  status?: PackStatus;
  pack_type?: PackType;
  location?: string;
  expiry_from?: string;
  expiry_to?: string;
  shipped_from?: string;
  shipped_to?: string;
  qc_passed?: boolean;
  shipping_status?: 'shipped' | 'delivered' | 'not_shipped';
  expiry_status?: 'expired' | 'expiring_soon' | 'active';
}

export interface CreatePackData {
  batch: number;
  serial_number: string;
  pack_size: number;
  pack_type: PackType;
  manufacturing_date?: string;
  expiry_date?: string;
  status?: PackStatus;
  location?: string;
  warehouse_section?: string;
  quality_control_notes?: string;
  quality_control_passed?: boolean;
  regulatory_code?: string;
  customer_reference?: string;
  shipped_date?: string;
  delivered_date?: string;
  tracking_number?: string;
}

@Injectable({ providedIn: 'root' })
export class PackService {
  private http = inject(HttpClient);
  private cacheService = inject(CacheService);
  private _packs = signal<PackListItem[]>([]);
  private _loading = signal(false);
  private _totalRecords = signal(0);
  private _currentPage = signal(1);
  private _pageSize = signal(DEFAULT_PAGE_SIZE);

  readonly packs = computed(() =>
    this._packs().filter((pack) => !pack.is_deleted)
  );
  readonly loading = computed(() => this._loading());
  readonly totalRecords = computed(() => this._totalRecords());
  readonly currentPage = computed(() => this._currentPage());
  readonly pageSize = computed(() => this._pageSize());

  /**
   * Load packs with optional filters and pagination
   */
  load(
    filters?: PackFilters,
    pagination?: PaginationParams
  ): Observable<PaginatedResponse<PackListItem>> {
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
    if (filters?.batch) {
      params = params.set('batch', filters.batch.toString());
    }
    if (filters?.product) {
      params = params.set('product', filters.product.toString());
    }
    if (filters?.status) {
      params = params.set('status', filters.status);
    }
    if (filters?.pack_type) {
      params = params.set('pack_type', filters.pack_type);
    }
    if (filters?.location) {
      params = params.set('location', filters.location);
    }
    if (filters?.expiry_from) {
      params = params.set('expiry_from', filters.expiry_from);
    }
    if (filters?.expiry_to) {
      params = params.set('expiry_to', filters.expiry_to);
    }
    if (filters?.shipped_from) {
      params = params.set('shipped_from', filters.shipped_from);
    }
    if (filters?.shipped_to) {
      params = params.set('shipped_to', filters.shipped_to);
    }
    if (filters?.qc_passed !== undefined) {
      params = params.set('qc_passed', filters.qc_passed.toString());
    }
    if (filters?.shipping_status) {
      params = params.set('shipping_status', filters.shipping_status);
    }
    if (filters?.expiry_status) {
      params = params.set('expiry_status', filters.expiry_status);
    }

    return this.http
      .get<PaginatedResponse<PackListItem>>('/api/packs/', { params })
      .pipe(
        tap((response) => {
          this._packs.set(response.results);
          this._totalRecords.set(response.count);
          this._currentPage.set(response.current_page);
          this._pageSize.set(response.page_size);
          this._loading.set(false);
        })
      );
  }

  /**
   * Load all packs (legacy method for backward compatibility)
   */
  loadAll(filters?: PackFilters): Observable<PackListItem[]> {
    return this.load(filters, { page: 1, page_size: 100 }).pipe(
      map((response) => response.results)
    );
  }

  /**
   * Refresh packs data and invalidate cache
   */
  refresh(filters?: PackFilters): void {
    this.cacheService.invalidateEntity('packs');
    this.load(filters).subscribe();
  }

  /**
   * Get a single pack by ID
   */
  getById(id: number): Observable<Pack> {
    return this.http.get<Pack>(`/api/packs/${id}/`);
  }

  /**
   * Create a new pack
   */
  create(data: CreatePackData): Observable<Pack> {
    return this.http.post<Pack>('/api/packs/', data).pipe(
      tap((pack) => {
        this.cacheService.invalidateEntity('packs');
        // Add the new pack to the list (convert to list item format)
        const listItem: PackListItem = {
          id: pack.id,
          batch: pack.batch,
          batch_lot_number: pack.batch_lot_number,
          product_name: pack.product_name,
          product_gtin: pack.product_gtin,
          serial_number: pack.serial_number,
          pack_size: pack.pack_size,
          pack_type: pack.pack_type,
          status: pack.status,
          location: pack.location,
          effective_manufacturing_date: pack.effective_manufacturing_date,
          effective_expiry_date: pack.effective_expiry_date,
          is_expired: pack.is_expired,
          days_until_expiry: pack.days_until_expiry,
          quality_control_passed: pack.quality_control_passed,
          is_shipped: pack.is_shipped,
          is_delivered: pack.is_delivered,
          shipped_date: pack.shipped_date,
          delivered_date: pack.delivered_date,
          created_at: pack.created_at,
          updated_at: pack.updated_at,
          is_deleted: pack.is_deleted,
        };
        this._packs.update((list) => [...list, listItem]);
      })
    );
  }

  /**
   * Update an existing pack
   */
  update(id: number, data: Partial<CreatePackData>): Observable<Pack> {
    return this.http.patch<Pack>(`/api/packs/${id}/`, data).pipe(
      tap((pack) => {
        this.cacheService.invalidateEntity('packs');
        // Update the pack in the list
        const listItem: PackListItem = {
          id: pack.id,
          batch: pack.batch,
          batch_lot_number: pack.batch_lot_number,
          product_name: pack.product_name,
          product_gtin: pack.product_gtin,
          serial_number: pack.serial_number,
          pack_size: pack.pack_size,
          pack_type: pack.pack_type,
          status: pack.status,
          location: pack.location,
          effective_manufacturing_date: pack.effective_manufacturing_date,
          effective_expiry_date: pack.effective_expiry_date,
          is_expired: pack.is_expired,
          days_until_expiry: pack.days_until_expiry,
          quality_control_passed: pack.quality_control_passed,
          is_shipped: pack.is_shipped,
          is_delivered: pack.is_delivered,
          shipped_date: pack.shipped_date,
          delivered_date: pack.delivered_date,
          created_at: pack.created_at,
          updated_at: pack.updated_at,
          is_deleted: pack.is_deleted,
        };
        this._packs.update((list) =>
          list.map((p) => (p.id === id ? listItem : p))
        );
      })
    );
  }

  /**
   * Delete a pack (soft delete)
   */
  delete(id: number): Observable<{ message: string }> {
    return this.http
      .delete<{ message: string }>(`/api/packs/${id}/delete/`)
      .pipe(
        tap(() => {
          this.cacheService.invalidateEntity('packs');
          // Remove the pack from the list completely
          this._packs.update((list) => list.filter((p) => p.id !== id));
        })
      );
  }

  /**
   * Get available pack types
   */
  getPackTypes(): { value: PackType; label: string }[] {
    return [
      { value: 'bottle', label: 'Bottle' },
      { value: 'box', label: 'Box' },
      { value: 'blister', label: 'Blister Pack' },
      { value: 'vial', label: 'Vial' },
      { value: 'tube', label: 'Tube' },
      { value: 'sachet', label: 'Sachet' },
      { value: 'ampoule', label: 'Ampoule' },
      { value: 'syringe', label: 'Syringe' },
      { value: 'inhaler', label: 'Inhaler' },
      { value: 'other', label: 'Other' },
    ];
  }

  /**
   * Get available pack statuses
   */
  getPackStatuses(): { value: PackStatus; label: string }[] {
    return [
      { value: 'active', label: 'Active' },
      { value: 'damaged', label: 'Damaged' },
      { value: 'recalled', label: 'Recalled' },
      { value: 'shipped', label: 'Shipped' },
      { value: 'delivered', label: 'Delivered' },
      { value: 'returned', label: 'Returned' },
      { value: 'quarantined', label: 'Quarantined' },
      { value: 'destroyed', label: 'Destroyed' },
    ];
  }

  /**
   * Get shipping status options for filtering
   */
  getShippingStatusOptions(): { value: string; label: string }[] {
    return [
      { value: 'not_shipped', label: 'Not Shipped' },
      { value: 'shipped', label: 'Shipped' },
      { value: 'delivered', label: 'Delivered' },
    ];
  }

  /**
   * Get expiry status options for filtering
   */
  getExpiryStatusOptions(): { value: string; label: string }[] {
    return [
      { value: 'active', label: 'Active (Not Expired)' },
      { value: 'expiring_soon', label: 'Expiring Soon (30 days)' },
      { value: 'expired', label: 'Expired' },
    ];
  }
}
