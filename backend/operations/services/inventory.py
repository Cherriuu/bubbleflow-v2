from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from ..models import (
    Batch,
    BatchStatus,
    InventoryEvent,
    EventType,
    PreparedItem,
)


@transaction.atomic
def create_batch(prepared_item, storage_location, batch_fraction, started_at):
    if batch_fraction <= 0:
        raise ValueError("Batch fraction must be greater than zero.")

    if storage_location.shop != prepared_item.shop:
        raise ValueError(
            "Storage location and prepared item must belong to the same shop."
        )

    initial_quantity = prepared_item.default_batch_quantity * batch_fraction
    ready_at = started_at + prepared_item.preparation_time
    expires_at = ready_at + prepared_item.default_shelf_life

    batch = Batch.objects.create(
        prepared_item=prepared_item,
        storage_location=storage_location,
        initial_quantity=initial_quantity,
        status=BatchStatus.PREPARING,
        started_at=started_at,
        ready_at=ready_at,
        expires_at=expires_at,
    )

    InventoryEvent.objects.create(
        batch=batch,
        event_type=EventType.BATCH_CREATED,
        quantity_delta=initial_quantity,
    )

    return batch


def get_batch_balance(batch):
    return batch.inventory_events.aggregate(
        total=Sum("quantity_delta")
    )["total"] or Decimal("0")


def get_item_inventory(prepared_item):
    batches = Batch.objects.filter(
        prepared_item=prepared_item,
        status=BatchStatus.READY,
    )

    total_inventory = Decimal("0")

    for batch in batches:
        total_inventory += get_batch_balance(batch)

    return total_inventory


def get_estimated_servings(prepared_item):
    inventory = get_item_inventory(prepared_item)

    buffer_percent = prepared_item.shop.inventory_buffer_percent
    buffer_multiplier = Decimal("1") - (buffer_percent / Decimal("100"))

    usable_inventory = inventory * buffer_multiplier

    if prepared_item.quantity_per_serving <= 0:
        return 0

    return int(usable_inventory / prepared_item.quantity_per_serving)


def get_inventory_status(prepared_item):
    servings = get_estimated_servings(prepared_item)
    threshold = prepared_item.shop.low_stock_threshold_servings

    if servings == 0:
        return "out"

    if servings < threshold:
        return "low"

    return "available"


def record_waste(batch, quantity, reason):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    if quantity > get_batch_balance(batch):
        raise ValueError(
            "Cannot record waste greater than the available batch balance."
        )

    InventoryEvent.objects.create(
        batch=batch,
        event_type=EventType.WASTE,
        quantity_delta=-quantity,
        reason=reason,
    )

    return get_batch_balance(batch)


def record_correction(batch, quantity, reason):
    if quantity == 0:
        raise ValueError("Quantity must be non-zero.")

    InventoryEvent.objects.create(
        batch=batch,
        event_type=EventType.CORRECTION,
        quantity_delta=quantity,
        reason=reason,
    )

    return get_batch_balance(batch)


@transaction.atomic
def expire_batch(batch):
    if batch.status != BatchStatus.READY:
        raise ValueError("Only ready batches can be expired.")

    balance = get_batch_balance(batch)

    if balance > 0:
        InventoryEvent.objects.create(
            batch=batch,
            event_type=EventType.EXPIRY,
            quantity_delta=-balance,
            reason="Batch expired",
        )

    batch.status = BatchStatus.EXPIRED
    batch.save()

    return batch


@transaction.atomic
def consume_fefo(prepared_item, quantity):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    batches = Batch.objects.filter(
        prepared_item=prepared_item,
        status=BatchStatus.READY,
    ).order_by("expires_at")

    for batch in batches:
        batch_balance = get_batch_balance(batch)

        if batch_balance <= 0:
            continue

        if quantity <= batch_balance:
            InventoryEvent.objects.create(
                batch=batch,
                event_type=EventType.ORDER_CONSUMPTION,
                quantity_delta=-quantity,
                reason="Consumed for order",
            )

            if quantity == batch_balance:
                batch.status = BatchStatus.DEPLETED
                batch.save()

            return

        InventoryEvent.objects.create(
            batch=batch,
            event_type=EventType.ORDER_CONSUMPTION,
            quantity_delta=-batch_balance,
            reason="Consumed for order",
        )

        batch.status = BatchStatus.DEPLETED
        batch.save()

        quantity -= batch_balance

    raise ValueError("Insufficient inventory.")


def mark_batch_ready(batch):
    if batch.status not in [
        BatchStatus.PREPARING,
        BatchStatus.COOLING,
    ]:
        raise ValueError(
            "Only preparing or cooling batches can be marked ready."
        )

    batch.status = BatchStatus.READY
    batch.save()

    return batch


def inventory_summary_view():
    prepared_items = PreparedItem.objects.filter(is_active=True)
    summary = []

    for item in prepared_items:
        estimated_servings = get_estimated_servings(item)
        status = get_inventory_status(item)

        summary.append({
            "id": item.id,
            "name": item.name,
            "estimated_servings": estimated_servings,
            "status": status,
        })

    return summary