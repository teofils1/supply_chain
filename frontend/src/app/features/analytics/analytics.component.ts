import {
  Component,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG Imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { SelectModule } from 'primeng/select';
import { TabsModule } from 'primeng/tabs';
import { ChartModule } from 'primeng/chart';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ProgressBarModule } from 'primeng/progressbar';
import { SkeletonModule } from 'primeng/skeleton';
import { TooltipModule } from 'primeng/tooltip';
import { DividerModule } from 'primeng/divider';
import { PanelModule } from 'primeng/panel';
import { BadgeModule } from 'primeng/badge';
import { MessageModule } from 'primeng/message';

import { TranslateModule } from '@ngx-translate/core';

import {
  AnalyticsService,
  SupplyChainKPIs,
  BatchYieldAnalysis,
  CarrierPerformance,
  TemperatureExcursions,
  DemandForecast,
  AnalyticsSummary,
} from '../../core/services/analytics.service';
import { Subscription, forkJoin } from 'rxjs';

interface PeriodOption {
  label: string;
  value: number;
}

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    SelectModule,
    TabsModule,
    ChartModule,
    TableModule,
    TagModule,
    ProgressBarModule,
    SkeletonModule,
    TooltipModule,
    DividerModule,
    PanelModule,
    BadgeModule,
    MessageModule,
    TranslateModule,
  ],
  templateUrl: './analytics.component.html',
  styleUrl: './analytics.component.css',
})
export class AnalyticsComponent implements OnInit, OnDestroy {
  private analyticsService = inject(AnalyticsService);
  private subscriptions: Subscription[] = [];

  // Period selection
  periodOptions: PeriodOption[] = [
    { label: 'Last 7 Days', value: 7 },
    { label: 'Last 30 Days', value: 30 },
    { label: 'Last 90 Days', value: 90 },
    { label: 'Last 180 Days', value: 180 },
    { label: 'Last 365 Days', value: 365 },
  ];
  selectedPeriod = signal(30);

  // Loading states
  loading = signal(true);
  error = signal<string | null>(null);

  // Data from service
  summary = this.analyticsService.summary;
  kpis = this.analyticsService.kpis;
  batchYield = this.analyticsService.batchYield;
  carrierPerformance = this.analyticsService.carrierPerformance;
  temperatureExcursions = this.analyticsService.temperatureExcursions;
  demandForecast = this.analyticsService.demandForecast;

  // Chart configurations
  kpiChartData = computed(() => {
    const data = this.kpis();
    if (!data) return null;

    return {
      labels: ['On-Time', 'Late', 'Damaged', 'Lost', 'Returned'],
      datasets: [
        {
          data: [
            data.on_time_delivery_rate,
            data.late_delivery_rate,
            data.damage_rate,
            data.loss_rate,
            data.return_rate,
          ],
          backgroundColor: [
            '#22c55e',
            '#f59e0b',
            '#ef4444',
            '#8b5cf6',
            '#3b82f6',
          ],
          hoverBackgroundColor: [
            '#16a34a',
            '#d97706',
            '#dc2626',
            '#7c3aed',
            '#2563eb',
          ],
        },
      ],
    };
  });

  dailyShipmentsChartData = computed(() => {
    const data = this.kpis();
    if (!data?.daily_shipments) return null;

    return {
      labels: data.daily_shipments.map((d) =>
        new Date(d.day).toLocaleDateString('en-US', {
          weekday: 'short',
          month: 'short',
          day: 'numeric',
        })
      ),
      datasets: [
        {
          label: 'Daily Shipments',
          data: data.daily_shipments.map((d) => d.count),
          fill: true,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          tension: 0.4,
        },
      ],
    };
  });

  batchStatusChartData = computed(() => {
    const data = this.batchYield();
    if (!data?.status_distribution) return null;

    const statusColors: { [key: string]: string } = {
      active: '#22c55e',
      released: '#3b82f6',
      quarantined: '#f59e0b',
      expired: '#6b7280',
      recalled: '#ef4444',
      destroyed: '#1f2937',
    };

    return {
      labels: data.status_distribution.map((s) => this.formatStatus(s.status)),
      datasets: [
        {
          data: data.status_distribution.map((s) => s.count),
          backgroundColor: data.status_distribution.map(
            (s) => statusColors[s.status] || '#6b7280'
          ),
        },
      ],
    };
  });

  weeklyProductionChartData = computed(() => {
    const data = this.batchYield();
    if (!data?.weekly_production) return null;

    return {
      labels: data.weekly_production.map((w) =>
        new Date(w.week).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        })
      ),
      datasets: [
        {
          label: 'Batches Created',
          data: data.weekly_production.map((w) => w.count),
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.2)',
          fill: true,
        },
        {
          label: 'Total Quantity',
          data: data.weekly_production.map((w) => w.total_quantity),
          borderColor: '#22c55e',
          backgroundColor: 'rgba(34, 197, 94, 0.2)',
          fill: true,
          yAxisID: 'y1',
        },
      ],
    };
  });

  carrierChartData = computed(() => {
    const data = this.carrierPerformance();
    if (!data?.carrier_performance) return null;

    return {
      labels: data.carrier_performance.map((c) => c.carrier_name),
      datasets: [
        {
          label: 'On-Time Rate (%)',
          data: data.carrier_performance.map((c) => c.on_time_rate),
          backgroundColor: '#22c55e',
        },
        {
          label: 'Damage Rate (%)',
          data: data.carrier_performance.map((c) => c.damage_rate),
          backgroundColor: '#ef4444',
        },
      ],
    };
  });

  temperatureTrendChartData = computed(() => {
    const data = this.temperatureExcursions();
    if (!data?.weekly_trend) return null;

    return {
      labels: data.weekly_trend.map((w) =>
        new Date(w.week).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        })
      ),
      datasets: [
        {
          label: 'Temperature Excursions',
          data: data.weekly_trend.map((w) => w.count),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          fill: true,
          tension: 0.4,
        },
      ],
    };
  });

  demandForecastChartData = computed(() => {
    const data = this.demandForecast();
    if (!data?.product_forecasts?.[0]) return null;

    const product = data.product_forecasts[0];

    return {
      labels: [
        ...product.historical_data.map((h) =>
          new Date(h.week).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
          })
        ),
        ...product.weekly_forecasts.map((f) =>
          new Date(f.week).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
          })
        ),
      ],
      datasets: [
        {
          label: 'Historical Demand',
          data: [
            ...product.historical_data.map((h) => h.demand),
            ...new Array(product.weekly_forecasts.length).fill(null),
          ],
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          fill: true,
        },
        {
          label: 'Forecasted Demand',
          data: [
            ...new Array(product.historical_data.length).fill(null),
            ...product.weekly_forecasts.map((f) => f.predicted_demand),
          ],
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.2)',
          borderDash: [5, 5],
          fill: true,
        },
      ],
    };
  });

  // Chart options
  chartOptions = {
    plugins: {
      legend: {
        labels: {
          usePointStyle: true,
          color: '#6b7280',
        },
      },
    },
    maintainAspectRatio: false,
  };

  lineChartOptions = {
    ...this.chartOptions,
    scales: {
      x: {
        ticks: { color: '#6b7280' },
        grid: { color: 'rgba(107, 114, 128, 0.1)' },
      },
      y: {
        ticks: { color: '#6b7280' },
        grid: { color: 'rgba(107, 114, 128, 0.1)' },
      },
    },
  };

  barChartOptions = {
    ...this.chartOptions,
    indexAxis: 'y' as const,
    scales: {
      x: {
        ticks: { color: '#6b7280' },
        grid: { color: 'rgba(107, 114, 128, 0.1)' },
        max: 100,
      },
      y: {
        ticks: { color: '#6b7280' },
        grid: { display: false },
      },
    },
  };

  dualAxisChartOptions = {
    ...this.chartOptions,
    scales: {
      x: {
        ticks: { color: '#6b7280' },
        grid: { color: 'rgba(107, 114, 128, 0.1)' },
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        ticks: { color: '#8b5cf6' },
        grid: { color: 'rgba(107, 114, 128, 0.1)' },
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        ticks: { color: '#22c55e' },
        grid: { drawOnChartArea: false },
      },
    },
  };

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach((sub) => sub.unsubscribe());
    this.analyticsService.clearAnalytics();
  }

  loadData(): void {
    this.loading.set(true);
    this.error.set(null);

    const period = this.selectedPeriod();

    const sub = forkJoin([
      this.analyticsService.getSummary(period),
      this.analyticsService.getKPIs(period),
      this.analyticsService.getBatchYieldAnalysis(period),
      this.analyticsService.getCarrierPerformance(period),
      this.analyticsService.getTemperatureExcursions(period),
      this.analyticsService.getDemandForecast(30, period * 6),
    ]).subscribe({
      next: () => {
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error loading analytics:', err);
        this.error.set('Failed to load analytics data. Please try again.');
        this.loading.set(false);
      },
    });

    this.subscriptions.push(sub);
  }

  onPeriodChange(event: any): void {
    this.selectedPeriod.set(event.value);
    this.loadData();
  }

  refreshData(): void {
    this.loadData();
  }

  formatStatus(status: string): string {
    return status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' ');
  }

  formatNumber(value: number | null | undefined): string {
    if (value == null) return '-';
    return value.toLocaleString();
  }

  formatPercent(value: number | null | undefined): string {
    if (value == null) return '-';
    return `${value.toFixed(1)}%`;
  }

  formatCurrency(value: number | null | undefined): string {
    if (value == null) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  }

  getSeverityColor(
    severity: string
  ):
    | 'success'
    | 'info'
    | 'warn'
    | 'danger'
    | 'secondary'
    | 'contrast'
    | undefined {
    const colors: {
      [key: string]: 'success' | 'info' | 'warn' | 'danger' | 'secondary';
    } = {
      info: 'info',
      low: 'success',
      medium: 'warn',
      high: 'danger',
      critical: 'danger',
    };
    return colors[severity] || 'secondary';
  }

  getTrendIcon(trend: string): string {
    switch (trend) {
      case 'increasing':
        return 'pi pi-arrow-up';
      case 'decreasing':
        return 'pi pi-arrow-down';
      default:
        return 'pi pi-minus';
    }
  }

  getTrendColor(trend: string): string {
    switch (trend) {
      case 'increasing':
        return 'text-green-500';
      case 'decreasing':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  }

  getRecommendationIcon(recommendation: string): string {
    return recommendation === 'increase_stock'
      ? 'pi pi-arrow-up-right'
      : 'pi pi-arrow-down-right';
  }

  getRecommendationColor(recommendation: string): string {
    return recommendation === 'increase_stock'
      ? 'text-green-600'
      : 'text-orange-600';
  }
}
