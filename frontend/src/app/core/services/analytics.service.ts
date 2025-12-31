import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, map, catchError, of } from 'rxjs';

// Interfaces for Supply Chain KPIs
export interface DailyShipment {
  day: string;
  count: number;
}

export interface SupplyChainKPIs {
  period_days: number;
  total_shipments: number;
  delivered_count: number;
  on_time_delivery_rate: number;
  late_delivery_rate: number;
  damage_rate: number;
  loss_rate: number;
  return_rate: number;
  in_transit_count: number;
  pending_count: number;
  average_delivery_days: number;
  temp_controlled_rate: number;
  special_handling_rate: number;
  daily_shipments: DailyShipment[];
}

// Interfaces for Batch Yield Analysis
export interface BatchStatusDistribution {
  status: string;
  count: number;
}

export interface BatchByProduct {
  product__name: string;
  product__gtin: string;
  batch_count: number;
  total_quantity: number;
  avg_quantity: number;
  qc_pass_count: number;
}

export interface WeeklyProduction {
  week: string;
  count: number;
  total_quantity: number;
}

export interface ExpiringBatch {
  product__name: string;
  lot_number: string;
  expiry_date: string;
  available_quantity: number;
}

export interface BatchYieldAnalysis {
  period_days: number;
  total_batches: number;
  active_batches: number;
  qc_pass_rate: number;
  expiry_rate: number;
  recall_rate: number;
  quarantined_count: number;
  total_produced: number;
  total_available: number;
  utilization_rate: number;
  average_shelf_life_days: number;
  status_distribution: BatchStatusDistribution[];
  by_product: BatchByProduct[];
  weekly_production: WeeklyProduction[];
  expiring_soon: ExpiringBatch[];
}

// Interfaces for Carrier Performance
export interface CarrierStats {
  carrier: string;
  carrier_name: string;
  total_shipments: number;
  delivered_count: number;
  on_time_rate: number;
  damage_rate: number;
  loss_rate: number;
  avg_delivery_days: number | null;
  total_cost: number;
  avg_cost: number;
}

export interface ServiceTypeStats {
  service_type: string;
  count: number;
  delivered: number;
  on_time_rate: number;
  avg_cost: number;
}

export interface CarrierPerformance {
  period_days: number;
  carrier_performance: CarrierStats[];
  service_type_stats: ServiceTypeStats[];
}

// Interfaces for Temperature Excursions
export interface SeverityCount {
  severity: string;
  count: number;
}

export interface EntityTypeCount {
  entity_type: string;
  count: number;
}

export interface DailyTrend {
  day: string;
  count: number;
}

export interface WeeklyTrend {
  week: string;
  count: number;
}

export interface LocationCount {
  location: string;
  count: number;
}

export interface TempRequirementCount {
  temperature_requirement: string;
  count: number;
}

export interface RecentExcursion {
  id: number;
  entity_type: string;
  entity_id: number;
  severity: string;
  description: string;
  timestamp: string;
  location: string;
}

export interface TemperatureExcursions {
  period_days: number;
  total_excursions: number;
  excursion_rate: number;
  by_severity: SeverityCount[];
  by_entity_type: EntityTypeCount[];
  by_temperature_requirement: TempRequirementCount[];
  by_location: LocationCount[];
  daily_trend: DailyTrend[];
  weekly_trend: WeeklyTrend[];
  recent_excursions: RecentExcursion[];
}

// Interfaces for Demand Forecasting
export interface WeeklyForecast {
  week: string;
  predicted_demand: number;
}

export interface HistoricalDataPoint {
  week: string;
  demand: number;
}

export interface ProductForecast {
  product_id: number;
  product_name: string;
  product_gtin: string;
  historical_weekly_avg: number;
  avg_weekly_forecast: number;
  total_forecast: number;
  demand_trend: 'increasing' | 'decreasing' | 'stable';
  trend_value: number;
  demand_change_pct: number;
  weekly_forecasts: WeeklyForecast[];
  historical_data: HistoricalDataPoint[];
}

export interface InventoryRecommendation {
  product: string;
  recommendation: 'increase_stock' | 'reduce_stock';
  reason: string;
  suggested_increase_pct?: number;
  suggested_reduction_pct?: number;
}

export interface DemandForecast {
  forecast_period_days: number;
  history_period_days: number;
  total_products_analyzed: number;
  total_historical_demand: number;
  avg_weekly_demand: number;
  product_forecasts: ProductForecast[];
  inventory_recommendations: InventoryRecommendation[];
}

// Interface for Analytics Summary
export interface AnalyticsKPIs {
  total_shipments: number;
  on_time_delivery_rate: number;
  damage_rate: number;
  total_batches: number;
  qc_pass_rate: number;
  total_packs: number;
  temperature_excursions: number;
  total_events: number;
}

export interface StatusDistribution {
  status: string;
  count: number;
}

export interface TopCarrier {
  carrier: string;
  count: number;
}

export interface AnalyticsSummary {
  period_days: number;
  kpis: AnalyticsKPIs;
  shipment_status_distribution: StatusDistribution[];
  top_carriers: TopCarrier[];
}

@Injectable({
  providedIn: 'root',
})
export class AnalyticsService {
  private readonly http = inject(HttpClient);
  private readonly API_URL = '/api/analytics';

  // Loading states
  readonly loadingSummary = signal(false);
  readonly loadingKPIs = signal(false);
  readonly loadingBatchYield = signal(false);
  readonly loadingCarrierPerformance = signal(false);
  readonly loadingTemperatureExcursions = signal(false);
  readonly loadingDemandForecast = signal(false);

  // Data signals
  readonly summary = signal<AnalyticsSummary | null>(null);
  readonly kpis = signal<SupplyChainKPIs | null>(null);
  readonly batchYield = signal<BatchYieldAnalysis | null>(null);
  readonly carrierPerformance = signal<CarrierPerformance | null>(null);
  readonly temperatureExcursions = signal<TemperatureExcursions | null>(null);
  readonly demandForecast = signal<DemandForecast | null>(null);

  // Error signals
  readonly error = signal<string | null>(null);

  /**
   * Get analytics summary for dashboard overview
   */
  getSummary(days: number = 30): Observable<AnalyticsSummary> {
    this.loadingSummary.set(true);
    this.error.set(null);

    const params = new HttpParams().set('days', days.toString());

    return this.http
      .get<AnalyticsSummary>(`${this.API_URL}/summary/`, { params })
      .pipe(
        tap((data) => {
          this.summary.set(data);
          this.loadingSummary.set(false);
        }),
        catchError((err) => {
          this.loadingSummary.set(false);
          this.error.set('Failed to load analytics summary');
          throw err;
        })
      );
  }

  /**
   * Get supply chain KPIs
   */
  getKPIs(days: number = 30): Observable<SupplyChainKPIs> {
    this.loadingKPIs.set(true);
    this.error.set(null);

    const params = new HttpParams().set('days', days.toString());

    return this.http
      .get<SupplyChainKPIs>(`${this.API_URL}/kpis/`, { params })
      .pipe(
        tap((data) => {
          this.kpis.set(data);
          this.loadingKPIs.set(false);
        }),
        catchError((err) => {
          this.loadingKPIs.set(false);
          this.error.set('Failed to load KPIs');
          throw err;
        })
      );
  }

  /**
   * Get batch yield analysis
   */
  getBatchYieldAnalysis(days: number = 90): Observable<BatchYieldAnalysis> {
    this.loadingBatchYield.set(true);
    this.error.set(null);

    const params = new HttpParams().set('days', days.toString());

    return this.http
      .get<BatchYieldAnalysis>(`${this.API_URL}/batch-yield/`, { params })
      .pipe(
        tap((data) => {
          this.batchYield.set(data);
          this.loadingBatchYield.set(false);
        }),
        catchError((err) => {
          this.loadingBatchYield.set(false);
          this.error.set('Failed to load batch yield analysis');
          throw err;
        })
      );
  }

  /**
   * Get carrier performance metrics
   */
  getCarrierPerformance(days: number = 90): Observable<CarrierPerformance> {
    this.loadingCarrierPerformance.set(true);
    this.error.set(null);

    const params = new HttpParams().set('days', days.toString());

    return this.http
      .get<CarrierPerformance>(`${this.API_URL}/carrier-performance/`, {
        params,
      })
      .pipe(
        tap((data) => {
          this.carrierPerformance.set(data);
          this.loadingCarrierPerformance.set(false);
        }),
        catchError((err) => {
          this.loadingCarrierPerformance.set(false);
          this.error.set('Failed to load carrier performance');
          throw err;
        })
      );
  }

  /**
   * Get temperature excursion trends
   */
  getTemperatureExcursions(
    days: number = 90
  ): Observable<TemperatureExcursions> {
    this.loadingTemperatureExcursions.set(true);
    this.error.set(null);

    const params = new HttpParams().set('days', days.toString());

    return this.http
      .get<TemperatureExcursions>(`${this.API_URL}/temperature-excursions/`, {
        params,
      })
      .pipe(
        tap((data) => {
          this.temperatureExcursions.set(data);
          this.loadingTemperatureExcursions.set(false);
        }),
        catchError((err) => {
          this.loadingTemperatureExcursions.set(false);
          this.error.set('Failed to load temperature excursions');
          throw err;
        })
      );
  }

  /**
   * Get demand forecasting data
   */
  getDemandForecast(
    forecastDays: number = 30,
    historyDays: number = 180
  ): Observable<DemandForecast> {
    this.loadingDemandForecast.set(true);
    this.error.set(null);

    const params = new HttpParams()
      .set('forecast_days', forecastDays.toString())
      .set('history_days', historyDays.toString());

    return this.http
      .get<DemandForecast>(`${this.API_URL}/demand-forecast/`, { params })
      .pipe(
        tap((data) => {
          this.demandForecast.set(data);
          this.loadingDemandForecast.set(false);
        }),
        catchError((err) => {
          this.loadingDemandForecast.set(false);
          this.error.set('Failed to load demand forecast');
          throw err;
        })
      );
  }

  /**
   * Load all analytics data at once
   */
  loadAllAnalytics(days: number = 30): void {
    this.getSummary(days).subscribe();
    this.getKPIs(days).subscribe();
    this.getBatchYieldAnalysis(days).subscribe();
    this.getCarrierPerformance(days).subscribe();
    this.getTemperatureExcursions(days).subscribe();
    this.getDemandForecast(30, days * 6).subscribe();
  }

  /**
   * Clear all cached analytics data
   */
  clearAnalytics(): void {
    this.summary.set(null);
    this.kpis.set(null);
    this.batchYield.set(null);
    this.carrierPerformance.set(null);
    this.temperatureExcursions.set(null);
    this.demandForecast.set(null);
    this.error.set(null);
  }

  /**
   * Check if any data is loading
   */
  isLoading(): boolean {
    return (
      this.loadingSummary() ||
      this.loadingKPIs() ||
      this.loadingBatchYield() ||
      this.loadingCarrierPerformance() ||
      this.loadingTemperatureExcursions() ||
      this.loadingDemandForecast()
    );
  }
}
