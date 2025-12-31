import {
  Component,
  Input,
  inject,
  signal,
  OnInit,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { FileUploadModule } from 'primeng/fileupload';
import { SelectModule } from 'primeng/select';
import { InputTextModule } from 'primeng/inputtext';
import { TextareaModule } from 'primeng/textarea';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

import { TranslateModule } from '@ngx-translate/core';
import { MessageService, ConfirmationService } from 'primeng/api';

import { DocumentService } from '../../core/services/document.service';
import {
  DocumentListItem,
  DocumentCategory,
  EntityType,
} from '../../core/models/document.model';

@Component({
  selector: 'app-entity-documents',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    TableModule,
    TagModule,
    ToastModule,
    ConfirmDialogModule,
    DialogModule,
    FileUploadModule,
    SelectModule,
    InputTextModule,
    TextareaModule,
    TooltipModule,
    ProgressSpinnerModule,
    TranslateModule,
  ],
  providers: [MessageService, ConfirmationService],
  template: `
    <p-toast></p-toast>
    <p-confirmDialog></p-confirmDialog>

    <p-card>
      <ng-template pTemplate="header">
        <div class="flex justify-between items-center p-4">
          <h4 class="font-semibold">
            <i class="pi pi-folder-open mr-2"></i>
            {{ 'pages.documents.title' | translate }}
          </h4>
          <div class="flex gap-2">
            <p-button
              *ngIf="showGenerateButtons && entityType === 'batch'"
              label="Generate CoA"
              icon="pi pi-file-pdf"
              size="small"
              severity="secondary"
              (onClick)="generateCoa()"
              [loading]="generating()"
            ></p-button>
            <p-button
              *ngIf="showGenerateButtons && entityType === 'shipment'"
              label="Generate Label"
              icon="pi pi-file-pdf"
              size="small"
              severity="secondary"
              (onClick)="generateLabel()"
              [loading]="generating()"
            ></p-button>
            <p-button
              *ngIf="showGenerateButtons && entityType === 'shipment'"
              label="Generate Packing List"
              icon="pi pi-file-pdf"
              size="small"
              severity="secondary"
              (onClick)="generatePackingList()"
              [loading]="generating()"
            ></p-button>
            <p-button
              label="Upload"
              icon="pi pi-upload"
              size="small"
              (onClick)="openUploadDialog()"
            ></p-button>
          </div>
        </div>
      </ng-template>

      <!-- Loading -->
      <div *ngIf="loading()" class="flex justify-center py-4">
        <p-progressSpinner
          [style]="{ width: '40px', height: '40px' }"
        ></p-progressSpinner>
      </div>

      <!-- Documents Table -->
      <p-table
        *ngIf="!loading()"
        [value]="documents()"
        styleClass="p-datatable-sm"
        [scrollable]="true"
        scrollHeight="300px"
      >
        <ng-template pTemplate="header">
          <tr>
            <th style="width: 2.5rem"></th>
            <th>Title</th>
            <th>Category</th>
            <th>Size</th>
            <th>Version</th>
            <th>Uploaded</th>
            <th style="width: 8rem">Actions</th>
          </tr>
        </ng-template>
        <ng-template pTemplate="body" let-doc>
          <tr>
            <td>
              <i [class]="getFileIcon(doc.file_type)"></i>
            </td>
            <td>
              <div class="flex flex-col">
                <span class="font-medium">{{ doc.title }}</span>
                <span class="text-xs text-gray-500">{{ doc.file_name }}</span>
              </div>
            </td>
            <td>
              <p-tag
                [value]="getCategoryLabel(doc.category)"
                [severity]="getCategorySeverity(doc.category)"
                [style]="{ 'font-size': '0.75rem' }"
              ></p-tag>
            </td>
            <td>{{ formatFileSize(doc.file_size) }}</td>
            <td>
              <span class="font-mono text-sm">v{{ doc.version_number }}</span>
            </td>
            <td>{{ doc.created_at | date : 'shortDate' }}</td>
            <td>
              <div class="flex gap-1">
                <p-button
                  icon="pi pi-download"
                  [rounded]="true"
                  [text]="true"
                  size="small"
                  (onClick)="downloadDocument(doc)"
                  pTooltip="Download"
                ></p-button>
                <p-button
                  icon="pi pi-eye"
                  [rounded]="true"
                  [text]="true"
                  size="small"
                  (onClick)="viewDocument(doc)"
                  pTooltip="View Details"
                ></p-button>
                <p-button
                  icon="pi pi-trash"
                  [rounded]="true"
                  [text]="true"
                  size="small"
                  severity="danger"
                  (onClick)="confirmDelete(doc)"
                  pTooltip="Delete"
                ></p-button>
              </div>
            </td>
          </tr>
        </ng-template>
        <ng-template pTemplate="emptymessage">
          <tr>
            <td colspan="7" class="text-center py-6 text-gray-500">
              <i class="pi pi-folder-open text-2xl mb-2"></i>
              <p>No documents attached</p>
              <p-button
                label="Upload First Document"
                icon="pi pi-upload"
                size="small"
                [text]="true"
                (onClick)="openUploadDialog()"
                class="mt-2"
              ></p-button>
            </td>
          </tr>
        </ng-template>
      </p-table>
    </p-card>

    <!-- Upload Dialog -->
    <p-dialog
      header="Upload Document"
      [(visible)]="showUploadDialog"
      [modal]="true"
      [style]="{ width: '450px' }"
      [draggable]="false"
    >
      <div class="flex flex-col gap-4">
        <!-- File -->
        <div class="flex flex-col">
          <label class="text-sm font-medium mb-2">
            File <span class="text-red-500">*</span>
          </label>
          <p-fileUpload
            mode="basic"
            [auto]="false"
            chooseLabel="Choose File"
            (onSelect)="onFileSelect($event)"
            [maxFileSize]="52428800"
            accept=".pdf,.png,.jpg,.jpeg,.doc,.docx,.xls,.xlsx,.csv,.txt"
          ></p-fileUpload>
          <small *ngIf="uploadFile()" class="text-green-600 mt-1">
            <i class="pi pi-check mr-1"></i>{{ uploadFile()?.name }}
          </small>
        </div>

        <!-- Title -->
        <div class="flex flex-col">
          <label class="text-sm font-medium mb-2">
            Title <span class="text-red-500">*</span>
          </label>
          <input
            type="text"
            pInputText
            [(ngModel)]="uploadTitle"
            placeholder="Document title"
          />
        </div>

        <!-- Description -->
        <div class="flex flex-col">
          <label class="text-sm font-medium mb-2">Description</label>
          <textarea
            pTextarea
            [(ngModel)]="uploadDescription"
            rows="2"
            placeholder="Optional description"
          ></textarea>
        </div>

        <!-- Category -->
        <div class="flex flex-col">
          <label class="text-sm font-medium mb-2">Category</label>
          <p-select
            [options]="categoryOptions"
            [(ngModel)]="uploadCategory"
            optionLabel="label"
            optionValue="value"
          ></p-select>
        </div>
      </div>

      <ng-template pTemplate="footer">
        <p-button
          label="Cancel"
          icon="pi pi-times"
          severity="secondary"
          (onClick)="showUploadDialog.set(false)"
        ></p-button>
        <p-button
          label="Upload"
          icon="pi pi-upload"
          (onClick)="uploadDocument()"
          [loading]="uploading()"
          [disabled]="!uploadFile() || !uploadTitle()"
        ></p-button>
      </ng-template>
    </p-dialog>
  `,
})
export class EntityDocumentsComponent implements OnInit, OnChanges {
  @Input({ required: true }) entityType!: EntityType;
  @Input({ required: true }) entityId!: number;
  @Input() showGenerateButtons = true;

  private documentService = inject(DocumentService);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);
  private router = inject(Router);

  // State
  documents = signal<DocumentListItem[]>([]);
  loading = signal(false);
  generating = signal(false);

  // Upload dialog
  showUploadDialog = signal(false);
  uploadFile = signal<File | null>(null);
  uploadTitle = signal('');
  uploadDescription = signal('');
  uploadCategory = signal<DocumentCategory>('other');
  uploading = signal(false);

  // Options
  categoryOptions = this.documentService.getCategories();

  ngOnInit(): void {
    this.loadDocuments();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['entityId'] || changes['entityType']) {
      this.loadDocuments();
    }
  }

  loadDocuments(): void {
    if (!this.entityType || !this.entityId) return;

    this.loading.set(true);
    this.documentService
      .getEntityDocuments(this.entityType, this.entityId)
      .subscribe({
        next: (docs) => {
          this.documents.set(docs);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
        },
      });
  }

  openUploadDialog(): void {
    this.uploadFile.set(null);
    this.uploadTitle.set('');
    this.uploadDescription.set('');
    this.uploadCategory.set('other');
    this.showUploadDialog.set(true);
  }

  onFileSelect(event: any): void {
    const file = event.files?.[0];
    if (file) {
      this.uploadFile.set(file);
      if (!this.uploadTitle()) {
        this.uploadTitle.set(file.name.replace(/\.[^/.]+$/, ''));
      }
    }
  }

  uploadDocument(): void {
    const file = this.uploadFile();
    const title = this.uploadTitle();

    if (!file || !title) return;

    this.uploading.set(true);
    this.documentService
      .upload(
        file,
        title,
        this.entityType,
        this.entityId,
        this.uploadCategory(),
        this.uploadDescription()
      )
      .subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Document uploaded successfully',
          });
          this.showUploadDialog.set(false);
          this.uploading.set(false);
          this.loadDocuments();
        },
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: err.error?.detail || 'Failed to upload document',
          });
          this.uploading.set(false);
        },
      });
  }

  downloadDocument(doc: DocumentListItem): void {
    this.documentService.getDownloadInfo(doc.id).subscribe({
      next: (info) => {
        window.open(info.download_url, '_blank');
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to get download link',
        });
      },
    });
  }

  viewDocument(doc: DocumentListItem): void {
    this.router.navigate(['/documents', doc.id]);
  }

  confirmDelete(doc: DocumentListItem): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete "${doc.title}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.deleteDocument(doc);
      },
    });
  }

  deleteDocument(doc: DocumentListItem): void {
    this.documentService.delete(doc.id).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Document deleted successfully',
        });
        this.loadDocuments();
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete document',
        });
      },
    });
  }

  generateLabel(): void {
    this.generating.set(true);
    this.documentService.generateShippingLabel(this.entityId, true).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Shipping label generated',
        });
        this.generating.set(false);
        this.loadDocuments();
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to generate shipping label',
        });
        this.generating.set(false);
      },
    });
  }

  generatePackingList(): void {
    this.generating.set(true);
    this.documentService.generatePackingList(this.entityId, true).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Packing list generated',
        });
        this.generating.set(false);
        this.loadDocuments();
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to generate packing list',
        });
        this.generating.set(false);
      },
    });
  }

  generateCoa(): void {
    this.generating.set(true);
    this.documentService.generateCoa(this.entityId, true).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Certificate of Analysis generated',
        });
        this.generating.set(false);
        this.loadDocuments();
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to generate CoA',
        });
        this.generating.set(false);
      },
    });
  }

  formatFileSize(bytes: number): string {
    return this.documentService.formatFileSize(bytes);
  }

  getFileIcon(fileType: string): string {
    return this.documentService.getFileIcon(fileType);
  }

  getCategoryLabel(category: DocumentCategory): string {
    const found = this.categoryOptions.find((c) => c.value === category);
    return found?.label || category;
  }

  getCategorySeverity(
    category: DocumentCategory
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' {
    const severityMap: Record<
      DocumentCategory,
      'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'
    > = {
      certificate: 'success',
      coa: 'success',
      invoice: 'info',
      packing_list: 'info',
      shipping_label: 'warn',
      msds: 'danger',
      quality_report: 'contrast',
      photo: 'secondary',
      other: 'secondary',
    };
    return severityMap[category] || 'secondary';
  }
}
