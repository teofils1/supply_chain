"""
Analytics views for supply chain KPIs, metrics, and predictive analytics.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import (
    Avg,
    Case,
    Count,
    F,
    FloatField,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import (
    Coalesce,
    ExtractMonth,
    ExtractWeek,
    ExtractYear,
    TruncDate,
    TruncMonth,
    TruncWeek,
)
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import models as m


class SupplyChainKPIsView(APIView):
    """
    Get supply chain KPIs including on-time delivery %, damage rate, etc.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get date range parameters
        days = int(request.query_params.get("days", 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Filter shipments within the date range
        shipments = m.Shipment.objects.filter(
            created_at__gte=start_date, created_at__lte=end_date
        )

        # Total shipments
        total_shipments = shipments.count()

        # Delivered shipments
        delivered_shipments = shipments.filter(status="delivered")
        delivered_count = delivered_shipments.count()

        # On-time delivery calculation
        # A shipment is on-time if actual_delivery_date <= estimated_delivery_date
        on_time_deliveries = delivered_shipments.filter(
            actual_delivery_date__isnull=False,
            estimated_delivery_date__isnull=False,
            actual_delivery_date__lte=F("estimated_delivery_date"),
        ).count()

        on_time_delivery_rate = (
            (on_time_deliveries / delivered_count * 100) if delivered_count > 0 else 0
        )

        # Late deliveries
        late_deliveries = delivered_shipments.filter(
            actual_delivery_date__isnull=False,
            estimated_delivery_date__isnull=False,
            actual_delivery_date__gt=F("estimated_delivery_date"),
        ).count()

        late_delivery_rate = (
            (late_deliveries / delivered_count * 100) if delivered_count > 0 else 0
        )

        # Damage rate
        damaged_shipments = shipments.filter(status="damaged").count()
        damage_rate = (
            (damaged_shipments / total_shipments * 100) if total_shipments > 0 else 0
        )

        # Lost shipments
        lost_shipments = shipments.filter(status="lost").count()
        loss_rate = (
            (lost_shipments / total_shipments * 100) if total_shipments > 0 else 0
        )

        # Return rate
        returned_shipments = shipments.filter(status="returned").count()
        return_rate = (
            (returned_shipments / total_shipments * 100) if total_shipments > 0 else 0
        )

        # In-transit shipments
        in_transit_shipments = shipments.filter(
            status__in=["picked_up", "in_transit", "out_for_delivery"]
        ).count()

        # Pending shipments
        pending_shipments = shipments.filter(
            status__in=["pending", "confirmed"]
        ).count()

        # Average delivery time (in days)
        avg_delivery_time = delivered_shipments.filter(
            actual_delivery_date__isnull=False, shipped_date__isnull=False
        ).annotate(
            delivery_days=F("actual_delivery_date") - F("shipped_date")
        )

        # Calculate average in Python since Django doesn't handle timedelta well
        delivery_times = []
        for s in avg_delivery_time:
            if s.delivery_days:
                delivery_times.append(s.delivery_days.days)
        avg_delivery_days = (
            sum(delivery_times) / len(delivery_times) if delivery_times else 0
        )

        # Temperature-controlled shipments
        temp_controlled = shipments.exclude(temperature_requirement="ambient").count()
        temp_controlled_rate = (
            (temp_controlled / total_shipments * 100) if total_shipments > 0 else 0
        )

        # Special handling required
        special_handling = shipments.filter(special_handling_required=True).count()
        special_handling_rate = (
            (special_handling / total_shipments * 100) if total_shipments > 0 else 0
        )

        # Shipment volume trends (last 7 days)
        seven_days_ago = end_date - timedelta(days=7)
        daily_shipments = (
            shipments.filter(created_at__gte=seven_days_ago)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        return Response(
            {
                "period_days": days,
                "total_shipments": total_shipments,
                "delivered_count": delivered_count,
                "on_time_delivery_rate": round(on_time_delivery_rate, 2),
                "late_delivery_rate": round(late_delivery_rate, 2),
                "damage_rate": round(damage_rate, 2),
                "loss_rate": round(loss_rate, 2),
                "return_rate": round(return_rate, 2),
                "in_transit_count": in_transit_shipments,
                "pending_count": pending_shipments,
                "average_delivery_days": round(avg_delivery_days, 1),
                "temp_controlled_rate": round(temp_controlled_rate, 2),
                "special_handling_rate": round(special_handling_rate, 2),
                "daily_shipments": list(daily_shipments),
            }
        )


class BatchYieldAnalysisView(APIView):
    """
    Analyze batch yields, quality control metrics, and production efficiency.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get date range parameters
        days = int(request.query_params.get("days", 90))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Filter batches within date range
        batches = m.Batch.objects.filter(
            created_at__gte=start_date, created_at__lte=end_date
        ).select_related("product")

        total_batches = batches.count()

        # Quality control pass rate
        qc_passed = batches.filter(quality_control_passed=True).count()
        qc_pass_rate = (qc_passed / total_batches * 100) if total_batches > 0 else 0

        # Batches by status
        status_distribution = (
            batches.values("status")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Active batches (not expired, recalled, or destroyed)
        active_batches = batches.filter(
            status__in=["active", "released"]
        ).count()

        # Expired batches
        expired_batches = batches.filter(status="expired").count()
        expiry_rate = (
            (expired_batches / total_batches * 100) if total_batches > 0 else 0
        )

        # Recalled batches
        recalled_batches = batches.filter(status="recalled").count()
        recall_rate = (
            (recalled_batches / total_batches * 100) if total_batches > 0 else 0
        )

        # Quarantined batches
        quarantined_batches = batches.filter(status="quarantined").count()

        # Yield analysis (available vs produced)
        yield_data = batches.aggregate(
            total_produced=Coalesce(Sum("quantity_produced"), 0),
            total_available=Coalesce(Sum("available_quantity"), 0),
        )

        total_produced = yield_data["total_produced"]
        total_available = yield_data["total_available"]
        utilization_rate = (
            ((total_produced - total_available) / total_produced * 100)
            if total_produced > 0
            else 0
        )

        # Batches by product
        by_product = (
            batches.values("product__name", "product__gtin")
            .annotate(
                batch_count=Count("id"),
                total_quantity=Sum("quantity_produced"),
                avg_quantity=Avg("quantity_produced"),
                qc_pass_count=Count("id", filter=Q(quality_control_passed=True)),
            )
            .order_by("-batch_count")[:10]
        )

        # Batch production trends (weekly)
        weekly_production = (
            batches.annotate(week=TruncWeek("manufacturing_date"))
            .values("week")
            .annotate(
                count=Count("id"),
                total_quantity=Sum("quantity_produced"),
            )
            .order_by("week")
        )

        # Batches expiring soon (next 30 days)
        today = date.today()
        thirty_days = today + timedelta(days=30)
        expiring_soon = (
            batches.filter(
                expiry_date__gte=today,
                expiry_date__lte=thirty_days,
                status__in=["active", "released"],
            )
            .values("product__name", "lot_number", "expiry_date", "available_quantity")
            .order_by("expiry_date")[:10]
        )

        # Average shelf life (manufacturing to expiry)
        avg_shelf_life = batches.annotate(
            shelf_life_days=F("expiry_date") - F("manufacturing_date")
        )
        shelf_lives = []
        for b in avg_shelf_life:
            if b.shelf_life_days:
                shelf_lives.append(b.shelf_life_days.days)
        avg_shelf_life_days = sum(shelf_lives) / len(shelf_lives) if shelf_lives else 0

        return Response(
            {
                "period_days": days,
                "total_batches": total_batches,
                "active_batches": active_batches,
                "qc_pass_rate": round(qc_pass_rate, 2),
                "expiry_rate": round(expiry_rate, 2),
                "recall_rate": round(recall_rate, 2),
                "quarantined_count": quarantined_batches,
                "total_produced": total_produced,
                "total_available": total_available,
                "utilization_rate": round(utilization_rate, 2),
                "average_shelf_life_days": round(avg_shelf_life_days, 0),
                "status_distribution": list(status_distribution),
                "by_product": list(by_product),
                "weekly_production": list(weekly_production),
                "expiring_soon": list(expiring_soon),
            }
        )


class CarrierPerformanceView(APIView):
    """
    Analyze carrier performance metrics.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get date range parameters
        days = int(request.query_params.get("days", 90))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Filter shipments within date range
        shipments = m.Shipment.objects.filter(
            created_at__gte=start_date, created_at__lte=end_date
        )

        # Performance by carrier
        carrier_stats = []
        carriers = dict(m.Shipment.CARRIER_CHOICES)

        for carrier_code, carrier_name in carriers.items():
            carrier_shipments = shipments.filter(carrier=carrier_code)
            total = carrier_shipments.count()

            if total == 0:
                continue

            delivered = carrier_shipments.filter(status="delivered")
            delivered_count = delivered.count()

            # On-time deliveries
            on_time = delivered.filter(
                actual_delivery_date__isnull=False,
                estimated_delivery_date__isnull=False,
                actual_delivery_date__lte=F("estimated_delivery_date"),
            ).count()

            on_time_rate = (on_time / delivered_count * 100) if delivered_count > 0 else 0

            # Damage rate
            damaged = carrier_shipments.filter(status="damaged").count()
            damage_rate = (damaged / total * 100) if total > 0 else 0

            # Lost rate
            lost = carrier_shipments.filter(status="lost").count()
            loss_rate = (lost / total * 100) if total > 0 else 0

            # Average delivery time
            delivery_times = []
            for s in delivered.filter(
                actual_delivery_date__isnull=False, shipped_date__isnull=False
            ):
                if s.actual_delivery_date and s.shipped_date:
                    diff = s.actual_delivery_date - s.shipped_date
                    delivery_times.append(diff.days)

            avg_delivery_days = (
                sum(delivery_times) / len(delivery_times) if delivery_times else None
            )

            # Total shipping cost
            total_cost = carrier_shipments.aggregate(
                total=Coalesce(Sum("shipping_cost"), Decimal("0"))
            )["total"]

            avg_cost = carrier_shipments.aggregate(
                avg=Coalesce(Avg("shipping_cost"), Decimal("0"))
            )["avg"]

            carrier_stats.append(
                {
                    "carrier": carrier_code,
                    "carrier_name": carrier_name,
                    "total_shipments": total,
                    "delivered_count": delivered_count,
                    "on_time_rate": round(on_time_rate, 2),
                    "damage_rate": round(damage_rate, 2),
                    "loss_rate": round(loss_rate, 2),
                    "avg_delivery_days": (
                        round(avg_delivery_days, 1) if avg_delivery_days else None
                    ),
                    "total_cost": float(total_cost),
                    "avg_cost": float(avg_cost),
                }
            )

        # Sort by total shipments
        carrier_stats.sort(key=lambda x: x["total_shipments"], reverse=True)

        # Service type analysis
        service_stats = (
            shipments.values("service_type")
            .annotate(
                count=Count("id"),
                delivered=Count("id", filter=Q(status="delivered")),
                on_time=Count(
                    "id",
                    filter=Q(
                        status="delivered",
                        actual_delivery_date__isnull=False,
                        estimated_delivery_date__isnull=False,
                        actual_delivery_date__lte=F("estimated_delivery_date"),
                    ),
                ),
                avg_cost=Avg("shipping_cost"),
            )
            .order_by("-count")
        )

        # Calculate on-time rate for each service type
        service_stats_list = []
        for stat in service_stats:
            on_time_rate = (
                (stat["on_time"] / stat["delivered"] * 100)
                if stat["delivered"] > 0
                else 0
            )
            service_stats_list.append(
                {
                    "service_type": stat["service_type"],
                    "count": stat["count"],
                    "delivered": stat["delivered"],
                    "on_time_rate": round(on_time_rate, 2),
                    "avg_cost": float(stat["avg_cost"]) if stat["avg_cost"] else 0,
                }
            )

        return Response(
            {
                "period_days": days,
                "carrier_performance": carrier_stats,
                "service_type_stats": service_stats_list,
            }
        )


class TemperatureExcursionTrendsView(APIView):
    """
    Analyze temperature excursion events and trends.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get date range parameters
        days = int(request.query_params.get("days", 90))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get temperature-related events
        temp_events = m.Event.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            event_type="temperature_alert",
        )

        total_excursions = temp_events.count()

        # Excursions by severity
        by_severity = (
            temp_events.values("severity")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Excursions by entity type
        by_entity = (
            temp_events.values("entity_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Daily excursion trend
        daily_trend = (
            temp_events.annotate(day=TruncDate("timestamp"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        # Weekly excursion trend
        weekly_trend = (
            temp_events.annotate(week=TruncWeek("timestamp"))
            .values("week")
            .annotate(count=Count("id"))
            .order_by("week")
        )

        # Get shipments with temperature requirements that had excursions
        shipment_excursions = temp_events.filter(entity_type="shipment")
        affected_shipment_ids = shipment_excursions.values_list(
            "entity_id", flat=True
        ).distinct()

        # Temperature requirement distribution of affected shipments
        affected_shipments = m.Shipment.objects.filter(id__in=affected_shipment_ids)
        by_temp_requirement = (
            affected_shipments.values("temperature_requirement")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Recent excursions (last 10)
        recent_excursions = (
            temp_events.values(
                "id",
                "entity_type",
                "entity_id",
                "severity",
                "description",
                "timestamp",
                "location",
            )
            .order_by("-timestamp")[:10]
        )

        # Excursions by location
        by_location = (
            temp_events.exclude(location__isnull=True)
            .exclude(location="")
            .values("location")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Calculate excursion rate per shipment
        total_temp_shipments = m.Shipment.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
        ).exclude(temperature_requirement="ambient").count()

        excursion_rate = (
            (len(affected_shipment_ids) / total_temp_shipments * 100)
            if total_temp_shipments > 0
            else 0
        )

        return Response(
            {
                "period_days": days,
                "total_excursions": total_excursions,
                "excursion_rate": round(excursion_rate, 2),
                "by_severity": list(by_severity),
                "by_entity_type": list(by_entity),
                "by_temperature_requirement": list(by_temp_requirement),
                "by_location": list(by_location),
                "daily_trend": list(daily_trend),
                "weekly_trend": list(weekly_trend),
                "recent_excursions": list(recent_excursions),
            }
        )


class DemandForecastingView(APIView):
    """
    Predictive analytics for demand forecasting based on historical data.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get parameters
        forecast_days = int(request.query_params.get("forecast_days", 30))
        history_days = int(request.query_params.get("history_days", 180))

        end_date = timezone.now()
        start_date = end_date - timedelta(days=history_days)

        # Historical shipment data by product
        shipment_packs = m.ShipmentPack.objects.filter(
            shipment__created_at__gte=start_date,
            shipment__created_at__lte=end_date,
        ).select_related("pack__batch__product", "shipment")

        # Aggregate demand by product and week
        product_demand = defaultdict(lambda: defaultdict(int))
        product_info = {}

        for sp in shipment_packs:
            product = sp.pack.batch.product
            week_start = sp.shipment.created_at.date() - timedelta(
                days=sp.shipment.created_at.weekday()
            )
            product_demand[product.id][week_start] += sp.quantity_shipped
            product_info[product.id] = {
                "name": product.name,
                "gtin": product.gtin,
            }

        # Calculate forecasts for each product
        forecasts = []
        for product_id, weekly_demand in product_demand.items():
            weeks = sorted(weekly_demand.keys())
            demands = [weekly_demand[w] for w in weeks]

            if len(demands) < 4:
                # Not enough data for forecasting
                continue

            # Simple moving average forecast
            window_size = min(4, len(demands))
            recent_avg = sum(demands[-window_size:]) / window_size

            # Calculate trend (simple linear regression)
            n = len(demands)
            if n >= 2:
                x_mean = (n - 1) / 2
                y_mean = sum(demands) / n
                numerator = sum((i - x_mean) * (d - y_mean) for i, d in enumerate(demands))
                denominator = sum((i - x_mean) ** 2 for i in range(n))
                trend = numerator / denominator if denominator != 0 else 0
            else:
                trend = 0

            # Calculate seasonality (if we have enough data)
            seasonality_factor = 1.0
            if len(demands) >= 12:
                # Compare current period to same period last quarter
                current_quarter_avg = sum(demands[-4:]) / 4
                prev_quarter_avg = sum(demands[-8:-4]) / 4 if len(demands) >= 8 else current_quarter_avg
                if prev_quarter_avg > 0:
                    seasonality_factor = current_quarter_avg / prev_quarter_avg

            # Generate forecast for future weeks
            forecast_weeks = forecast_days // 7
            weekly_forecasts = []
            for i in range(1, forecast_weeks + 1):
                # Combine moving average, trend, and seasonality
                forecast_value = max(0, (recent_avg + trend * i) * seasonality_factor)
                week_date = end_date.date() + timedelta(weeks=i)
                weekly_forecasts.append(
                    {
                        "week": week_date.isoformat(),
                        "predicted_demand": round(forecast_value, 0),
                    }
                )

            # Calculate forecast summary
            total_forecast = sum(f["predicted_demand"] for f in weekly_forecasts)
            avg_weekly_forecast = total_forecast / len(weekly_forecasts) if weekly_forecasts else 0

            # Historical comparison
            historical_weekly_avg = sum(demands) / len(demands)
            demand_change_pct = (
                ((avg_weekly_forecast - historical_weekly_avg) / historical_weekly_avg * 100)
                if historical_weekly_avg > 0
                else 0
            )

            forecasts.append(
                {
                    "product_id": product_id,
                    "product_name": product_info[product_id]["name"],
                    "product_gtin": product_info[product_id]["gtin"],
                    "historical_weekly_avg": round(historical_weekly_avg, 0),
                    "avg_weekly_forecast": round(avg_weekly_forecast, 0),
                    "total_forecast": round(total_forecast, 0),
                    "demand_trend": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable",
                    "trend_value": round(trend, 2),
                    "demand_change_pct": round(demand_change_pct, 2),
                    "weekly_forecasts": weekly_forecasts,
                    "historical_data": [
                        {"week": w.isoformat(), "demand": d}
                        for w, d in zip(weeks, demands)
                    ],
                }
            )

        # Sort by average forecast demand
        forecasts.sort(key=lambda x: x["avg_weekly_forecast"], reverse=True)

        # Overall demand trend
        total_historical = sum(
            sum(weekly_demand.values()) for weekly_demand in product_demand.values()
        )
        weeks_in_history = history_days // 7

        # Inventory recommendations
        inventory_recommendations = []
        for forecast in forecasts[:10]:
            if forecast["demand_trend"] == "increasing" and forecast["demand_change_pct"] > 10:
                inventory_recommendations.append(
                    {
                        "product": forecast["product_name"],
                        "recommendation": "increase_stock",
                        "reason": f"Demand increasing by {forecast['demand_change_pct']}%",
                        "suggested_increase_pct": min(50, forecast["demand_change_pct"]),
                    }
                )
            elif forecast["demand_trend"] == "decreasing" and forecast["demand_change_pct"] < -10:
                inventory_recommendations.append(
                    {
                        "product": forecast["product_name"],
                        "recommendation": "reduce_stock",
                        "reason": f"Demand decreasing by {abs(forecast['demand_change_pct'])}%",
                        "suggested_reduction_pct": min(30, abs(forecast["demand_change_pct"])),
                    }
                )

        return Response(
            {
                "forecast_period_days": forecast_days,
                "history_period_days": history_days,
                "total_products_analyzed": len(forecasts),
                "total_historical_demand": total_historical,
                "avg_weekly_demand": round(total_historical / weeks_in_history, 0) if weeks_in_history > 0 else 0,
                "product_forecasts": forecasts[:20],  # Top 20 products
                "inventory_recommendations": inventory_recommendations,
            }
        )


class AnalyticsSummaryView(APIView):
    """
    Get a summary of all analytics for dashboard overview.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Quick KPIs
        shipments = m.Shipment.objects.filter(
            created_at__gte=start_date, created_at__lte=end_date
        )
        batches = m.Batch.objects.filter(
            created_at__gte=start_date, created_at__lte=end_date
        )
        events = m.Event.objects.filter(
            created_at__gte=start_date, created_at__lte=end_date
        )
        packs = m.Pack.objects.filter(
            created_at__gte=start_date, created_at__lte=end_date
        )

        total_shipments = shipments.count()
        delivered = shipments.filter(status="delivered").count()

        on_time = shipments.filter(
            status="delivered",
            actual_delivery_date__isnull=False,
            estimated_delivery_date__isnull=False,
            actual_delivery_date__lte=F("estimated_delivery_date"),
        ).count()

        on_time_rate = (on_time / delivered * 100) if delivered > 0 else 0

        damaged = shipments.filter(status="damaged").count()
        damage_rate = (damaged / total_shipments * 100) if total_shipments > 0 else 0

        total_batches = batches.count()
        qc_passed = batches.filter(quality_control_passed=True).count()
        qc_rate = (qc_passed / total_batches * 100) if total_batches > 0 else 0

        temp_excursions = events.filter(event_type="temperature_alert").count()

        # Status distribution
        shipment_status = (
            shipments.values("status")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Top carriers
        top_carriers = (
            shipments.values("carrier")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        return Response(
            {
                "period_days": days,
                "kpis": {
                    "total_shipments": total_shipments,
                    "on_time_delivery_rate": round(on_time_rate, 2),
                    "damage_rate": round(damage_rate, 2),
                    "total_batches": total_batches,
                    "qc_pass_rate": round(qc_rate, 2),
                    "total_packs": packs.count(),
                    "temperature_excursions": temp_excursions,
                    "total_events": events.count(),
                },
                "shipment_status_distribution": list(shipment_status),
                "top_carriers": list(top_carriers),
            }
        )
