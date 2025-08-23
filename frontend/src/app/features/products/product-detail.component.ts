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
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { DividerModule } from 'primeng/divider';

// Services
import { TranslateModule } from '@ngx-translate/core';
import {
  ProductService,
  Product,
  CreateProductData,
} from '../../core/services/product.service';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-product-detail',
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
    ToastModule,
    ProgressSpinnerModule,
    DividerModule,
    TranslateModule,
  ],
  providers: [MessageService],
  templateUrl: './product-detail.component.html',
})
export class ProductDetailComponent implements OnInit {
  private productService = inject(ProductService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(FormBuilder);
  private messageService = inject(MessageService);

  // State
  product = signal<Product | null>(null);
  loading = signal(false);
  saving = signal(false);
  isEditMode = signal(false);
  isNewProduct = signal(false);

  // Form
  productForm: FormGroup;

  // Options
  statusOptions = this.productService.getProductStatuses();
  formOptions = this.productService.getProductForms();

  constructor() {
    this.productForm = this.fb.group({
      gtin: ['', [Validators.required, Validators.pattern(/^\d{8,14}$/)]],
      name: ['', [Validators.required, Validators.maxLength(255)]],
      description: [''],
      form: ['', Validators.required],
      strength: ['', Validators.maxLength(100)],
      storage_temp_min: [null],
      storage_temp_max: [null],
      storage_humidity_min: [null],
      storage_humidity_max: [null],
      manufacturer: ['', Validators.maxLength(255)],
      ndc: ['', Validators.maxLength(11)],
      status: ['active', Validators.required],
      approval_number: ['', Validators.maxLength(100)],
    });
  }

  ngOnInit() {
    const productId = this.route.snapshot.paramMap.get('id');
    const isEdit = this.route.snapshot.url.some(
      (segment) => segment.path === 'edit'
    );
    const isNewRoute = this.route.snapshot.url.some(
      (segment) => segment.path === 'new'
    );

    if (productId === 'new' || isNewRoute) {
      this.isNewProduct.set(true);
      this.isEditMode.set(true);
      this.updateFormState();
    } else if (productId) {
      this.loadProduct(parseInt(productId, 10));
      this.isEditMode.set(isEdit);
      this.updateFormState();
    }
  }

  loadProduct(id: number) {
    this.loading.set(true);
    this.productService.getById(id).subscribe({
      next: (product) => {
        this.product.set(product);
        this.populateForm(product);
        this.updateFormState();
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Error loading product:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load product',
        });
        this.loading.set(false);
        this.router.navigate(['/products']);
      },
    });
  }

  populateForm(product: Product) {
    this.productForm.patchValue({
      gtin: product.gtin,
      name: product.name,
      description: product.description || '',
      form: product.form,
      strength: product.strength || '',
      storage_temp_min: product.storage_temp_min,
      storage_temp_max: product.storage_temp_max,
      storage_humidity_min: product.storage_humidity_min,
      storage_humidity_max: product.storage_humidity_max,
      manufacturer: product.manufacturer || '',
      ndc: product.ndc || '',
      status: product.status,
      approval_number: product.approval_number || '',
    });
  }

  toggleEditMode() {
    this.isEditMode.update((mode) => !mode);
    this.updateFormState();
    if (!this.isEditMode()) {
      // Reset form to original values
      if (this.product()) {
        this.populateForm(this.product()!);
      }
    }
  }

  private updateFormState() {
    if (this.isEditMode()) {
      this.productForm.enable();
    } else {
      this.productForm.disable();
    }
  }

  onSave() {
    if (this.productForm.invalid) {
      this.markFormGroupTouched();
      return;
    }

    this.saving.set(true);
    const formData = this.productForm.value as CreateProductData;

    const operation = this.isNewProduct()
      ? this.productService.create(formData)
      : this.productService.update(this.product()!.id, formData);

    operation.subscribe({
      next: (product) => {
        this.product.set(product);
        this.saving.set(false);
        this.isEditMode.set(false);

        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: this.isNewProduct()
            ? 'Product created successfully'
            : 'Product updated successfully',
        });

        if (this.isNewProduct()) {
          this.router.navigate(['/products', product.id]);
        }
      },
      error: (error) => {
        console.error('Error saving product:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to save product',
        });
        this.saving.set(false);
      },
    });
  }

  onCancel() {
    if (this.isNewProduct()) {
      this.router.navigate(['/products']);
    } else {
      this.toggleEditMode();
    }
  }

  onDelete() {
    if (!this.product()) return;

    this.productService.delete(this.product()!.id).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Product deleted successfully',
        });
        this.router.navigate(['/products']);
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
  }

  private markFormGroupTouched() {
    Object.keys(this.productForm.controls).forEach((key) => {
      const control = this.productForm.get(key);
      control?.markAsTouched();
    });
  }

  getFieldError(fieldName: string): string | null {
    const control = this.productForm.get(fieldName);
    if (control?.errors && control.touched) {
      if (control.errors['required']) {
        return `${fieldName} is required`;
      }
      if (control.errors['pattern']) {
        return `${fieldName} format is invalid`;
      }
      if (control.errors['maxlength']) {
        return `${fieldName} is too long`;
      }
    }
    return null;
  }

  goBack() {
    this.router.navigate(['/products']);
  }
}
