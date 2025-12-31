import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { TableModule, TableLazyLoadEvent } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { DatePickerModule } from 'primeng/datepicker';
import { ProgressBarModule } from 'primeng/progressbar';

// Services
import { TranslateModule } from '@ngx-translate/core';
import {
  BatchService,
  BatchListItem,
  BatchFilters,
} from '../../core/services/batch.service';
import { ProductService } from '../../core/services/product.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import {
  lazyLoadToParams,
  DEFAULT_PAGE_SIZE,
  PAGE_SIZE_OPTIONS,
} from '../../core/models/pagination.model';

@Component({
  selector: 'app-batches',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    SelectModule,
    TagModule,
    TooltipModule,
    ConfirmDialogModule,
    ToastModule,
    DatePickerModule,
    ProgressBarModule,
    TranslateModule,
  ],
  providers: [ConfirmationService, MessageService],
  templateUrl: './batches.component.html',
})
export class BatchesComponent implements OnInit {
  private batchService = inject(BatchService);
  private productService = inject(ProductService);
  private router = inject(Router);
  private confirmationService = inject(ConfirmationService);
  private messageService = inject(MessageService);

  // Reactive state
  batches = this.batchService.batches;
  loading = this.batchService.loading;
  totalRecords = this.batchService.totalRecords;

  // Filter state
  filters = signal<BatchFilters>({});
  searchTerm = signal('');
  selectedProduct = signal<number | null>(null);
  selectedStatus = signal<string | null>(null);
  selectedExpiryStatus = signal<string | null>(null);
  expiryFromDate = signal<Date | null>(null);
  expiryToDate = signal<Date | null>(null);

  // Pagination state
  first = signal(0);
  rows = signal(DEFAULT_PAGE_SIZE);
  rowsPerPageOptions = PAGE_SIZE_OPTIONS;

  // Options for dropdowns
  products = this.productService.products;
  statusOptions = this.batchService.getBatchStatuses();
  expiryStatusOptions = this.batchService.getExpiryStatusOptions();

  // Expose Math for template
  Math = Math;

  ngOnInit() {
    // Load products for the filter dropdown
    this.productService.load().subscribe();
    // Initial load will be triggered by the table's onLazyLoad event
  }

  /**
   * Handle lazy load event from PrimeNG table for server-side pagination
   */
  onLazyLoad(event: TableLazyLoadEvent) {
    this.first.set(event.first || 0);
    this.rows.set(event.rows || DEFAULT_PAGE_SIZE);

    const paginationParams = lazyLoadToParams({
      first: event.first,
      rows: event.rows,
    });

    this.batchService.load(this.filters(), paginationParams).subscribe({
      error: (error) => {
        console.error('Error loading batches:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load batches',
        });
      },
    });
  }

  loadBatches() {
    const paginationParams = lazyLoadToParams({
      first: this.first(),
      rows: this.rows(),
    });

    this.batchService.load(this.filters(), paginationParams).subscribe({
      error: (error) => {
        console.error('Error loading batches:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load batches',
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
    this.loadBatches();
  }

  onProductFilter() {
    this.filters.update((f) => ({
      ...f,
      product: this.selectedProduct() || undefined,
    }));
    this.first.set(0);
    this.loadBatches();
  }

  onStatusFilter() {
    this.filters.update((f) => ({
      ...f,
      status: (this.selectedStatus() as any) || undefined,
    }));
    this.first.set(0);
    this.loadBatches();
  }

  onExpiryStatusFilter() {
    this.filters.update((f) => ({
      ...f,
      expiry_status: (this.selectedExpiryStatus() as any) || undefined,
    }));
    this.first.set(0);
    this.loadBatches();
  }

  onExpiryDateFilter() {
    const fromDate = this.expiryFromDate();
    const toDate = this.expiryToDate();

    this.filters.update((f) => ({
      ...f,
      expiry_from: fromDate ? this.formatDate(fromDate) : undefined,
      expiry_to: toDate ? this.formatDate(toDate) : undefined,
    }));
    this.first.set(0);
    this.loadBatches();
  }

  clearFilters() {
    this.searchTerm.set('');
    this.selectedProduct.set(null);
    this.selectedStatus.set(null);
    this.selectedExpiryStatus.set(null);
    this.expiryFromDate.set(null);
    this.expiryToDate.set(null);
    this.filters.set({});
    this.first.set(0);
    this.loadBatches();
  }

  viewBatch(batch: BatchListItem) {
    this.router.navigate(['/batches', batch.id]);
  }

  editBatch(batch: BatchListItem) {
    this.router.navigate(['/batches', batch.id, 'edit']);
  }

  deleteBatch(batch: BatchListItem) {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete batch "${batch.lot_number}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.batchService.delete(batch.id).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Batch deleted successfully',
            });
          },
          error: (error) => {
            console.error('Error deleting batch:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to delete batch',
            });
          },
        });
      },
    });
  }

  getStatusSeverity(status: string): 'success' | 'warning' | 'danger' | 'info' {
    switch (status) {
      case 'active':
      case 'released':
        return 'success';
      case 'quarantined':
        return 'warning';
      case 'expired':
      case 'recalled':
      case 'destroyed':
        return 'danger';
      default:
        return 'info';
    }
  }

  getExpiryStatusSeverity(
    batch: BatchListItem
  ): 'success' | 'warning' | 'danger' {
    if (batch.is_expired) {
      return 'danger';
    } else if (batch.days_until_expiry <= 30) {
      return 'warning';
    }
    return 'success';
  }

  createBatch() {
    this.router.navigate(['/batches', 'new']);
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }
}
