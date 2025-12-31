import { Component, inject, signal, OnInit } from '@angular/core';
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
import { TextareaModule } from 'primeng/textarea';
import { InputNumberModule } from 'primeng/inputnumber';
import { SelectModule } from 'primeng/select';
import { DatePickerModule } from 'primeng/datepicker';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ProgressBarModule } from 'primeng/progressbar';
import { DividerModule } from 'primeng/divider';
import { CheckboxModule } from 'primeng/checkbox';
import { TagModule } from 'primeng/tag';

// Services
import { TranslateModule } from '@ngx-translate/core';
import {
  BatchService,
  Batch,
  CreateBatchData,
} from '../../core/services/batch.service';
import { ProductService } from '../../core/services/product.service';
import { MessageService } from 'primeng/api';
import { EntityDocumentsComponent } from '../documents/entity-documents.component';

@Component({
  selector: 'app-batch-detail',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    CardModule,
    ButtonModule,
    InputTextModule,
    TextareaModule,
    InputNumberModule,
    SelectModule,
    DatePickerModule,
    ToastModule,
    ProgressSpinnerModule,
    ProgressBarModule,
    DividerModule,
    CheckboxModule,
    TagModule,
    TranslateModule,
    EntityDocumentsComponent,
  ],
  providers: [MessageService],
  templateUrl: './batch-detail.component.html',
})
export class BatchDetailComponent implements OnInit {
  private batchService = inject(BatchService);
  private productService = inject(ProductService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(FormBuilder);
  private messageService = inject(MessageService);

  // State
  batch = signal<Batch | null>(null);
  loading = signal(false);
  saving = signal(false);
  isEditMode = signal(false);
  isNewBatch = signal(false);

  // Form
  batchForm: FormGroup;

  // Options
  products = this.productService.products;
  statusOptions = this.batchService.getBatchStatuses();

  // Expose Math for template
  Math = Math;

  constructor() {
    this.batchForm = this.fb.group({
      product: [null, Validators.required],
      lot_number: ['', [Validators.required, Validators.maxLength(100)]],
      manufacturing_date: [null, Validators.required],
      expiry_date: [null, Validators.required],
      quantity_produced: [null, [Validators.required, Validators.min(1)]],
      manufacturing_location: ['', Validators.maxLength(255)],
      manufacturing_facility: ['', Validators.maxLength(255)],
      status: ['active', Validators.required],
      quality_control_notes: [''],
      quality_control_passed: [true],
      batch_size: ['', Validators.maxLength(100)],
      supplier_batch_number: ['', Validators.maxLength(100)],
      regulatory_approval_number: ['', Validators.maxLength(100)],
      certificate_of_analysis: ['', Validators.maxLength(255)],
    });
  }

  ngOnInit() {
    // Load products for the dropdown
    this.productService.load().subscribe();

    const batchId = this.route.snapshot.paramMap.get('id');
    const isNewRoute = this.route.snapshot.url.some(
      (segment) => segment.path === 'new'
    );
    const isEdit = this.route.snapshot.url.some(
      (segment) => segment.path === 'edit'
    );

    if (batchId === 'new' || isNewRoute) {
      this.isNewBatch.set(true);
      this.isEditMode.set(true);
      this.updateFormState();
    } else if (batchId) {
      this.loadBatch(parseInt(batchId, 10));
      this.isEditMode.set(isEdit);
      this.updateFormState();
    }
  }

  loadBatch(id: number) {
    this.loading.set(true);
    this.batchService.getById(id).subscribe({
      next: (batch) => {
        this.batch.set(batch);
        this.populateForm(batch);
        this.loading.set(false);
        this.updateFormState();
      },
      error: (error) => {
        console.error('Error loading batch:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load batch',
        });
        this.loading.set(false);
        this.router.navigate(['/batches']);
      },
    });
  }

  populateForm(batch: Batch) {
    this.batchForm.patchValue({
      product: batch.product,
      lot_number: batch.lot_number,
      manufacturing_date: new Date(batch.manufacturing_date),
      expiry_date: new Date(batch.expiry_date),
      quantity_produced: batch.quantity_produced,
      manufacturing_location: batch.manufacturing_location || '',
      manufacturing_facility: batch.manufacturing_facility || '',
      status: batch.status,
      quality_control_notes: batch.quality_control_notes || '',
      quality_control_passed: batch.quality_control_passed,
      batch_size: batch.batch_size || '',
      supplier_batch_number: batch.supplier_batch_number || '',
      regulatory_approval_number: batch.regulatory_approval_number || '',
      certificate_of_analysis: batch.certificate_of_analysis || '',
    });
  }

  toggleEditMode() {
    this.isEditMode.update((mode) => !mode);
    if (!this.isEditMode()) {
      // Reset form to original values
      if (this.batch()) {
        this.populateForm(this.batch()!);
      }
    }
    this.updateFormState();
  }

  onSave() {
    if (this.batchForm.invalid) {
      this.markFormGroupTouched();
      return;
    }

    this.saving.set(true);
    const formData = this.prepareSaveData();

    const operation = this.isNewBatch()
      ? this.batchService.create(formData)
      : this.batchService.update(this.batch()!.id, formData);

    operation.subscribe({
      next: (batch) => {
        this.batch.set(batch);
        this.saving.set(false);
        this.isEditMode.set(false);
        this.updateFormState();

        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: this.isNewBatch()
            ? 'Batch created successfully'
            : 'Batch updated successfully',
        });

        if (this.isNewBatch()) {
          this.router.navigate(['/batches', batch.id]);
        }
      },
      error: (error) => {
        console.error('Error saving batch:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to save batch',
        });
        this.saving.set(false);
      },
    });
  }

  onCancel() {
    if (this.isNewBatch()) {
      this.router.navigate(['/batches']);
    } else {
      this.toggleEditMode();
    }
  }

  onDelete() {
    if (!this.batch()) return;

    this.batchService.delete(this.batch()!.id).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Batch deleted successfully',
        });
        this.router.navigate(['/batches']);
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
  }

  private prepareSaveData(): CreateBatchData {
    const formValue = this.batchForm.value;
    return {
      product: formValue.product,
      lot_number: formValue.lot_number,
      manufacturing_date: this.formatDate(formValue.manufacturing_date),
      expiry_date: this.formatDate(formValue.expiry_date),
      quantity_produced: formValue.quantity_produced,
      manufacturing_location: formValue.manufacturing_location || undefined,
      manufacturing_facility: formValue.manufacturing_facility || undefined,
      status: formValue.status,
      quality_control_notes: formValue.quality_control_notes || undefined,
      quality_control_passed: formValue.quality_control_passed,
      batch_size: formValue.batch_size || undefined,
      supplier_batch_number: formValue.supplier_batch_number || undefined,
      regulatory_approval_number:
        formValue.regulatory_approval_number || undefined,
      certificate_of_analysis: formValue.certificate_of_analysis || undefined,
    };
  }

  private updateFormState() {
    if (this.isEditMode()) {
      this.batchForm.enable();
    } else {
      this.batchForm.disable();
    }
  }

  private markFormGroupTouched() {
    Object.keys(this.batchForm.controls).forEach((key) => {
      const control = this.batchForm.get(key);
      control?.markAsTouched();
    });
  }

  private formatDate(date: Date): string {
    if (!date) return '';
    return date.toISOString().split('T')[0];
  }

  getFieldError(fieldName: string): string | null {
    const control = this.batchForm.get(fieldName);
    if (control?.errors && control.touched) {
      if (control.errors['required']) {
        return `${fieldName} is required`;
      }
      if (control.errors['min']) {
        return `${fieldName} must be greater than ${control.errors['min'].min}`;
      }
      if (control.errors['maxlength']) {
        return `${fieldName} is too long`;
      }
    }
    return null;
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

  getSelectedProductName(): string {
    const selectedProductId = this.batchForm.get('product')?.value;
    if (!selectedProductId) return '';

    const product = this.products().find((p) => p.id === selectedProductId);
    return product ? product.name : '';
  }

  goBack() {
    this.router.navigate(['/batches']);
  }
}
