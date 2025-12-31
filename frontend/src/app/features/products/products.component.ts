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

// Services
import { TranslateModule } from '@ngx-translate/core';
import {
  ProductService,
  ProductListItem,
  ProductFilters,
} from '../../core/services/product.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import {
  lazyLoadToParams,
  DEFAULT_PAGE_SIZE,
  PAGE_SIZE_OPTIONS,
} from '../../core/models/pagination.model';

@Component({
  selector: 'app-products',
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
    TranslateModule,
  ],
  providers: [ConfirmationService, MessageService],
  templateUrl: './products.component.html',
})
export class ProductsComponent implements OnInit {
  private productService = inject(ProductService);
  private router = inject(Router);
  private confirmationService = inject(ConfirmationService);
  private messageService = inject(MessageService);

  // Reactive state
  products = this.productService.products;
  loading = this.productService.loading;
  totalRecords = this.productService.totalRecords;

  // Filter state
  filters = signal<ProductFilters>({});
  searchTerm = signal('');
  selectedStatus = signal<string | null>(null);
  selectedForm = signal<string | null>(null);

  // Pagination state
  first = signal(0);
  rows = signal(DEFAULT_PAGE_SIZE);
  rowsPerPageOptions = PAGE_SIZE_OPTIONS;

  // Options for dropdowns
  statusOptions = this.productService.getProductStatuses();
  formOptions = this.productService.getProductForms();

  ngOnInit() {
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

    this.productService.load(this.filters(), paginationParams).subscribe({
      error: (error) => {
        console.error('Error loading products:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load products',
        });
      },
    });
  }

  loadProducts() {
    const paginationParams = lazyLoadToParams({
      first: this.first(),
      rows: this.rows(),
    });

    this.productService.load(this.filters(), paginationParams).subscribe({
      error: (error) => {
        console.error('Error loading products:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load products',
        });
      },
    });
  }

  onSearch() {
    this.filters.update((f) => ({
      ...f,
      search: this.searchTerm() || undefined,
    }));
    this.first.set(0); // Reset to first page on search
    this.loadProducts();
  }

  onStatusFilter() {
    this.filters.update((f) => ({
      ...f,
      status: (this.selectedStatus() as any) || undefined,
    }));
    this.first.set(0); // Reset to first page on filter
    this.loadProducts();
  }

  onFormFilter() {
    this.filters.update((f) => ({
      ...f,
      form: (this.selectedForm() as any) || undefined,
    }));
    this.first.set(0); // Reset to first page on filter
    this.loadProducts();
  }

  clearFilters() {
    this.searchTerm.set('');
    this.selectedStatus.set(null);
    this.selectedForm.set(null);
    this.filters.set({});
    this.first.set(0); // Reset to first page
    this.loadProducts();
  }

  viewProduct(product: ProductListItem) {
    this.router.navigate(['/products', product.id]);
  }

  editProduct(product: ProductListItem) {
    this.router.navigate(['/products', product.id, 'edit']);
  }

  deleteProduct(product: ProductListItem) {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete "${product.name}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.productService.delete(product.id).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Product deleted successfully',
            });
          },
          error: (error) => {
            console.error('Error deleting product:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to delete product',
            });
          },
        });
      },
    });
  }

  getStatusSeverity(status: string): 'success' | 'warning' | 'danger' | 'info' {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'warning';
      case 'discontinued':
        return 'danger';
      default:
        return 'info';
    }
  }

  createProduct() {
    this.router.navigate(['/products', 'new']);
  }
}
