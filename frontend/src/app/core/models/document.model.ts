export type DocumentCategory =
  | 'certificate'
  | 'invoice'
  | 'packing_list'
  | 'shipping_label'
  | 'coa'
  | 'msds'
  | 'quality_report'
  | 'photo'
  | 'other';

export type EntityType = 'product' | 'batch' | 'pack' | 'shipment';

export interface Document {
  id: number;
  title: string;
  description?: string;
  category: DocumentCategory;
  file_name: string;
  file_size: number;
  file_type: string;
  file_hash?: string;
  file_url: string;
  entity_type: EntityType;
  object_id: number;
  version_number: number;
  is_latest: boolean;
  parent_document?: number;
  uploaded_by?: number;
  uploaded_by_name?: string;
  created_at: string;
  updated_at?: string;
}

export interface DocumentListItem {
  id: number;
  title: string;
  category: DocumentCategory;
  file_name: string;
  file_size: number;
  file_type: string;
  file_url: string;
  entity_type: EntityType;
  object_id: number;
  version_number: number;
  is_latest: boolean;
  uploaded_by_name?: string;
  created_at: string;
}

export interface DocumentVersion {
  id: number;
  version_number: number;
  is_latest: boolean;
  created_at: string;
}

export interface DocumentDetail extends Document {
  versions: DocumentVersion[];
}

export interface DocumentUploadData {
  file: File;
  title: string;
  description?: string;
  category: DocumentCategory;
  entity_type: EntityType;
  entity_id: number;
}

export interface DocumentFilters {
  entity_type?: EntityType;
  entity_id?: number;
  category?: DocumentCategory;
  search?: string;
  latest_only?: boolean;
}

export interface DownloadInfo {
  download_url: string;
  file_name: string;
  file_type: string;
  file_size: number;
}

export interface GeneratedPdfResponse {
  id: number;
  title: string;
  file_url: string;
  file_name: string;
  created_at: string;
}
