from decimal import Decimal
from datetime import timedelta

from django.utils import timezone
from django.db.models import Sum

from ..models import InventoryEvent, EventType
from .inventory import get_item_inventory


def get_usage_history(prepared_item, hours=4):
    start_time = timezone.now() - timedelta(hours=hours)

    total = InventoryEvent.objects.filter(
        batch__prepared_item=prepared_item,
        event_type=EventType.ORDER_CONSUMPTION,
        created_at__gte=start_time
    ).aggregate(
        total=Sum("quantity_delta")
    )["total"] or Decimal("0")

    return abs(total)


def calculate_usage_rate(prepared_item, hours=4):
    usage = get_usage_history(prepared_item, hours)

    return usage / Decimal(str(hours))


def forecast_demand(prepared_item, forecast_hours=2, history_hours=4):
    usage_rate = calculate_usage_rate(
        prepared_item,
        history_hours
    )

    expected_usage = usage_rate * Decimal(str(forecast_hours))

    buffer_percent = prepared_item.shop.inventory_buffer_percent
    buffer_multiplier = Decimal("1") + (
        buffer_percent / Decimal("100")
    )

    return expected_usage * buffer_multiplier


def recommend_production(prepared_item, forecast_hours=2, history_hours=4):
    forecast = forecast_demand(
        prepared_item,
        forecast_hours,
        history_hours
    )

    current_inventory = get_item_inventory(prepared_item)

    recommended_quantity = forecast - current_inventory

    if recommended_quantity < 0:
        return Decimal("0")

    return recommended_quantity