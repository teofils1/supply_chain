import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { DividerModule } from 'primeng/divider';
import { DialogModule } from 'primeng/dialog';
import { FileUploadModule } from 'primeng/fileupload';
import { TableModule } from 'primeng/table';
import { TooltipModule } from 'primeng/tooltip';

import { TranslateModule } from '@ngx-translate/core';
import { MessageService, ConfirmationService } from 'primeng/api';

import { DocumentService } from '../../core/services/document.service';
import {
  DocumentDetail,
  DocumentCategory,
} from '../../core/models/document.model';

@Component({
  selector: 'app-document-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    TagModule,
    ToastModule,
    ConfirmDialogModule,
    ProgressSpinnerModule,
    DividerModule,
    DialogModule,
    FileUploadModule,
    TableModule,
    TooltipModule,
    TranslateModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './document-detail.component.html',
})
export class DocumentDetailComponent implements OnInit {
  private documentService = inject(DocumentService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);

  // State
  document = signal<DocumentDetail | null>(null);
  loading = signal(false);

  // New version upload
  showVersionDialog = signal(false);
  newVersionFile = signal<File | null>(null);
  uploading = signal(false);

  // Options
  categoryOptions = this.documentService.getCategories();

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadDocument(parseInt(id, 10));
    }
  }

  loadDocument(id: number): void {
    this.loading.set(true);
    this.documentService.get(id).subscribe({
      next: (doc) => {
        this.document.set(doc);
        this.loading.set(false);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load document',
        });
        this.loading.set(false);
        this.router.navigate(['/documents']);
      },
    });
  }

  goBack(): void {
    this.router.navigate(['/documents']);
  }

  downloadDocument(): void {
    const doc = this.document();
    if (!doc) return;

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

  downloadVersion(versionId: number): void {
    this.documentService.getDownloadInfo(versionId).subscribe({
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

  viewVersion(versionId: number): void {
    this.router.navigate(['/documents', versionId]);
    this.loadDocument(versionId);
  }

  openVersionDialog(): void {
    this.newVersionFile.set(null);
    this.showVersionDialog.set(true);
  }

  onVersionFileSelect(event: any): void {
    const file = event.files?.[0];
    if (file) {
      this.newVersionFile.set(file);
    }
  }

  uploadNewVersion(): void {
    const doc = this.document();
    const file = this.newVersionFile();
    if (!doc || !file) return;

    this.uploading.set(true);
    this.documentService.uploadNewVersion(doc.id, file).subscribe({
      next: (newDoc) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'New version uploaded successfully',
        });
        this.showVersionDialog.set(false);
        this.uploading.set(false);
        this.document.set(newDoc);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to upload new version',
        });
        this.uploading.set(false);
      },
    });
  }

  confirmDelete(): void {
    const doc = this.document();
    if (!doc) return;

    this.confirmationService.confirm({
      message: `Are you sure you want to delete "${doc.title}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.deleteDocument();
      },
    });
  }

  deleteDocument(): void {
    const doc = this.document();
    if (!doc) return;

    this.documentService.delete(doc.id).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Document deleted successfully',
        });
        this.router.navigate(['/documents']);
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

  navigateToEntity(): void {
    const doc = this.document();
    if (!doc) return;
    this.router.navigate([`/${doc.entity_type}s`, doc.object_id]);
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
