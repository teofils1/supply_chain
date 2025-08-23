import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export type ProductStatus = 'active' | 'inactive' | 'discontinued';
export type ProductForm = 'tablet' | 'capsule' | 'liquid' | 'injection' | 'cream' | 'ointment' | 'powder' | 'other';

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
  private _products = signal<ProductListItem[]>([]);
  private _loading = signal(false);
  
  readonly products = computed(() => this._products());
  readonly loading = computed(() => this._loading());

  /**
   * Load products with optional filters
   */
  load(filters?: ProductFilters): Observable<ProductListItem[]> {
    this._loading.set(true);
    
    let params = new HttpParams();
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
      .get<ProductListItem[]>('/api/products/', { params })
      .pipe(
        tap((products) => {
          this._products.set(products);
          this._loading.set(false);
        })
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
    return this.http
      .post<Product>('/api/products/', data)
      .pipe(
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
        })
      );
  }

  /**
   * Update an existing product
   */
  update(id: number, data: Partial<CreateProductData>): Observable<Product> {
    return this.http
      .patch<Product>(`/api/products/${id}/`, data)
      .pipe(
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
          // Remove the product from the list or mark as deleted
          this._products.update((list) =>
            list.map((p) => (p.id === id ? { ...p, is_deleted: true } : p))
          );
        })
      );
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
