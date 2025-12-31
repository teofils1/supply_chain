import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

/**
 * Cache entry with expiration tracking
 */
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

/**
 * Cache configuration
 */
export interface CacheConfig {
  /** Time to live in milliseconds */
  ttl: number;
  /** Maximum number of entries */
  maxEntries?: number;
}

/**
 * Default cache configurations for different entity types
 */
export const CACHE_CONFIGS: Record<string, CacheConfig> = {
  products: { ttl: 60000, maxEntries: 100 }, // 1 minute
  batches: { ttl: 30000, maxEntries: 100 }, // 30 seconds
  packs: { ttl: 30000, maxEntries: 100 }, // 30 seconds
  shipments: { ttl: 30000, maxEntries: 100 }, // 30 seconds
  events: { ttl: 60000, maxEntries: 200 }, // 1 minute
  users: { ttl: 120000, maxEntries: 50 }, // 2 minutes
  default: { ttl: 60000, maxEntries: 100 }, // 1 minute
};

/**
 * Client-side caching service for API responses.
 *
 * Features:
 * - TTL-based expiration
 * - LRU eviction when max entries reached
 * - Automatic cleanup of expired entries
 * - Request deduplication (prevents duplicate in-flight requests)
 */
@Injectable({ providedIn: 'root' })
export class CacheService {
  private cache = new Map<string, CacheEntry<any>>();
  private pendingRequests = new Map<string, Observable<any>>();

  constructor() {
    // Periodic cleanup of expired entries
    setInterval(() => this.cleanup(), 60000);
  }

  /**
   * Generate a cache key from URL and params
   */
  generateKey(url: string, params?: Record<string, any>): string {
    const sortedParams = params
      ? Object.keys(params)
          .sort()
          .map((k) => `${k}=${params[k]}`)
          .join('&')
      : '';
    return sortedParams ? `${url}?${sortedParams}` : url;
  }

  /**
   * Get a value from cache if it exists and hasn't expired
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  /**
   * Set a value in cache with TTL
   */
  set<T>(key: string, data: T, config?: CacheConfig): void {
    const cacheConfig = config || CACHE_CONFIGS['default'];
    const now = Date.now();

    // Evict oldest entries if at capacity
    if (cacheConfig.maxEntries && this.cache.size >= cacheConfig.maxEntries) {
      this.evictOldest();
    }

    this.cache.set(key, {
      data,
      timestamp: now,
      expiresAt: now + cacheConfig.ttl,
    });
  }

  /**
   * Check if a key exists and is valid
   */
  has(key: string): boolean {
    return this.get(key) !== null;
  }

  /**
   * Invalidate a specific cache entry
   */
  invalidate(key: string): void {
    this.cache.delete(key);
    this.pendingRequests.delete(key);
  }

  /**
   * Invalidate all entries matching a prefix
   */
  invalidateByPrefix(prefix: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(prefix)) {
        this.cache.delete(key);
      }
    }
    for (const key of this.pendingRequests.keys()) {
      if (key.startsWith(prefix)) {
        this.pendingRequests.delete(key);
      }
    }
  }

  /**
   * Invalidate all cache entries for an entity type
   */
  invalidateEntity(
    entityType:
      | 'products'
      | 'batches'
      | 'packs'
      | 'shipments'
      | 'events'
      | 'users'
  ): void {
    this.invalidateByPrefix(`/api/${entityType}`);
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    this.pendingRequests.clear();
  }

  /**
   * Get or set a pending request to prevent duplicate in-flight requests
   */
  getPendingRequest<T>(key: string): Observable<T> | null {
    return this.pendingRequests.get(key) || null;
  }

  /**
   * Set a pending request
   */
  setPendingRequest<T>(key: string, observable: Observable<T>): void {
    this.pendingRequests.set(key, observable);
  }

  /**
   * Remove a pending request after completion
   */
  removePendingRequest(key: string): void {
    this.pendingRequests.delete(key);
  }

  /**
   * Get cache statistics for debugging
   */
  getStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    };
  }

  /**
   * Clean up expired entries
   */
  private cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Evict the oldest entry (LRU-style)
   */
  private evictOldest(): void {
    let oldestKey: string | null = null;
    let oldestTime = Infinity;

    for (const [key, entry] of this.cache.entries()) {
      if (entry.timestamp < oldestTime) {
        oldestTime = entry.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }
}
