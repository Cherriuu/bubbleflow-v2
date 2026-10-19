# my old forecasting system, only works with 4 hours of history, and doesn't account for incoming inventory. Keeping it around for now in case we want to use it as a backup.
from decimal import Decimal
from datetime import timedelta

from django.utils import timezone
from django.db.models import Sum

from ..models import InventoryEvent, EventType
from .inventory import get_item_inventory, get_incoming_inventory


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


# Get the average usage during these same hours of the day over the past few days
def get_same_hours_usage(prepared_item, hours=2, days=7):
    now = timezone.now()
    total = Decimal("0")

    # Day 1 is this time yesterday, day 2 is this time two days ago, and so on
    for day in range(1, days + 1):
        start_time = now - timedelta(days=day)
        end_time = start_time + timedelta(hours=hours)

        usage = InventoryEvent.objects.filter(
            batch__prepared_item=prepared_item,
            event_type=EventType.ORDER_CONSUMPTION,
            created_at__gte=start_time,
            created_at__lt=end_time
        ).aggregate(
            total=Sum("quantity_delta")
        )["total"] or Decimal("0")

        total += abs(usage)

    return total / Decimal(str(days))


# Estimate usage for the next few hours from past days at the same time, or the recent rate if there's no history
def forecast_demand(prepared_item, forecast_hours=2, history_hours=4):
    expected_usage = get_same_hours_usage(
        prepared_item,
        forecast_hours
    )

    # No sales at these hours on past days, so fall back to how fast it's selling right now
    if expected_usage == 0:
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


# Recommend how much to prepare to cover the expected demand
def recommend_production(prepared_item, forecast_hours=2, history_hours=4):
    forecast = forecast_demand(
        prepared_item,
        forecast_hours,
        history_hours
    )

    current_inventory = get_item_inventory(prepared_item)
    incoming_inventory = get_incoming_inventory(prepared_item)

    total_supply = current_inventory + incoming_inventory

    # Bug fix
    # If we have no demand history, keep a baseline amount available.
    if forecast == 0:
        baseline = prepared_item.default_batch_quantity / Decimal("2")

        recommended_quantity = baseline - total_supply

        if recommended_quantity < 0:
            return Decimal("0")

        return recommended_quantity

    recommended_quantity = forecast - total_supply

    if recommended_quantity < 0:
        return Decimal("0")

    return recommended_quantity


# Get the latest time to start the next batch so it's ready before current inventory runs out
def get_start_by(prepared_item, forecast_hours=2):
    usage_per_hour = forecast_demand(
        prepared_item,
        forecast_hours
    ) / Decimal(str(forecast_hours))

    if usage_per_hour == 0:
        return None

    hours_left = get_item_inventory(prepared_item) / usage_per_hour

    return (
        timezone.now()
        + timedelta(hours=float(hours_left))
        - prepared_item.preparation_time
        - prepared_item.cooling_time
    )
