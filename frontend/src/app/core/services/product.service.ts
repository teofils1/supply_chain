import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, map } from 'rxjs';
import {
  PaginatedResponse,
  PaginationParams,
  DEFAULT_PAGE_SIZE,
} from '../models/pagination.model';
import { CacheService } from './cache.service';

export type ProductStatus = 'active' | 'inactive' | 'discontinued';
export type ProductForm =
  | 'tablet'
  | 'capsule'
  | 'liquid'
  | 'injection'
  | 'cream'
  | 'ointment'
  | 'powder'
  | 'other';

export interface Product {
  id: number;
  gtin: string;
  name: string;
  description?: string;
  form: ProductForm;
  strength?: string;
  storage_temp_min?: number;
  storage_temp_max?: number;
  storage_humidity_min?: number;
  storage_humidity_max?: number;
  storage_range_display: string;
  manufacturer?: string;
  ndc?: string;
  status: ProductStatus;
  approval_number?: string;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
}

export interface ProductListItem {
  id: number;
  gtin: string;
  name: string;
  form: ProductForm;
  strength?: string;
  manufacturer?: string;
  status: ProductStatus;
  storage_range_display: string;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
}

export interface ProductFilters {
  search?: string;
  status?: ProductStatus;
  form?: ProductForm;
  manufacturer?: string;
}

export interface CreateProductData {
  gtin: string;
  name: string;
  description?: string;
  form: ProductForm;
  strength?: string;
  storage_temp_min?: number;
  storage_temp_max?: number;
  storage_humidity_min?: number;
  storage_humidity_max?: number;
  manufacturer?: string;
  ndc?: string;
  status?: ProductStatus;
  approval_number?: string;
}

@Injectable({ providedIn: 'root' })
export class ProductService {
  private http = inject(HttpClient);
  private cacheService = inject(CacheService);
  private _products = signal<ProductListItem[]>([]);
  private _loading = signal(false);
  private _totalRecords = signal(0);
  private _currentPage = signal(1);
  private _pageSize = signal(DEFAULT_PAGE_SIZE);

  readonly products = computed(() => this._products());
  readonly loading = computed(() => this._loading());
  readonly totalRecords = computed(() => this._totalRecords());
  readonly currentPage = computed(() => this._currentPage());
  readonly pageSize = computed(() => this._pageSize());

  /**
   * Load products with optional filters and pagination
   */
  load(
    filters?: ProductFilters,
    pagination?: PaginationParams
  ): Observable<PaginatedResponse<ProductListItem>> {
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
    if (filters?.form) {
      params = params.set('form', filters.form);
    }
    if (filters?.manufacturer) {
      params = params.set('manufacturer', filters.manufacturer);
    }

    return this.http
      .get<PaginatedResponse<ProductListItem>>('/api/products/', { params })
      .pipe(
        tap((response) => {
          this._products.set(response.results);
          this._totalRecords.set(response.count);
          this._currentPage.set(response.current_page);
          this._pageSize.set(response.page_size);
          this._loading.set(false);
        })
      );
  }

  /**
   * Load all products (legacy method for backward compatibility)
   * Returns just the results array
   */
  loadAll(filters?: ProductFilters): Observable<ProductListItem[]> {
    return this.load(filters, { page: 1, page_size: 100 }).pipe(
      map((response) => response.results)
    );
  }

  /**
   * Get a single product by ID
   */
  getById(id: number): Observable<Product> {
    return this.http.get<Product>(`/api/products/${id}/`);
  }

  /**
   * Create a new product
   */
  create(data: CreateProductData): Observable<Product> {
    return this.http.post<Product>('/api/products/', data).pipe(
      tap((product) => {
        // Add the new product to the list (convert to list item format)
        const listItem: ProductListItem = {
          id: product.id,
          gtin: product.gtin,
          name: product.name,
          form: product.form,
          strength: product.strength,
          manufacturer: product.manufacturer,
          status: product.status,
          storage_range_display: product.storage_range_display,
          created_at: product.created_at,
          updated_at: product.updated_at,
          is_deleted: product.is_deleted,
        };
        this._products.update((list) => [...list, listItem]);
        // Invalidate cache to ensure fresh data on next load
        this.cacheService.invalidateEntity('products');
      })
    );
  }

  /**
   * Update an existing product
   */
  update(id: number, data: Partial<CreateProductData>): Observable<Product> {
    return this.http.patch<Product>(`/api/products/${id}/`, data).pipe(
      tap((product) => {
        // Update the product in the list
        const listItem: ProductListItem = {
          id: product.id,
          gtin: product.gtin,
          name: product.name,
          form: product.form,
          strength: product.strength,
          manufacturer: product.manufacturer,
          status: product.status,
          storage_range_display: product.storage_range_display,
          created_at: product.created_at,
          updated_at: product.updated_at,
          is_deleted: product.is_deleted,
        };
        this._products.update((list) =>
          list.map((p) => (p.id === id ? listItem : p))
        );
        // Invalidate cache
        this.cacheService.invalidateEntity('products');
      })
    );
  }

  /**
   * Delete a product (soft delete)
   */
  delete(id: number): Observable<{ message: string }> {
    return this.http
      .delete<{ message: string }>(`/api/products/${id}/delete/`)
      .pipe(
        tap(() => {
          // Remove the product from the list completely
          this._products.update((list) => list.filter((p) => p.id !== id));
          // Invalidate cache
          this.cacheService.invalidateEntity('products');
        })
      );
  }

  /**
   * Force refresh - invalidate cache and reload
   */
  refresh(
    filters?: ProductFilters,
    pagination?: PaginationParams
  ): Observable<PaginatedResponse<ProductListItem>> {
    this.cacheService.invalidateEntity('products');
    return this.load(filters, pagination);
  }

  /**
   * Get available product forms
   */
  getProductForms(): { value: ProductForm; label: string }[] {
    return [
      { value: 'tablet', label: 'Tablet' },
      { value: 'capsule', label: 'Capsule' },
      { value: 'liquid', label: 'Liquid' },
      { value: 'injection', label: 'Injection' },
      { value: 'cream', label: 'Cream' },
      { value: 'ointment', label: 'Ointment' },
      { value: 'powder', label: 'Powder' },
      { value: 'other', label: 'Other' },
    ];
  }

  /**
   * Get available product statuses
   */
  getProductStatuses(): { value: ProductStatus; label: string }[] {
    return [
      { value: 'active', label: 'Active' },
      { value: 'inactive', label: 'Inactive' },
      { value: 'discontinued', label: 'Discontinued' },
    ];
  }
}
