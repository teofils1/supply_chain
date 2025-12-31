import {
  Component,
  OnInit,
  signal,
  computed,
  inject,
  OnDestroy,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { RippleModule } from 'primeng/ripple';
import { ProgressBarModule } from 'primeng/progressbar';
import { TagModule } from 'primeng/tag';
import { SkeletonModule } from 'primeng/skeleton';
import { TooltipModule } from 'primeng/tooltip';
import { TranslateModule } from '@ngx-translate/core';
import { CommonModule } from '@angular/common';
import { interval, Subscription, switchMap, startWith, tap } from 'rxjs';

import {
  EventService,
  type EventListItem,
} from '../../core/services/event.service';
import { ProductService } from '../../core/services/product.service';
import { BatchService } from '../../core/services/batch.service';
import { PackService } from '../../core/services/pack.service';
import { ShipmentService } from '../../core/services/shipment.service';

interface DashboardStats {
  totalProducts: number;
  totalBatches: number;
  totalPacks: number;
  totalShipments: number;
  activeShipments: number;
  criticalEvents: number;
}

@Component({
  selector: 'app-welcome',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    ButtonModule,
    CardModule,
    RippleModule,
    ProgressBarModule,
    TagModule,
    SkeletonModule,
    TooltipModule,
    TranslateModule,
  ],
  templateUrl: './welcome.component.html',
})
export class WelcomeComponent implements OnInit, OnDestroy {
  private eventService = inject(EventService);
  private productService = inject(ProductService);
  private batchService = inject(BatchService);
  private packService = inject(PackService);
  private shipmentService = inject(ShipmentService);

  // Signals for reactive data
  recentEvents = signal<EventListItem[]>([]);
  stats = signal<DashboardStats>({
    totalProducts: 0,
    totalBatches: 0,
    totalPacks: 0,
    totalShipments: 0,
    activeShipments: 0,
    criticalEvents: 0,
  });
  loading = signal(true);
  error = signal<string | null>(null);

  // Computed values
  systemHealth = computed(() => {
    const currentStats = this.stats();
    const events = this.recentEvents();

    const criticalCount = events.filter(
      (e) => e.severity === 'critical'
    ).length;
    const errorCount = events.filter((e) => e.event_type === 'error').length;

    if (criticalCount > 0 || errorCount > 2) {
      return { status: 'warning', text: 'Needs Attention', color: 'orange' };
    } else if (events.some((e) => e.severity === 'high')) {
      return { status: 'caution', text: 'Monitor', color: 'yellow' };
    }
    return { status: 'operational', text: 'Operational', color: 'green' };
  });

  private refreshSubscription?: Subscription;

  ngOnInit() {
    this.loadDashboardData();

    // Set up automatic refresh every 30 seconds
    this.refreshSubscription = interval(30000)
      .pipe(
        startWith(0),
        switchMap(() => this.loadRecentEvents())
      )
      .subscribe();
  }

  ngOnDestroy() {
    this.refreshSubscription?.unsubscribe();
  }

  private async loadDashboardData() {
    try {
      this.loading.set(true);
      this.error.set(null);

      // Load recent events and stats in parallel
      const [events] = await Promise.all([
        this.loadRecentEvents().toPromise(),
        this.loadStats(),
      ]);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      this.error.set('Failed to load dashboard data');
    } finally {
      this.loading.set(false);
    }
  }

  private loadRecentEvents() {
    return this.eventService.load({ recent_days: 7 }).pipe(
      tap((response) => {
        // Sort by timestamp descending and take latest 5
        const sortedEvents = response.results
          .sort(
            (a: EventListItem, b: EventListItem) =>
              new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
          )
          .slice(0, 5);
        this.recentEvents.set(sortedEvents);
      })
    );
  }

  private async loadStats() {
    try {
      // Load all stats in parallel
      const [products, batches, packs, shipments] = await Promise.all([
        this.productService.load().toPromise(),
        this.batchService.load().toPromise(),
        this.packService.load().toPromise(),
        this.shipmentService.load().toPromise(),
      ]);

      const activeShipments =
        shipments?.results.filter((s) =>
          ['picked_up', 'in_transit', 'out_for_delivery'].includes(s.status)
        ).length || 0;

      const events = this.recentEvents();
      const criticalEvents = events.filter(
        (e) => e.severity === 'critical' || e.is_critical
      ).length;

      this.stats.set({
        totalProducts: products?.count || 0,
        totalBatches: batches?.count || 0,
        totalPacks: packs?.count || 0,
        totalShipments: shipments?.count || 0,
        activeShipments,
        criticalEvents,
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  }

  getEventIcon(eventType: string): string {
    return this.eventService.getEventTypeIcon(eventType as any);
  }

  getEventIconColor(severity: string): string {
    switch (severity) {
      case 'critical':
        return 'text-red-500';
      case 'high':
        return 'text-orange-500';
      case 'medium':
        return 'text-yellow-500';
      case 'low':
        return 'text-blue-500';
      default:
        return 'text-gray-500';
    }
  }

  getRelativeTime(timestamp: string): string {
    return this.eventService.getRelativeTime(timestamp);
  }

  refresh() {
    this.loadDashboardData();
  }

  getCurrentTime(): string {
    return new Date().toLocaleString();
  }
}
