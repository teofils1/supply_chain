import {
  HttpInterceptorFn,
  HttpResponse,
  HttpEvent,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Observable, of, tap, shareReplay, filter, take } from 'rxjs';
import { CacheService, CACHE_CONFIGS } from '../core/services/cache.service';

/**
 * HTTP interceptor that caches GET requests.
 *
 * Features:
 * - Only caches GET requests
 * - Respects Cache-Control headers
 * - Deduplicates in-flight requests
 * - Uses entity-specific TTLs
 */
export const cacheInterceptor: HttpInterceptorFn = (
  req,
  next
): Observable<HttpEvent<unknown>> => {
  const cacheService = inject(CacheService);

  // Only cache GET requests
  if (req.method !== 'GET') {
    // Invalidate cache for mutations
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method)) {
      const entityType = getEntityTypeFromUrl(req.url);
      if (entityType) {
        cacheService.invalidateEntity(entityType);
      }
    }
    return next(req);
  }

  // Skip caching for certain endpoints
  if (shouldSkipCache(req.url)) {
    return next(req);
  }

  // Generate cache key
  const cacheKey = cacheService.generateKey(
    req.url,
    req.params.keys().reduce((acc, key) => {
      acc[key] = req.params.get(key);
      return acc;
    }, {} as Record<string, string | null>)
  );

  // Check for cached response
  const cachedResponse = cacheService.get<HttpResponse<unknown>>(cacheKey);
  if (cachedResponse) {
    console.log('[Cache HIT]', cacheKey);
    return of(cachedResponse.clone());
  }

  console.log('[Cache MISS]', cacheKey);

  // Check for pending request (deduplication)
  const pendingRequest =
    cacheService.getPendingRequest<HttpEvent<unknown>>(cacheKey);
  if (pendingRequest) {
    return pendingRequest;
  }

  // Get cache config based on entity type
  const entityType = getEntityTypeFromUrl(req.url);
  const cacheConfig = entityType
    ? CACHE_CONFIGS[entityType] || CACHE_CONFIGS['default']
    : CACHE_CONFIGS['default'];

  // Make the request and cache the response
  const request$ = next(req).pipe(
    tap((event) => {
      if (event instanceof HttpResponse && event.status === 200) {
        cacheService.set(cacheKey, event.clone(), cacheConfig);
      }
    }),
    shareReplay(1)
  );

  // Store as pending request for deduplication
  cacheService.setPendingRequest(cacheKey, request$);

  // Return the shared observable that filters to HttpResponse and emits first result
  return request$.pipe(
    filter(
      (event): event is HttpEvent<unknown> => event instanceof HttpResponse
    ),
    take(1),
    tap(() => {
      // Remove from pending after complete
      cacheService.removePendingRequest(cacheKey);
    })
  );
};

/**
 * Extract entity type from URL for cache configuration
 */
function getEntityTypeFromUrl(
  url: string
): 'products' | 'batches' | 'packs' | 'shipments' | 'events' | 'users' | null {
  if (url.includes('/api/products')) return 'products';
  if (url.includes('/api/batches')) return 'batches';
  if (url.includes('/api/packs')) return 'packs';
  if (url.includes('/api/shipments')) return 'shipments';
  if (url.includes('/api/events')) return 'events';
  if (url.includes('/api/users')) return 'users';
  return null;
}

/**
 * Check if URL should skip caching
 */
function shouldSkipCache(url: string): boolean {
  const skipPatterns = [
    '/api/auth/',
    '/api/me',
    '/api/schema',
    '/api/docs',
    '/health',
  ];
  return skipPatterns.some((pattern) => url.includes(pattern));
}
