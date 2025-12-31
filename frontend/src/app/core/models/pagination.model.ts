import { environment } from '../../../environments/environment';

/**
 * Paginated response interface matching the backend pagination format.
 *
 * Backend returns:
 * {
 *   count: number,
 *   total_pages: number,
 *   current_page: number,
 *   page_size: number,
 *   next: string | null,
 *   previous: string | null,
 *   results: T[]
 * }
 */
export interface PaginatedResponse<T> {
  count: number;
  total_pages: number;
  current_page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Pagination parameters for API requests
 */
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

/**
 * Lazy load event from PrimeNG Table
 */
export interface LazyLoadEvent {
  first?: number | null;
  rows?: number | null;
  sortField?: string | null;
  sortOrder?: number | null;
  filters?: Record<string, any>;
}

/**
 * Default pagination values from environment
 */
export const DEFAULT_PAGE_SIZE = environment.pagination.defaultPageSize;
export const PAGE_SIZE_OPTIONS = environment.pagination.pageSizeOptions;

/**
 * Convert PrimeNG lazy load event to pagination params
 */
export function lazyLoadToParams(event: LazyLoadEvent): PaginationParams {
  const first = event.first ?? 0;
  const rows = event.rows ?? DEFAULT_PAGE_SIZE;
  const page = rows > 0 ? Math.floor(first / rows) + 1 : 1;

  return {
    page,
    page_size: rows,
  };
}
