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
import { CheckboxModule } from 'primeng/checkbox';

// Services
import { TranslateModule } from '@ngx-translate/core';
import {
  ShipmentService,
  ShipmentListItem,
  ShipmentFilters,
} from '../../core/services/shipment.service';
import { PackService } from '../../core/services/pack.service';
import { BatchService } from '../../core/services/batch.service';
import { ProductService } from '../../core/services/product.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import {
  lazyLoadToParams,
  DEFAULT_PAGE_SIZE,
  PAGE_SIZE_OPTIONS,
} from '../../core/models/pagination.model';

@Component({
  selector: 'app-shipments',
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
    CheckboxModule,
    TranslateModule,
  ],
  providers: [ConfirmationService, MessageService],
  templateUrl: './shipments.component.html',
})
export class ShipmentsComponent implements OnInit {
  private shipmentService = inject(ShipmentService);
  private packService = inject(PackService);
  private batchService = inject(BatchService);
  private productService = inject(ProductService);
  private router = inject(Router);
  private confirmationService = inject(ConfirmationService);
  private messageService = inject(MessageService);

  // Reactive state
  shipments = this.shipmentService.shipments;
  loading = this.shipmentService.loading;
  totalRecords = this.shipmentService.totalRecords;

  // Filter state
  filters = signal<ShipmentFilters>({});
  searchTerm = signal('');
  selectedStatus = signal<string | null>(null);
  selectedCarrier = signal<string | null>(null);
  selectedServiceType = signal<string | null>(null);
  selectedTemperatureRequirement = signal<string | null>(null);
  selectedDeliveryStatus = signal<string | null>(null);
  selectedSpecialHandling = signal<boolean | null>(null);
  selectedPack = signal<number | null>(null);
  selectedBatch = signal<number | null>(null);
  selectedProduct = signal<number | null>(null);
  shippedFromDate = signal<Date | null>(null);
  shippedToDate = signal<Date | null>(null);
  estimatedDeliveryFromDate = signal<Date | null>(null);
  estimatedDeliveryToDate = signal<Date | null>(null);

  // Pagination state
  first = signal(0);
  rows = signal(DEFAULT_PAGE_SIZE);
  rowsPerPageOptions = PAGE_SIZE_OPTIONS;

  // Options for dropdowns
  statusOptions = this.shipmentService.getShipmentStatuses();
  carrierOptions = this.shipmentService.getCarriers();
  serviceTypeOptions = this.shipmentService.getServiceTypes();
  temperatureRequirementOptions =
    this.shipmentService.getTemperatureRequirements();
  deliveryStatusOptions = this.shipmentService.getDeliveryStatusOptions();
  specialHandlingOptions = this.shipmentService.getSpecialHandlingOptions();
  packs = this.packService.packs;
  batches = this.batchService.batches;
  products = this.productService.products;

  ngOnInit() {
    // Load related data for filter dropdowns
    this.packService.load().subscribe();
    this.batchService.load().subscribe();
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

    this.shipmentService.load(this.filters(), paginationParams).subscribe({
      error: (error) => {
        console.error('Error loading shipments:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load shipments',
        });
      },
    });
  }

  loadShipments() {
    const paginationParams = lazyLoadToParams({
      first: this.first(),
      rows: this.rows(),
    });

    this.shipmentService.load(this.filters(), paginationParams).subscribe({
      error: (error) => {
        console.error('Error loading shipments:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load shipments',
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
    this.loadShipments();
  }

  onStatusFilter() {
    this.filters.update((f) => ({
      ...f,
      status: (this.selectedStatus() as any) || undefined,
    }));
    this.first.set(0);
    this.loadShipments();
  }

  onCarrierFilter() {
    this.filters.update((f) => ({
      ...f,
      carrier: (this.selectedCarrier() as any) || undefined,
    }));
    this.first.set(0);
    this.loadShipments();
  }

  onServiceTypeFilter() {
    this.filters.update((f) => ({
      ...f,
      service_type: (this.selectedServiceType() as any) || undefined,
    }));
    this.first.set(0);
    this.loadShipments();
  }

  onTemperatureRequirementFilter() {
    this.filters.update((f) => ({
      ...f,
      temperature_requirement:
        (this.selectedTemperatureRequirement() as any) || undefined,
    }));
    this.first.set(0);
    this.loadShipments();
  }

  onDeliveryStatusFilter() {
    this.filters.update((f) => ({
      ...f,
      delivery_status: (this.selectedDeliveryStatus() as any) || undefined,
    }));
    this.first.set(0);
    this.loadShipments();
  }

  onSpecialHandlingFilter() {
    this.filters.update((f) => ({
      ...f,
      special_handling: this.selectedSpecialHandling() ?? undefined,
    }));
    this.first.set(0);
    this.loadShipments();
  }

  onPackFilter() {
    this.filters.update((f) => ({
      ...f,
      pack: this.selectedPack() || undefined,
    }));
    this.first.set(0);
    this.loadShipments();
  }

  onBatchFilter() {
    this.filters.update((f) => ({
      ...f,
      batch: this.selectedBatch() || undefined,
    }));
    this.first.set(0);
    this.loadShipments();
  }

  onProductFilter() {
    this.filters.update((f) => ({
      ...f,
      product: this.selectedProduct() || undefined,
    }));
    this.first.set(0);
    this.loadShipments();
  }

  onShippedDateFilter() {
    const fromDate = this.shippedFromDate();
    const toDate = this.shippedToDate();

    this.filters.update((f) => ({
      ...f,
      shipped_from: fromDate ? this.formatDate(fromDate) : undefined,
      shipped_to: toDate ? this.formatDate(toDate) : undefined,
    }));
    this.first.set(0);
    this.loadShipments();
  }

  onEstimatedDeliveryDateFilter() {
    const fromDate = this.estimatedDeliveryFromDate();
    const toDate = this.estimatedDeliveryToDate();

    this.filters.update((f) => ({
      ...f,
      estimated_delivery_from: fromDate ? this.formatDate(fromDate) : undefined,
      estimated_delivery_to: toDate ? this.formatDate(toDate) : undefined,
    }));
    this.first.set(0);
    this.loadShipments();
  }

  clearFilters() {
    this.searchTerm.set('');
    this.selectedStatus.set(null);
    this.selectedCarrier.set(null);
    this.selectedServiceType.set(null);
    this.selectedTemperatureRequirement.set(null);
    this.selectedDeliveryStatus.set(null);
    this.selectedSpecialHandling.set(null);
    this.selectedPack.set(null);
    this.selectedBatch.set(null);
    this.selectedProduct.set(null);
    this.shippedFromDate.set(null);
    this.shippedToDate.set(null);
    this.estimatedDeliveryFromDate.set(null);
    this.estimatedDeliveryToDate.set(null);
    this.filters.set({});
    this.first.set(0);
    this.loadShipments();
  }

  viewShipment(shipment: ShipmentListItem) {
    this.router.navigate(['/shipments', shipment.id]);
  }

  editShipment(shipment: ShipmentListItem) {
    this.router.navigate(['/shipments', shipment.id, 'edit']);
  }

  deleteShipment(shipment: ShipmentListItem) {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete shipment "${shipment.tracking_number}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.shipmentService.delete(shipment.id).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Shipment deleted successfully',
            });
          },
          error: (error) => {
            console.error('Error deleting shipment:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to delete shipment',
            });
          },
        });
      },
    });
  }

  getStatusSeverity(status: string): 'success' | 'warning' | 'danger' | 'info' {
    switch (status) {
      case 'delivered':
        return 'success';
      case 'in_transit':
      case 'picked_up':
      case 'out_for_delivery':
        return 'warning';
      case 'cancelled':
      case 'lost':
      case 'damaged':
        return 'danger';
      default:
        return 'info';
    }
  }

  getDeliveryStatusSeverity(
    shipment: ShipmentListItem
  ): 'success' | 'warning' | 'danger' | 'info' {
    if (shipment.is_delivered) {
      return 'success';
    } else if (shipment.is_in_transit) {
      return 'warning';
    } else if (this.isOverdue(shipment)) {
      return 'danger';
    }
    return 'info';
  }

  isOverdue(shipment: ShipmentListItem): boolean {
    if (!shipment.estimated_delivery_date || shipment.is_delivered) {
      return false;
    }
    const estimatedDate = new Date(shipment.estimated_delivery_date);
    const today = new Date();
    return estimatedDate < today;
  }

  createShipment() {
    this.router.navigate(['/shipments', 'new']);
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }
}
