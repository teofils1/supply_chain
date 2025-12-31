import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, map } from 'rxjs';
import {
  Document,
  DocumentListItem,
  DocumentDetail,
  DocumentFilters,
  DocumentCategory,
  EntityType,
  DownloadInfo,
  GeneratedPdfResponse,
} from '../models/document.model';
import {
  PaginatedResponse,
  PaginationParams,
  DEFAULT_PAGE_SIZE,
} from '../models/pagination.model';

@Injectable({ providedIn: 'root' })
export class DocumentService {
  private http = inject(HttpClient);
  private _documents = signal<DocumentListItem[]>([]);
  private _loading = signal(false);
  private _totalRecords = signal(0);
  private _currentPage = signal(1);
  private _pageSize = signal(DEFAULT_PAGE_SIZE);

  readonly documents = computed(() => this._documents());
  readonly loading = computed(() => this._loading());
  readonly totalRecords = computed(() => this._totalRecords());
  readonly currentPage = computed(() => this._currentPage());
  readonly pageSize = computed(() => this._pageSize());

  /**
   * Load documents with optional filters and pagination
   */
  load(
    filters?: DocumentFilters,
    pagination?: PaginationParams
  ): Observable<PaginatedResponse<DocumentListItem>> {
    this._loading.set(true);
    let params = new HttpParams();

    if (filters?.entity_type) {
      params = params.set('entity_type', filters.entity_type);
    }
    if (filters?.entity_id) {
      params = params.set('entity_id', filters.entity_id.toString());
    }
    if (filters?.category) {
      params = params.set('category', filters.category);
    }
    if (filters?.search) {
      params = params.set('search', filters.search);
    }
    if (filters?.latest_only !== undefined) {
      params = params.set('latest_only', filters.latest_only.toString());
    }

    // Pagination
    const page = pagination?.page ?? this._currentPage();
    const size = pagination?.page_size ?? this._pageSize();
    params = params.set('page', page.toString());
    params = params.set('page_size', size.toString());

    return this.http
      .get<PaginatedResponse<DocumentListItem>>('/api/documents/', { params })
      .pipe(
        tap((response) => {
          this._documents.set(response.results);
          this._totalRecords.set(response.count);
          this._currentPage.set(page);
          this._pageSize.set(size);
          this._loading.set(false);
        })
      );
  }

  /**
   * Get documents for a specific entity
   */
  getEntityDocuments(
    entityType: EntityType,
    entityId: number,
    category?: DocumentCategory
  ): Observable<DocumentListItem[]> {
    let params = new HttpParams();
    if (category) {
      params = params.set('category', category);
    }
    return this.http.get<DocumentListItem[]>(
      `/api/${entityType}s/${entityId}/documents/`,
      { params }
    );
  }

  /**
   * Get a single document by ID
   */
  get(id: number): Observable<DocumentDetail> {
    return this.http.get<DocumentDetail>(`/api/documents/${id}/`);
  }

  /**
   * Upload a new document
   */
  upload(
    file: File,
    title: string,
    entityType: EntityType,
    entityId: number,
    category: DocumentCategory = 'other',
    description: string = ''
  ): Observable<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('entity_type', entityType);
    formData.append('entity_id', entityId.toString());
    formData.append('category', category);
    if (description) {
      formData.append('description', description);
    }

    return this.http.post<Document>('/api/documents/', formData);
  }

  /**
   * Upload a new version of an existing document
   */
  uploadNewVersion(
    documentId: number,
    file: File,
    title?: string,
    description?: string
  ): Observable<DocumentDetail> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) {
      formData.append('title', title);
    }
    if (description) {
      formData.append('description', description);
    }

    return this.http.post<DocumentDetail>(
      `/api/documents/${documentId}/new-version/`,
      formData
    );
  }

  /**
   * Get download information for a document
   */
  getDownloadInfo(id: number): Observable<DownloadInfo> {
    return this.http.get<DownloadInfo>(`/api/documents/${id}/download/`);
  }

  /**
   * Delete a document (soft delete)
   */
  delete(id: number): Observable<void> {
    return this.http.delete<void>(`/api/documents/${id}/delete/`);
  }

  /**
   * Generate shipping label PDF for a shipment
   */
  generateShippingLabel(
    shipmentId: number,
    save: boolean = true
  ): Observable<GeneratedPdfResponse | Blob> {
    const params = new HttpParams().set('save', save.toString());
    if (save) {
      return this.http.post<GeneratedPdfResponse>(
        `/api/shipments/${shipmentId}/generate-label/`,
        {},
        { params }
      );
    } else {
      return this.http.post(
        `/api/shipments/${shipmentId}/generate-label/`,
        {},
        { params, responseType: 'blob' }
      );
    }
  }

  /**
   * Generate packing list PDF for a shipment
   */
  generatePackingList(
    shipmentId: number,
    save: boolean = true
  ): Observable<GeneratedPdfResponse | Blob> {
    const params = new HttpParams().set('save', save.toString());
    if (save) {
      return this.http.post<GeneratedPdfResponse>(
        `/api/shipments/${shipmentId}/generate-packing-list/`,
        {},
        { params }
      );
    } else {
      return this.http.post(
        `/api/shipments/${shipmentId}/generate-packing-list/`,
        {},
        { params, responseType: 'blob' }
      );
    }
  }

  /**
   * Generate Certificate of Analysis PDF for a batch
   */
  generateCoa(
    batchId: number,
    save: boolean = true
  ): Observable<GeneratedPdfResponse | Blob> {
    const params = new HttpParams().set('save', save.toString());
    if (save) {
      return this.http.post<GeneratedPdfResponse>(
        `/api/batches/${batchId}/generate-coa/`,
        {},
        { params }
      );
    } else {
      return this.http.post(
        `/api/batches/${batchId}/generate-coa/`,
        {},
        { params, responseType: 'blob' }
      );
    }
  }

  /**
   * Get available document categories
   */
  getCategories(): { label: string; value: DocumentCategory }[] {
    return [
      { label: 'Certificate', value: 'certificate' },
      { label: 'Invoice', value: 'invoice' },
      { label: 'Packing List', value: 'packing_list' },
      { label: 'Shipping Label', value: 'shipping_label' },
      { label: 'Certificate of Analysis', value: 'coa' },
      { label: 'Material Safety Data Sheet', value: 'msds' },
      { label: 'Quality Report', value: 'quality_report' },
      { label: 'Photo', value: 'photo' },
      { label: 'Other', value: 'other' },
    ];
  }

  /**
   * Get entity types for document association
   */
  getEntityTypes(): { label: string; value: EntityType }[] {
    return [
      { label: 'Product', value: 'product' },
      { label: 'Batch', value: 'batch' },
      { label: 'Pack', value: 'pack' },
      { label: 'Shipment', value: 'shipment' },
    ];
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get icon for file type
   */
  getFileIcon(fileType: string): string {
    if (fileType.includes('pdf')) return 'pi pi-file-pdf';
    if (fileType.includes('image')) return 'pi pi-image';
    if (fileType.includes('word') || fileType.includes('document'))
      return 'pi pi-file-word';
    if (fileType.includes('excel') || fileType.includes('spreadsheet'))
      return 'pi pi-file-excel';
    if (fileType.includes('text')) return 'pi pi-file';
    return 'pi pi-file';
  }
}
