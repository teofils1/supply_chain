import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

// PrimeNG imports
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { DialogModule } from 'primeng/dialog';
import { FileUploadModule } from 'primeng/fileupload';
import { TextareaModule } from 'primeng/textarea';

import { TranslateModule } from '@ngx-translate/core';
import { MessageService, ConfirmationService } from 'primeng/api';

import { DocumentService } from '../../core/services/document.service';
import {
  DocumentListItem,
  DocumentCategory,
  EntityType,
} from '../../core/models/document.model';

@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    SelectModule,
    CardModule,
    TagModule,
    ToastModule,
    ConfirmDialogModule,
    TooltipModule,
    ProgressSpinnerModule,
    DialogModule,
    FileUploadModule,
    TextareaModule,
    TranslateModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './documents.component.html',
})
export class DocumentsComponent implements OnInit {
  private documentService = inject(DocumentService);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);
  private router = inject(Router);

  // State
  documents = this.documentService.documents;
  loading = this.documentService.loading;
  totalRecords = this.documentService.totalRecords;

  // Filters
  searchQuery = signal('');
  selectedCategory = signal<DocumentCategory | null>(null);
  selectedEntityType = signal<EntityType | null>(null);

  // Upload dialog
  showUploadDialog = signal(false);
  uploadFile = signal<File | null>(null);
  uploadTitle = signal('');
  uploadDescription = signal('');
  uploadCategory = signal<DocumentCategory>('other');
  uploadEntityType = signal<EntityType>('product');
  uploadEntityId = signal<number | null>(null);
  uploading = signal(false);

  // Options
  categoryOptions = this.documentService.getCategories();
  entityTypeOptions = this.documentService.getEntityTypes();

  // Pagination
  first = 0;
  rows = 10;

  ngOnInit(): void {
    this.loadDocuments();
  }

  loadDocuments(): void {
    this.documentService
      .load(
        {
          search: this.searchQuery() || undefined,
          category: this.selectedCategory() || undefined,
          entity_type: this.selectedEntityType() || undefined,
          latest_only: true,
        },
        {
          page: Math.floor(this.first / this.rows) + 1,
          page_size: this.rows,
        }
      )
      .subscribe({
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to load documents',
          });
        },
      });
  }

  onSearch(): void {
    this.first = 0;
    this.loadDocuments();
  }

  onFilterChange(): void {
    this.first = 0;
    this.loadDocuments();
  }

  clearFilters(): void {
    this.searchQuery.set('');
    this.selectedCategory.set(null);
    this.selectedEntityType.set(null);
    this.first = 0;
    this.loadDocuments();
  }

  onPageChange(event: any): void {
    this.first = event.first;
    this.rows = event.rows;
    this.loadDocuments();
  }

  openUploadDialog(): void {
    this.uploadFile.set(null);
    this.uploadTitle.set('');
    this.uploadDescription.set('');
    this.uploadCategory.set('other');
    this.uploadEntityType.set('product');
    this.uploadEntityId.set(null);
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
    const entityId = this.uploadEntityId();

    if (!file || !title || !entityId) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Validation',
        detail: 'Please fill all required fields',
      });
      return;
    }

    this.uploading.set(true);
    this.documentService
      .upload(
        file,
        title,
        this.uploadEntityType(),
        entityId,
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

  navigateToEntity(doc: DocumentListItem): void {
    const entityType = doc.entity_type;
    const entityId = doc.object_id;
    this.router.navigate([`/${entityType}s`, entityId]);
  }
}
