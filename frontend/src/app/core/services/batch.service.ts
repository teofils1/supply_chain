import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, map } from 'rxjs';
import {
  PaginatedResponse,
  PaginationParams,
  DEFAULT_PAGE_SIZE,
} from '../models/pagination.model';
import { CacheService } from './cache.service';

export type BatchStatus =
  | 'active'
  | 'expired'
  | 'recalled'
  | 'quarantined'
  | 'released'
  | 'destroyed';

export interface Batch {
  id: number;
  product: number;
  product_name: string;
  product_gtin: string;
  lot_number: string;
  manufacturing_date: string;
  expiry_date: string;
  quantity_produced: number;
  available_quantity: number;
  quantity_used: number;
  manufacturing_location?: string;
  manufacturing_facility?: string;
  status: BatchStatus;
  quality_control_notes?: string;
  quality_control_passed: boolean;
  batch_size?: string;
  supplier_batch_number?: string;
  regulatory_approval_number?: string;
  certificate_of_analysis?: string;
  is_expired: boolean;
  days_until_expiry: number;
  age_in_days?: number;
  shelf_life_remaining_percent: number;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
}

export interface BatchListItem {
  id: number;
  product: number;
  product_name: string;
  product_gtin: string;
  lot_number: string;
  manufacturing_date: string;
  expiry_date: string;
  quantity_produced: number;
  available_quantity: number;
  quantity_used: number;
  manufacturing_location?: string;
  status: BatchStatus;
  quality_control_passed: boolean;
  is_expired: boolean;
  days_until_expiry: number;
  shelf_life_remaining_percent: number;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
}

export interface BatchFilters {
  search?: string;
  product?: number;
  status?: BatchStatus;
  location?: string;
  expiry_from?: string;
  expiry_to?: string;
  mfg_from?: string;
  mfg_to?: string;
  qc_passed?: boolean;
  expiry_status?: 'expired' | 'expiring_soon' | 'active';
}

export interface CreateBatchData {
  product: number;
  lot_number: string;
  manufacturing_date: string;
  expiry_date: string;
  quantity_produced: number;
  manufacturing_location?: string;
  manufacturing_facility?: string;
  status?: BatchStatus;
  quality_control_notes?: string;
  quality_control_passed?: boolean;
  batch_size?: string;
  supplier_batch_number?: string;
  regulatory_approval_number?: string;
  certificate_of_analysis?: string;
}

@Injectable({ providedIn: 'root' })
export class BatchService {
  private http = inject(HttpClient);
  private cacheService = inject(CacheService);
  private _batches = signal<BatchListItem[]>([]);
  private _loading = signal(false);
  private _totalRecords = signal(0);
  private _currentPage = signal(1);
  private _pageSize = signal(DEFAULT_PAGE_SIZE);

  readonly batches = computed(() => this._batches());
  readonly loading = computed(() => this._loading());
  readonly totalRecords = computed(() => this._totalRecords());
  readonly currentPage = computed(() => this._currentPage());
  readonly pageSize = computed(() => this._pageSize());

  /**
   * Load batches with optional filters and pagination
   */
  load(
    filters?: BatchFilters,
    pagination?: PaginationParams
  ): Observable<PaginatedResponse<BatchListItem>> {
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
    if (filters?.product) {
      params = params.set('product', filters.product.toString());
    }
    if (filters?.status) {
      params = params.set('status', filters.status);
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
    if (filters?.mfg_from) {
      params = params.set('mfg_from', filters.mfg_from);
    }
    if (filters?.mfg_to) {
      params = params.set('mfg_to', filters.mfg_to);
    }
    if (filters?.qc_passed !== undefined) {
      params = params.set('qc_passed', filters.qc_passed.toString());
    }
    if (filters?.expiry_status) {
      params = params.set('expiry_status', filters.expiry_status);
    }

    return this.http
      .get<PaginatedResponse<BatchListItem>>('/api/batches/', { params })
      .pipe(
        tap((response) => {
          this._batches.set(response.results);
          this._totalRecords.set(response.count);
          this._currentPage.set(response.current_page);
          this._pageSize.set(response.page_size);
          this._loading.set(false);
        })
      );
  }

  /**
   * Load all batches (legacy method for backward compatibility)
   */
  loadAll(filters?: BatchFilters): Observable<BatchListItem[]> {
    return this.load(filters, { page: 1, page_size: 100 }).pipe(
      map((response) => response.results)
    );
  }

  /**
   * Get a single batch by ID
   */
  getById(id: number): Observable<Batch> {
    return this.http.get<Batch>(`/api/batches/${id}/`);
  }

  /**
   * Create a new batch
   */
  create(data: CreateBatchData): Observable<Batch> {
    return this.http.post<Batch>('/api/batches/', data).pipe(
      tap((batch) => {
        // Add the new batch to the list (convert to list item format)
        const listItem: BatchListItem = {
          id: batch.id,
          product: batch.product,
          product_name: batch.product_name,
          product_gtin: batch.product_gtin,
          lot_number: batch.lot_number,
          manufacturing_date: batch.manufacturing_date,
          expiry_date: batch.expiry_date,
          quantity_produced: batch.quantity_produced,
          available_quantity: batch.available_quantity,
          quantity_used: batch.quantity_used,
          manufacturing_location: batch.manufacturing_location,
          status: batch.status,
          quality_control_passed: batch.quality_control_passed,
          is_expired: batch.is_expired,
          days_until_expiry: batch.days_until_expiry,
          shelf_life_remaining_percent: batch.shelf_life_remaining_percent,
          created_at: batch.created_at,
          updated_at: batch.updated_at,
          is_deleted: batch.is_deleted,
        };
        this._batches.update((list) => [...list, listItem]);
        this.cacheService.invalidateEntity('batches');
      })
    );
  }

  /**
   * Update an existing batch
   */
  update(id: number, data: Partial<CreateBatchData>): Observable<Batch> {
    return this.http.patch<Batch>(`/api/batches/${id}/`, data).pipe(
      tap((batch) => {
        // Update the batch in the list
        const listItem: BatchListItem = {
          id: batch.id,
          product: batch.product,
          product_name: batch.product_name,
          product_gtin: batch.product_gtin,
          lot_number: batch.lot_number,
          manufacturing_date: batch.manufacturing_date,
          expiry_date: batch.expiry_date,
          quantity_produced: batch.quantity_produced,
          available_quantity: batch.available_quantity,
          quantity_used: batch.quantity_used,
          manufacturing_location: batch.manufacturing_location,
          status: batch.status,
          quality_control_passed: batch.quality_control_passed,
          is_expired: batch.is_expired,
          days_until_expiry: batch.days_until_expiry,
          shelf_life_remaining_percent: batch.shelf_life_remaining_percent,
          created_at: batch.created_at,
          updated_at: batch.updated_at,
          is_deleted: batch.is_deleted,
        };
        this._batches.update((list) =>
          list.map((b) => (b.id === id ? listItem : b))
        );
        this.cacheService.invalidateEntity('batches');
      })
    );
  }

  /**
   * Delete a batch (soft delete)
   */
  delete(id: number): Observable<{ message: string }> {
    return this.http
      .delete<{ message: string }>(`/api/batches/${id}/delete/`)
      .pipe(
        tap(() => {
          this._batches.update((list) => list.filter((b) => b.id !== id));
          this.cacheService.invalidateEntity('batches');
        })
      );
  }

  /**
   * Force refresh - invalidate cache and reload
   */
  refresh(
    filters?: BatchFilters,
    pagination?: PaginationParams
  ): Observable<PaginatedResponse<BatchListItem>> {
    this.cacheService.invalidateEntity('batches');
    return this.load(filters, pagination);
  }

  /**
   * Get available batch statuses
   */
  getBatchStatuses(): { value: BatchStatus; label: string }[] {
    return [
      { value: 'active', label: 'Active' },
      { value: 'expired', label: 'Expired' },
      { value: 'recalled', label: 'Recalled' },
      { value: 'quarantined', label: 'Quarantined' },
      { value: 'released', label: 'Released' },
      { value: 'destroyed', label: 'Destroyed' },
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
