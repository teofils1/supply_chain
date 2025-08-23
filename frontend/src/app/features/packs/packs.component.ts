import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { DatePickerModule } from 'primeng/datepicker';
import { ProgressBarModule } from 'primeng/progressbar';
import { CheckboxModule } from 'primeng/checkbox';

// Services
import { TranslateModule } from '@ngx-translate/core';
import {
  PackService,
  PackListItem,
  PackFilters,
} from '../../core/services/pack.service';
import { BatchService } from '../../core/services/batch.service';
import { ProductService } from '../../core/services/product.service';
import { ConfirmationService, MessageService } from 'primeng/api';

@Component({
  selector: 'app-packs',
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
    CheckboxModule,
    TranslateModule,
  ],
  providers: [ConfirmationService, MessageService],
  templateUrl: './packs.component.html',
})
export class PacksComponent implements OnInit {
  private packService = inject(PackService);
  private batchService = inject(BatchService);
  private productService = inject(ProductService);
  private router = inject(Router);
  private confirmationService = inject(ConfirmationService);
  private messageService = inject(MessageService);

  // Reactive state
  packs = this.packService.packs;
  loading = this.packService.loading;

  // Filter state
  filters = signal<PackFilters>({});
  searchTerm = signal('');
  selectedBatch = signal<number | null>(null);
  selectedProduct = signal<number | null>(null);
  selectedStatus = signal<string | null>(null);
  selectedPackType = signal<string | null>(null);
  selectedLocation = signal<string | null>(null);
  selectedShippingStatus = signal<string | null>(null);
  selectedExpiryStatus = signal<string | null>(null);
  selectedQcPassed = signal<boolean | null>(null);
  expiryFromDate = signal<Date | null>(null);
  expiryToDate = signal<Date | null>(null);

  // Options for dropdowns
  batches = this.batchService.batches;
  products = this.productService.products;
  statusOptions = this.packService.getPackStatuses();
  packTypeOptions = this.packService.getPackTypes();
  shippingStatusOptions = this.packService.getShippingStatusOptions();
  expiryStatusOptions = this.packService.getExpiryStatusOptions();
  qcOptions = [
    { value: true, label: 'Passed' },
    { value: false, label: 'Failed' },
  ];

  // Expose Math for template
  Math = Math;

  ngOnInit() {
    // Load related data for filter dropdowns
    this.batchService.load().subscribe();
    this.productService.load().subscribe();
    this.loadPacks();
  }

  loadPacks() {
    const currentFilters = this.filters();
    this.packService.load(currentFilters).subscribe({
      error: (error) => {
        console.error('Error loading packs:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load packs',
        });
      },
    });
  }

  onSearch() {
    this.filters.update((f) => ({
      ...f,
      search: this.searchTerm() || undefined,
    }));
    this.loadPacks();
  }

  onBatchFilter() {
    this.filters.update((f) => ({
      ...f,
      batch: this.selectedBatch() || undefined,
    }));
    this.loadPacks();
  }

  onProductFilter() {
    this.filters.update((f) => ({
      ...f,
      product: this.selectedProduct() || undefined,
    }));
    this.loadPacks();
  }

  onStatusFilter() {
    this.filters.update((f) => ({
      ...f,
      status: (this.selectedStatus() as any) || undefined,
    }));
    this.loadPacks();
  }

  onPackTypeFilter() {
    this.filters.update((f) => ({
      ...f,
      pack_type: (this.selectedPackType() as any) || undefined,
    }));
    this.loadPacks();
  }

  onLocationFilter() {
    this.filters.update((f) => ({
      ...f,
      location: this.selectedLocation() || undefined,
    }));
    this.loadPacks();
  }

  onShippingStatusFilter() {
    this.filters.update((f) => ({
      ...f,
      shipping_status: (this.selectedShippingStatus() as any) || undefined,
    }));
    this.loadPacks();
  }

  onExpiryStatusFilter() {
    this.filters.update((f) => ({
      ...f,
      expiry_status: (this.selectedExpiryStatus() as any) || undefined,
    }));
    this.loadPacks();
  }

  onQcFilter() {
    this.filters.update((f) => ({
      ...f,
      qc_passed: this.selectedQcPassed() ?? undefined,
    }));
    this.loadPacks();
  }

  onExpiryDateFilter() {
    const fromDate = this.expiryFromDate();
    const toDate = this.expiryToDate();

    this.filters.update((f) => ({
      ...f,
      expiry_from: fromDate ? this.formatDate(fromDate) : undefined,
      expiry_to: toDate ? this.formatDate(toDate) : undefined,
    }));
    this.loadPacks();
  }

  clearFilters() {
    this.searchTerm.set('');
    this.selectedBatch.set(null);
    this.selectedProduct.set(null);
    this.selectedStatus.set(null);
    this.selectedPackType.set(null);
    this.selectedLocation.set(null);
    this.selectedShippingStatus.set(null);
    this.selectedExpiryStatus.set(null);
    this.selectedQcPassed.set(null);
    this.expiryFromDate.set(null);
    this.expiryToDate.set(null);
    this.filters.set({});
    this.loadPacks();
  }

  viewPack(pack: PackListItem) {
    this.router.navigate(['/packs', pack.id]);
  }

  editPack(pack: PackListItem) {
    this.router.navigate(['/packs', pack.id, 'edit']);
  }

  deletePack(pack: PackListItem) {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete pack "${pack.serial_number}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.packService.delete(pack.id).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Pack deleted successfully',
            });
          },
          error: (error) => {
            console.error('Error deleting pack:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to delete pack',
            });
          },
        });
      },
    });
  }

  getStatusSeverity(status: string): 'success' | 'warning' | 'danger' | 'info' {
    switch (status) {
      case 'active':
      case 'delivered':
        return 'success';
      case 'shipped':
      case 'quarantined':
        return 'warning';
      case 'damaged':
      case 'recalled':
      case 'destroyed':
        return 'danger';
      default:
        return 'info';
    }
  }

  getExpiryStatusSeverity(
    pack: PackListItem
  ): 'success' | 'warning' | 'danger' {
    if (pack.is_expired) {
      return 'danger';
    } else if (pack.days_until_expiry <= 30) {
      return 'warning';
    }
    return 'success';
  }

  createPack() {
    this.router.navigate(['/packs', 'new']);
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }
}
