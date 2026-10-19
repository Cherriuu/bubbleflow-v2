# Forecasting v2: predicts when each prepared item runs out and when the next batch must start.
# The math uses plain lists and numbers so it can be tested without a database; get_item_forecast loads the real data.
from datetime import timedelta
from decimal import Decimal
from math import ceil, floor
from zoneinfo import ZoneInfo

from ..models import Batch, BatchStatus, EventType, InventoryEvent
from .inventory import get_batch_balance


# A slot is a 15-minute block of time. Slot 0 starts now, slot 1 starts 15 minutes from now, and so on.
SLOT_MINUTES = 15
SLOTS_PER_HOUR = 60 // SLOT_MINUTES
SLOT = timedelta(minutes=SLOT_MINUTES)

# How far ahead to forecast: 8 hours
HORIZON_SLOTS = 8 * SLOTS_PER_HOUR

HISTORY_DAYS = 14
MIN_HISTORY_DAYS = 3
FLAT_RATE_HOURS = 4

MIN_TODAY_FACTOR = Decimal("0.5")
MAX_TODAY_FACTOR = Decimal("2.0")

START_SOON_WINDOW = timedelta(minutes=20)

HALF_BATCH = Decimal("0.5")
FULL_BATCH = Decimal("1")

# Most urgent first, used to sort the forecast list
STATUS_ORDER = ["late", "start_soon", "on_track", "no_runout"]


# Get the average quantity consumed in each hour of the day (0-23) over a number of days
def hourly_profile(events, days):
    totals = [Decimal("0")] * 24

    for local_datetime, quantity in events:
        totals[local_datetime.hour] += Decimal(quantity)

    if days <= 0:
        return totals

    return [total / Decimal(days) for total in totals]


# Compare today's sales so far with a normal day, to scale the rest of today's forecast up or down
def today_factor(actual_so_far, expected_so_far, minimum_expected=Decimal("1")):
    # Early in the day there's too little expected demand for the comparison to mean anything
    if expected_so_far <= 0 or expected_so_far < minimum_expected:
        return Decimal("1")

    factor = Decimal(actual_so_far) / Decimal(expected_so_far)

    # Clamp so one unusual hour can't halve or more than double the forecast
    return max(MIN_TODAY_FACTOR, min(MAX_TODAY_FACTOR, factor))


# Get the expected demand for each slot, starting at a local time
def expected_demand(profile, start_local_datetime, num_slots, factor):
    demand = []

    for slot in range(num_slots):
        hour = (start_local_datetime + slot * SLOT).hour
        demand.append(profile[hour] / SLOTS_PER_HOUR * factor)

    return demand


# Walk through the slots using up stock, and find when it runs out and how much expires unused
# A lot is one batch's stock: (first slot it can be used, slot it expires, quantity)
def project_stock(lots, demand):
    remaining = [
        [available_from, expires_at, Decimal(quantity)]
        for available_from, expires_at, quantity in lots
    ]

    runout_slot = None
    expected_waste = Decimal("0")

    for slot, slot_demand in enumerate(demand):
        # Whatever is left in a lot when it expires is thrown away
        for lot in remaining:
            if lot[1] <= slot and lot[2] > 0:
                expected_waste += lot[2]
                lot[2] = Decimal("0")

        # Use the lot that expires first (FEFO), and only lots that are ready by this slot
        usable = sorted(
            (lot for lot in remaining if lot[0] <= slot and lot[2] > 0),
            key=lambda lot: lot[1]
        )

        needed = slot_demand

        for lot in usable:
            if needed <= 0:
                break

            used = min(needed, lot[2])
            lot[2] -= used
            needed -= used

        if needed > 0 and runout_slot is None:
            runout_slot = slot

    return runout_slot, expected_waste


# Work out when the next batch must start so it's ready before stock runs out
def start_by(runout_time, prep_time, cooling_time, now):
    if runout_time is None:
        return None, "no_runout"

    start_time = runout_time - prep_time - cooling_time

    if start_time <= now:
        return start_time, "late"

    if start_time - now <= START_SOON_WINDOW:
        return start_time, "start_soon"

    return start_time, "on_track"


# Pick a half batch if it covers demand for the rest of the forecast, otherwise a full batch
def recommend_batch_fraction(lots, demand, batch_quantity, ready_slot, shelf_life_slots):
    for fraction in [HALF_BATCH, FULL_BATCH]:
        new_lot = (
            ready_slot,
            ready_slot + shelf_life_slots,
            Decimal(batch_quantity) * fraction
        )

        runout_slot, expected_waste = project_stock(
            lots + [new_lot],
            demand
        )

        if runout_slot is None or fraction == FULL_BATCH:
            return fraction, expected_waste


# Get how many slots from now a time is, as a decimal number
def slots_from_now(time, now):
    return (time - now) / SLOT


# Get the forecast for a specific prepared item, using the shop's local time
def get_item_forecast(prepared_item, now):
    shop = prepared_item.shop
    shop_timezone = ZoneInfo(shop.timezone)
    local_now = now.astimezone(shop_timezone)
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Order consumption is stored as negative deltas, so flip the sign to get the quantity used
    events = [
        (created_at.astimezone(shop_timezone), -quantity_delta)
        for created_at, quantity_delta in InventoryEvent.objects.filter(
            batch__prepared_item=prepared_item,
            event_type=EventType.ORDER_CONSUMPTION,
            created_at__gte=now - timedelta(days=HISTORY_DAYS),
            created_at__lte=now,
        ).values_list("created_at", "quantity_delta")
    ]

    # Past full days build the profile; today's sales so far adjust it
    past_events = [event for event in events if event[0] < today_start]
    today_events = [event for event in events if event[0] >= today_start]

    days_with_history = len({local_datetime.date() for local_datetime, _ in past_events})

    if days_with_history >= MIN_HISTORY_DAYS:
        method = "hourly_profile"

        # Average over every day since the first sale, including quiet days with no sales
        first_day = min(local_datetime.date() for local_datetime, _ in past_events)
        window_days = (today_start.date() - first_day).days

        profile = hourly_profile(past_events, window_days)

        # Expected so far = full hours already passed, plus the part of the current hour
        expected_so_far = sum(profile[:local_now.hour], Decimal("0")) + (
            profile[local_now.hour] * Decimal(local_now.minute) / Decimal("60")
        )
        actual_so_far = sum((quantity for _, quantity in today_events), Decimal("0"))

        factor = today_factor(
            actual_so_far,
            expected_so_far,
            minimum_expected=prepared_item.quantity_per_serving
        )
    else:
        # Not enough history for a daily pattern, so spread the last 4 hours of usage evenly
        method = "flat_rate"

        recent_usage = sum(
            (
                quantity for local_datetime, quantity in events
                if local_datetime >= local_now - timedelta(hours=FLAT_RATE_HOURS)
            ),
            Decimal("0")
        )

        profile = [recent_usage / FLAT_RATE_HOURS] * 24
        factor = Decimal("1")

    # Plan for a bit more demand than expected, as a safety margin
    buffer_multiplier = Decimal("1") + shop.inventory_buffer_percent / Decimal("100")

    demand = expected_demand(
        profile,
        local_now,
        HORIZON_SLOTS,
        factor * buffer_multiplier
    )

    lots = []

    for batch in Batch.objects.filter(
        prepared_item=prepared_item,
        status__in=[BatchStatus.READY, BatchStatus.PREPARING, BatchStatus.COOLING],
        expires_at__gt=now,
    ):
        balance = get_batch_balance(batch)

        if balance <= 0:
            continue

        if batch.status == BatchStatus.READY:
            available_from = 0
        else:
            # A batch being made can be served once it's prepared and cooled
            ready_time = (batch.ready_at or now) + prepared_item.cooling_time
            available_from = max(0, ceil(slots_from_now(ready_time, now)))

        expires_at = max(0, floor(slots_from_now(batch.expires_at, now)))

        lots.append((available_from, expires_at, balance))

    runout_slot, expected_waste = project_stock(lots, demand)

    runout_at = None if runout_slot is None else now + runout_slot * SLOT

    start_time, status = start_by(
        runout_at,
        prepared_item.preparation_time,
        prepared_item.cooling_time,
        now
    )

    recommended_fraction = None

    if runout_at is not None:
        # If it's already too late, the new batch is ready as soon as it can be made
        ready_time = max(
            runout_at,
            now + prepared_item.preparation_time + prepared_item.cooling_time
        )

        recommended_fraction, expected_waste = recommend_batch_fraction(
            lots,
            demand,
            prepared_item.default_batch_quantity,
            ceil(slots_from_now(ready_time, now)),
            floor(prepared_item.default_shelf_life / SLOT)
        )

    return {
        "runout_at": runout_at,
        "start_by": start_time,
        "status": status,
        "recommended_batch_fraction": recommended_fraction,
        "expected_waste": expected_waste.quantize(Decimal("0.001")),
        "method": method,
    }
