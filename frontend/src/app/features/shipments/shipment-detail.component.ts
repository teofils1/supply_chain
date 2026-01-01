import {
  Component,
  inject,
  signal,
  OnInit,
  computed,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { SelectModule } from 'primeng/select';
import { CheckboxModule } from 'primeng/checkbox';
import { TextareaModule } from 'primeng/textarea';
import { ToastModule } from 'primeng/toast';
import { DatePickerModule } from 'primeng/datepicker';
import { TagModule } from 'primeng/tag';
import { MultiSelectModule } from 'primeng/multiselect';
import { StepperModule } from 'primeng/stepper';

// Services
import { TranslateModule } from '@ngx-translate/core';
import {
  ShipmentService,
  Shipment,
  CreateShipmentData,
} from '../../core/services/shipment.service';
import { PackService, PackListItem } from '../../core/services/pack.service';
import { DocumentService } from '../../core/services/document.service';
import { MessageService } from 'primeng/api';
import { EntityDocumentsComponent } from '../documents/entity-documents.component';

// Interface for displayed pack information
interface DisplayedPack {
  id: number;
  serial_number: string;
  product_name: string;
  batch_lot_number: string;
  pack_size: number;
  pack_type: string;
  quantity_shipped?: number;
}

@Component({
  selector: 'app-shipment-detail',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    CardModule,
    ButtonModule,
    InputTextModule,
    InputNumberModule,
    SelectModule,
    CheckboxModule,
    TextareaModule,
    ToastModule,
    DatePickerModule,
    TagModule,
    MultiSelectModule,
    StepperModule,
    TranslateModule,
    EntityDocumentsComponent,
  ],
  providers: [MessageService],
  templateUrl: './shipment-detail.component.html',
})
export class ShipmentDetailComponent implements OnInit {
  private shipmentService = inject(ShipmentService);
  private packService = inject(PackService);
  private documentService = inject(DocumentService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(FormBuilder);
  private messageService = inject(MessageService);

  @ViewChild(EntityDocumentsComponent)
  documentsComponent?: EntityDocumentsComponent;

  // State
  shipment = signal<Shipment | null>(null);
  loading = signal(false);
  saving = signal(false);
  generatingPdf = signal(false);

  // Form
  shipmentForm: FormGroup;

  // Mode detection
  shipmentId = signal<number | null>(null);
  isEditMode = computed(() =>
    this.route.snapshot.url.some((segment) => segment.path === 'edit')
  );
  isCreateMode = computed(() =>
    this.route.snapshot.url.some((segment) => segment.path === 'new')
  );
  isViewMode = computed(() => !this.isEditMode() && !this.isCreateMode());

  // Options
  availablePacks = this.packService.packs;
  statusOptions = this.shipmentService.getShipmentStatuses();
  carrierOptions = this.shipmentService.getCarriers();
  serviceTypeOptions = this.shipmentService.getServiceTypes();
  temperatureRequirementOptions =
    this.shipmentService.getTemperatureRequirements();

  // Expose Math for template
  Math = Math;

  constructor() {
    this.shipmentForm = this.fb.group({
      tracking_number: ['', [Validators.required, Validators.maxLength(100)]],
      status: ['pending', [Validators.required]],
      carrier: ['', [Validators.required]],
      service_type: ['standard', [Validators.required]],
      pack_ids: [[], [Validators.required, Validators.minLength(1)]],

      // Origin address
      origin_name: ['', [Validators.required, Validators.maxLength(255)]],
      origin_address_line1: [
        '',
        [Validators.required, Validators.maxLength(255)],
      ],
      origin_address_line2: [''],
      origin_city: ['', [Validators.required, Validators.maxLength(100)]],
      origin_state: ['', [Validators.required, Validators.maxLength(100)]],
      origin_postal_code: ['', [Validators.required, Validators.maxLength(20)]],
      origin_country: ['USA', [Validators.required, Validators.maxLength(100)]],

      // Destination address
      destination_name: ['', [Validators.required, Validators.maxLength(255)]],
      destination_address_line1: [
        '',
        [Validators.required, Validators.maxLength(255)],
      ],
      destination_address_line2: [''],
      destination_city: ['', [Validators.required, Validators.maxLength(100)]],
      destination_state: ['', [Validators.required, Validators.maxLength(100)]],
      destination_postal_code: [
        '',
        [Validators.required, Validators.maxLength(20)],
      ],
      destination_country: [
        'USA',
        [Validators.required, Validators.maxLength(100)],
      ],

      // Dates
      shipped_date: [null],
      estimated_delivery_date: [null],
      actual_delivery_date: [null],

      // Requirements
      temperature_requirement: ['ambient'],
      special_handling_required: [false],
      special_instructions: [''],

      // Cost and billing
      shipping_cost: [null, [Validators.min(0)]],
      currency: ['USD'],
      billing_reference: [''],

      // Additional information
      notes: [''],
      external_tracking_url: [''],
    });
  }

  ngOnInit() {
    // Get shipment ID from route first
    const id = this.route.snapshot.paramMap.get('id');
    if (id && id !== 'new') {
      this.shipmentId.set(parseInt(id, 10));
      this.loadShipment();
    }

    // Load available packs for selection
    // For view/edit mode, load all packs to show existing shipment packs
    // For create mode, only load active packs
    this.packService
      .load(
        this.isCreateMode()
          ? { status: 'active' } // Only load active packs that can be shipped
          : {} // Load all packs to show existing shipment packs
      )
      .subscribe();

    // Disable form in view mode
    if (this.isViewMode()) {
      this.shipmentForm.disable();
    }
  }

  loadShipment() {
    const id = this.shipmentId();
    if (!id) return;

    this.loading.set(true);
    this.shipmentService.getById(id).subscribe({
      next: (shipment) => {
        this.shipment.set(shipment);
        this.populateForm(shipment);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Error loading shipment:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load shipment details',
        });
        this.loading.set(false);
      },
    });
  }

  populateForm(shipment: Shipment) {
    // Convert date strings to Date objects for the form
    const shippedDate = shipment.shipped_date
      ? new Date(shipment.shipped_date)
      : null;
    const estimatedDeliveryDate = shipment.estimated_delivery_date
      ? new Date(shipment.estimated_delivery_date)
      : null;
    const actualDeliveryDate = shipment.actual_delivery_date
      ? new Date(shipment.actual_delivery_date)
      : null;

    // Get pack IDs from shipment packs
    const packIds = shipment.shipment_packs.map((sp) => sp.pack);

    this.shipmentForm.patchValue({
      tracking_number: shipment.tracking_number,
      status: shipment.status,
      carrier: shipment.carrier,
      service_type: shipment.service_type,
      pack_ids: packIds,

      // Origin address
      origin_name: shipment.origin_name,
      origin_address_line1: shipment.origin_address_line1,
      origin_address_line2: shipment.origin_address_line2 || '',
      origin_city: shipment.origin_city,
      origin_state: shipment.origin_state,
      origin_postal_code: shipment.origin_postal_code,
      origin_country: shipment.origin_country,

      // Destination address
      destination_name: shipment.destination_name,
      destination_address_line1: shipment.destination_address_line1,
      destination_address_line2: shipment.destination_address_line2 || '',
      destination_city: shipment.destination_city,
      destination_state: shipment.destination_state,
      destination_postal_code: shipment.destination_postal_code,
      destination_country: shipment.destination_country,

      // Dates
      shipped_date: shippedDate,
      estimated_delivery_date: estimatedDeliveryDate,
      actual_delivery_date: actualDeliveryDate,

      // Requirements
      temperature_requirement: shipment.temperature_requirement,
      special_handling_required: shipment.special_handling_required,
      special_instructions: shipment.special_instructions || '',

      // Cost and billing
      shipping_cost: shipment.shipping_cost,
      currency: shipment.currency,
      billing_reference: shipment.billing_reference || '',

      // Additional information
      notes: shipment.notes || '',
      external_tracking_url: shipment.external_tracking_url || '',
    });
  }

  onSubmit() {
    if (this.shipmentForm.invalid) {
      this.markFormGroupTouched();
      return;
    }

    this.saving.set(true);
    const formData = this.getFormData();

    if (this.isCreateMode()) {
      this.shipmentService.create(formData).subscribe({
        next: (shipment) => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Shipment created successfully',
          });
          this.router.navigate(['/shipments', shipment.id]);
        },
        error: (error) => {
          console.error('Error creating shipment:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to create shipment',
          });
          this.saving.set(false);
        },
      });
    } else if (this.isEditMode()) {
      const id = this.shipmentId();
      if (id) {
        this.shipmentService.update(id, formData).subscribe({
          next: (shipment) => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Shipment updated successfully',
            });
            this.router.navigate(['/shipments', shipment.id]);
          },
          error: (error) => {
            console.error('Error updating shipment:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to update shipment',
            });
            this.saving.set(false);
          },
        });
      }
    }
  }

  private getFormData(): CreateShipmentData {
    const formValue = this.shipmentForm.value;

    return {
      tracking_number: formValue.tracking_number,
      status: formValue.status,
      carrier: formValue.carrier,
      service_type: formValue.service_type,
      pack_ids: formValue.pack_ids,

      // Origin address
      origin_name: formValue.origin_name,
      origin_address_line1: formValue.origin_address_line1,
      origin_address_line2: formValue.origin_address_line2 || undefined,
      origin_city: formValue.origin_city,
      origin_state: formValue.origin_state,
      origin_postal_code: formValue.origin_postal_code,
      origin_country: formValue.origin_country,

      // Destination address
      destination_name: formValue.destination_name,
      destination_address_line1: formValue.destination_address_line1,
      destination_address_line2:
        formValue.destination_address_line2 || undefined,
      destination_city: formValue.destination_city,
      destination_state: formValue.destination_state,
      destination_postal_code: formValue.destination_postal_code,
      destination_country: formValue.destination_country,

      // Dates
      shipped_date: formValue.shipped_date
        ? formValue.shipped_date.toISOString()
        : undefined,
      estimated_delivery_date: formValue.estimated_delivery_date
        ? formValue.estimated_delivery_date.toISOString()
        : undefined,
      actual_delivery_date: formValue.actual_delivery_date
        ? formValue.actual_delivery_date.toISOString()
        : undefined,

      // Requirements
      temperature_requirement: formValue.temperature_requirement,
      special_handling_required: formValue.special_handling_required,
      special_instructions: formValue.special_instructions || undefined,

      // Cost and billing
      shipping_cost: formValue.shipping_cost || undefined,
      currency: formValue.currency,
      billing_reference: formValue.billing_reference || undefined,

      // Additional information
      notes: formValue.notes || undefined,
      external_tracking_url: formValue.external_tracking_url || undefined,
    };
  }

  private markFormGroupTouched() {
    Object.keys(this.shipmentForm.controls).forEach((key) => {
      const control = this.shipmentForm.get(key);
      control?.markAsTouched();
    });
  }

  enableEdit() {
    this.router.navigate(['/shipments', this.shipmentId(), 'edit']);
  }

  cancel() {
    if (this.isCreateMode()) {
      this.router.navigate(['/shipments']);
    } else {
      this.router.navigate(['/shipments', this.shipmentId()]);
    }
  }

  goBack() {
    this.router.navigate(['/shipments']);
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

  getSelectedPacks(): DisplayedPack[] {
    const packIds = this.shipmentForm.get('pack_ids')?.value || [];
    return this.availablePacks()
      .filter((pack) => packIds.includes(pack.id))
      .map((pack) => ({
        id: pack.id,
        serial_number: pack.serial_number,
        product_name: pack.product_name,
        batch_lot_number: pack.batch_lot_number,
        pack_size: pack.pack_size,
        pack_type: pack.pack_type,
      }));
  }

  // Method to get shipment packs directly from shipment data (for view mode)
  getShipmentPacks(): DisplayedPack[] {
    const shipment = this.shipment();
    if (!shipment) return [];

    return shipment.shipment_packs.map((sp) => ({
      id: sp.pack,
      serial_number: sp.pack_serial_number,
      product_name: sp.product_name,
      batch_lot_number: sp.batch_lot_number,
      pack_size: sp.pack_size,
      pack_type: sp.pack_type,
      quantity_shipped: sp.quantity_shipped,
    }));
  }

  // Helper method to get displayed packs (works for both create/edit and view modes)
  getDisplayedPacks(): DisplayedPack[] {
    if (this.isViewMode() && this.shipment()) {
      return this.getShipmentPacks();
    }
    return this.getSelectedPacks();
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.shipmentForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  getFieldError(fieldName: string): string {
    const field = this.shipmentForm.get(fieldName);
    if (field?.errors) {
      if (field.errors['required']) return `${fieldName} is required`;
      if (field.errors['maxlength']) return `${fieldName} is too long`;
      if (field.errors['min'])
        return `${fieldName} must be greater than ${field.errors['min'].min}`;
      if (field.errors['minlength'])
        return `At least one pack must be selected`;
    }
    return '';
  }

  // Helper method to get pack display text
  getPackDisplayText(pack: any): string {
    return `${pack.serial_number} - ${pack.product_name} (${pack.batch_lot_number})`;
  }

  // Helper method to check if shipment is overdue
  isOverdue(): boolean {
    const shipment = this.shipment();
    if (
      !shipment ||
      !shipment.estimated_delivery_date ||
      shipment.is_delivered
    ) {
      return false;
    }
    const estimatedDate = new Date(shipment.estimated_delivery_date);
    const today = new Date();
    return estimatedDate < today;
  }

  /**
   * Generate, save, and download shipping label
   */
  generateShippingLabel() {
    const shipmentId = this.shipmentId();
    if (!shipmentId) return;

    this.generatingPdf.set(true);
    // First save the document
    this.documentService.generateShippingLabel(shipmentId, true).subscribe({
      next: (savedDoc: any) => {
        // Use the document download endpoint for proper download
        if (savedDoc.id) {
          this.documentService.getDownloadInfo(savedDoc.id).subscribe({
            next: (downloadInfo) => {
              // Fetch and download using the download URL
              fetch(downloadInfo.download_url)
                .then((response) => {
                  if (!response.ok) throw new Error('Failed to fetch PDF');
                  return response.blob();
                })
                .then((blob) => {
                  const url = window.URL.createObjectURL(blob);
                  const link = window.document.createElement('a');
                  link.href = url;
                  link.download = downloadInfo.file_name;
                  window.document.body.appendChild(link);
                  link.click();
                  window.document.body.removeChild(link);
                  window.URL.revokeObjectURL(url);
                })
                .catch((error) => {
                  console.error('Error downloading PDF:', error);
                  // Fallback: open download URL directly
                  window.open(downloadInfo.download_url, '_blank');
                });
            },
            error: (error) => {
              console.error('Error getting download info:', error);
            },
          });
        }

        this.generatingPdf.set(false);
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Shipping label saved and downloaded',
        });
        // Refresh the documents table
        if (this.documentsComponent) {
          this.documentsComponent.loadDocuments();
        }
      },
      error: (error) => {
        console.error('Error generating shipping label:', error);
        this.generatingPdf.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to generate shipping label',
        });
      },
    });
  }

  /**
   * Generate, save, and download packing list
   */
  generatePackingList() {
    const shipmentId = this.shipmentId();
    if (!shipmentId) return;

    this.generatingPdf.set(true);
    // First save the document
    this.documentService.generatePackingList(shipmentId, true).subscribe({
      next: (savedDoc: any) => {
        // Use the document download endpoint for proper download
        if (savedDoc.id) {
          this.documentService.getDownloadInfo(savedDoc.id).subscribe({
            next: (downloadInfo) => {
              // Fetch and download using the download URL
              fetch(downloadInfo.download_url)
                .then((response) => {
                  if (!response.ok) throw new Error('Failed to fetch PDF');
                  return response.blob();
                })
                .then((blob) => {
                  const url = window.URL.createObjectURL(blob);
                  const link = window.document.createElement('a');
                  link.href = url;
                  link.download = downloadInfo.file_name;
                  window.document.body.appendChild(link);
                  link.click();
                  window.document.body.removeChild(link);
                  window.URL.revokeObjectURL(url);
                })
                .catch((error) => {
                  console.error('Error downloading PDF:', error);
                  // Fallback: open download URL directly
                  window.open(downloadInfo.download_url, '_blank');
                });
            },
            error: (error) => {
              console.error('Error getting download info:', error);
            },
          });
        }

        this.generatingPdf.set(false);
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Packing list saved and downloaded',
        });
        // Refresh the documents table
        if (this.documentsComponent) {
          this.documentsComponent.loadDocuments();
        }
      },
      error: (error) => {
        console.error('Error generating packing list:', error);
        this.generatingPdf.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to generate packing list',
        });
      },
    });
  }
}
