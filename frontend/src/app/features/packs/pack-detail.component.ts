import { Component, inject, signal, OnInit, computed } from '@angular/core';
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
import { ProgressBarModule } from 'primeng/progressbar';

// Services
import { TranslateModule } from '@ngx-translate/core';
import {
  PackService,
  Pack,
  CreatePackData,
} from '../../core/services/pack.service';
import { BatchService } from '../../core/services/batch.service';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-pack-detail',
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
    ProgressBarModule,
    TranslateModule,
  ],
  providers: [MessageService],
  templateUrl: './pack-detail.component.html',
})
export class PackDetailComponent implements OnInit {
  private packService = inject(PackService);
  private batchService = inject(BatchService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(FormBuilder);
  private messageService = inject(MessageService);

  // State
  pack = signal<Pack | null>(null);
  loading = signal(false);
  saving = signal(false);

  // Form
  packForm: FormGroup;

  // Mode detection
  packId = signal<number | null>(null);
  isEditMode = computed(() =>
    this.route.snapshot.url.some((segment) => segment.path === 'edit')
  );
  isCreateMode = computed(() =>
    this.route.snapshot.url.some((segment) => segment.path === 'new')
  );
  isViewMode = computed(() => !this.isEditMode() && !this.isCreateMode());

  // Options
  batches = this.batchService.batches;
  statusOptions = this.packService.getPackStatuses();
  packTypeOptions = this.packService.getPackTypes();

  // Expose Math for template
  Math = Math;

  constructor() {
    this.packForm = this.fb.group({
      batch: [null, [Validators.required]],
      serial_number: ['', [Validators.required, Validators.maxLength(100)]],
      pack_size: [1, [Validators.required, Validators.min(1)]],
      pack_type: ['', [Validators.required]],
      manufacturing_date: [null],
      expiry_date: [null],
      status: ['active', [Validators.required]],
      location: [''],
      warehouse_section: [''],
      quality_control_notes: [''],
      quality_control_passed: [true],
      regulatory_code: [''],
      customer_reference: [''],
      shipped_date: [null],
      delivered_date: [null],
      tracking_number: [''],
    });
  }

  ngOnInit() {
    // Load batches for dropdown
    this.batchService.load().subscribe();

    // Get pack ID from route
    const id = this.route.snapshot.paramMap.get('id');
    if (id && id !== 'new') {
      this.packId.set(parseInt(id, 10));
      this.loadPack();
    }

    // Disable form in view mode
    if (this.isViewMode()) {
      this.packForm.disable();
    }
  }

  loadPack() {
    const id = this.packId();
    if (!id) return;

    this.loading.set(true);
    this.packService.getById(id).subscribe({
      next: (pack) => {
        this.pack.set(pack);
        this.populateForm(pack);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Error loading pack:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load pack details',
        });
        this.loading.set(false);
      },
    });
  }

  populateForm(pack: Pack) {
    // Convert date strings to Date objects for the form
    const manufacturingDate = pack.manufacturing_date
      ? new Date(pack.manufacturing_date)
      : null;
    const expiryDate = pack.expiry_date ? new Date(pack.expiry_date) : null;
    const shippedDate = pack.shipped_date ? new Date(pack.shipped_date) : null;
    const deliveredDate = pack.delivered_date
      ? new Date(pack.delivered_date)
      : null;

    this.packForm.patchValue({
      batch: pack.batch,
      serial_number: pack.serial_number,
      pack_size: pack.pack_size,
      pack_type: pack.pack_type,
      manufacturing_date: manufacturingDate,
      expiry_date: expiryDate,
      status: pack.status,
      location: pack.location || '',
      warehouse_section: pack.warehouse_section || '',
      quality_control_notes: pack.quality_control_notes || '',
      quality_control_passed: pack.quality_control_passed,
      regulatory_code: pack.regulatory_code || '',
      customer_reference: pack.customer_reference || '',
      shipped_date: shippedDate,
      delivered_date: deliveredDate,
      tracking_number: pack.tracking_number || '',
    });
  }

  onSubmit() {
    if (this.packForm.invalid) {
      this.markFormGroupTouched();
      return;
    }

    this.saving.set(true);
    const formData = this.getFormData();

    if (this.isCreateMode()) {
      this.packService.create(formData).subscribe({
        next: (pack) => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Pack created successfully',
          });
          this.router.navigate(['/packs', pack.id]);
        },
        error: (error) => {
          console.error('Error creating pack:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to create pack',
          });
          this.saving.set(false);
        },
      });
    } else if (this.isEditMode()) {
      const id = this.packId();
      if (id) {
        this.packService.update(id, formData).subscribe({
          next: (pack) => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Pack updated successfully',
            });
            this.router.navigate(['/packs', pack.id]);
          },
          error: (error) => {
            console.error('Error updating pack:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to update pack',
            });
            this.saving.set(false);
          },
        });
      }
    }
  }

  private getFormData(): CreatePackData {
    const formValue = this.packForm.value;

    return {
      batch: formValue.batch,
      serial_number: formValue.serial_number,
      pack_size: formValue.pack_size,
      pack_type: formValue.pack_type,
      manufacturing_date: formValue.manufacturing_date
        ? this.formatDate(formValue.manufacturing_date)
        : undefined,
      expiry_date: formValue.expiry_date
        ? this.formatDate(formValue.expiry_date)
        : undefined,
      status: formValue.status,
      location: formValue.location || undefined,
      warehouse_section: formValue.warehouse_section || undefined,
      quality_control_notes: formValue.quality_control_notes || undefined,
      quality_control_passed: formValue.quality_control_passed,
      regulatory_code: formValue.regulatory_code || undefined,
      customer_reference: formValue.customer_reference || undefined,
      shipped_date: formValue.shipped_date
        ? formValue.shipped_date.toISOString()
        : undefined,
      delivered_date: formValue.delivered_date
        ? formValue.delivered_date.toISOString()
        : undefined,
      tracking_number: formValue.tracking_number || undefined,
    };
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  private markFormGroupTouched() {
    Object.keys(this.packForm.controls).forEach((key) => {
      const control = this.packForm.get(key);
      control?.markAsTouched();
    });
  }

  enableEdit() {
    this.router.navigate(['/packs', this.packId(), 'edit']);
  }

  cancel() {
    if (this.isCreateMode()) {
      this.router.navigate(['/packs']);
    } else {
      this.router.navigate(['/packs', this.packId()]);
    }
  }

  goBack() {
    this.router.navigate(['/packs']);
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

  getExpiryStatusSeverity(pack: Pack): 'success' | 'warning' | 'danger' {
    if (pack.is_expired) {
      return 'danger';
    } else if (pack.days_until_expiry <= 30) {
      return 'warning';
    }
    return 'success';
  }

  getSelectedBatch() {
    const batchId = this.packForm.get('batch')?.value;
    return this.batches().find((b) => b.id === batchId);
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.packForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  getFieldError(fieldName: string): string {
    const field = this.packForm.get(fieldName);
    if (field?.errors) {
      if (field.errors['required']) return `${fieldName} is required`;
      if (field.errors['maxlength']) return `${fieldName} is too long`;
      if (field.errors['min'])
        return `${fieldName} must be greater than ${field.errors['min'].min}`;
    }
    return '';
  }
}
