from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from ..models import (
    Batch,
    BatchStatus,
    InventoryEvent,
    EventType,
    PreparedItem,
)

def update_batch_status(batch):
    now = timezone.now()

    if batch.status == BatchStatus.PREPARING:
        if now >= batch.ready_at:
            if batch.prepared_item.requires_cooling:
                batch.status = BatchStatus.COOLING
            else:
                batch.status = BatchStatus.READY

            batch.save()

    elif batch.status == BatchStatus.READY:
        if now >= batch.expires_at:
            expire_batch(batch)

# Transcation atomic ensures that all database operations within the function succeed or fail as a single unit, maintaining data integrity.
@transaction.atomic
def create_batch(prepared_item, storage_location, batch_fraction, started_at):
    if batch_fraction <= 0:
        raise ValueError("Batch fraction must be greater than zero.")

    if storage_location.shop != prepared_item.shop:
        raise ValueError(
            "Storage location and prepared item must belong to the same shop."
        )

    actual_preparation_time = (
        prepared_item.preparation_time * float(batch_fraction)
    )

    initial_quantity = (
        prepared_item.default_batch_quantity * batch_fraction
    )

    ready_at = started_at + actual_preparation_time
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

# Get the current balance of a batch by summing up all the quantity deltas from its inventory events. If there are no events, return 0.
# Aggregate is a Django ORM function that allows you to take a bunch of rows and perform a calculation on them, returning a single value.
def get_batch_balance(batch):
    result = batch.inventory_events.aggregate(total=Sum("quantity_delta"))

    total = result["total"]

    if total is None:
        return Decimal("0")

    return total

# Get the total available inventory for a specific prepared item
def get_item_inventory(prepared_item):
    total = InventoryEvent.objects.filter(
        batch__prepared_item=prepared_item,
        batch__status=BatchStatus.READY,
        batch__expires_at__gt=timezone.now(),
    ).aggregate(total=Sum("quantity_delta"))

    total_quantity = total["total"]

    if total_quantity is None:
        return Decimal("0")

    return total_quantity

# Get the total incoming inventory for a specific prepared item, which includes batches that are currently being prepared or cooling
def get_incoming_inventory(prepared_item):
    batches = Batch.objects.filter(
        prepared_item=prepared_item,
        status__in=[
            BatchStatus.PREPARING,
            BatchStatus.COOLING,
        ],
    )

    total_incoming = Decimal("0")

    for batch in batches:
        total_incoming += get_batch_balance(batch)

    return total_incoming

# Get the estimated number of servings available for a specific prepared item, taking into account the shop's inventory buffer percentage
def get_estimated_servings(prepared_item):
    inventory = get_item_inventory(prepared_item)

    buffer_percent = prepared_item.shop.inventory_buffer_percent
    buffer_multiplier = (
        Decimal("1") -
        (buffer_percent / Decimal("100"))
    )

    usable_inventory = inventory * buffer_multiplier

    if prepared_item.quantity_per_serving <= 0:
        return 0

    return int(usable_inventory / prepared_item.quantity_per_serving)

# Get the inventory status for a specific prepared item based on the estimated servings and the shop's low stock threshold
def get_inventory_status(prepared_item):
    servings = get_estimated_servings(prepared_item)
    threshold = prepared_item.shop.low_stock_threshold_servings

    if servings == 0:
        return "out"

    if servings < threshold:
        return "low"

    return "available"

# Lock available batches for a specific prepared item, ensuring that they are ready and not expired. The batches are ordered by experation date and ID to follow the FEFO (First Expired, First Out) principle. 
# The select_for_update() method is used to lock the selected rows for the duration of the transaction, preventing other transactions from modifying them until the current transaction is complete.
# Concurrent transactions that attempt to access the same rows will be blocked until the lock is released, ensuring data consistency and preventing race conditions.
def lock_available_batches(prepared_item):
    return list(
        Batch.objects.select_for_update()
        .filter(
            prepared_item=prepared_item,
            status=BatchStatus.READY,
            expires_at__gt=timezone.now(),
        )
        .order_by(
            "expires_at",
            "id",
        )
    )

# Get the total available inventory from a list of batches by summing up their balances
def get_inventory_from_batches(batches):
    total = Decimal("0")

    for batch in batches:
        total += get_batch_balance(batch)

    return total

# Consume a specific quantity from a list of batches, following the FEFO principle.
def consume_from_batches(batches, quantity):
    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    remaining = quantity

    for batch in batches:
        batch_balance = get_batch_balance(batch)

        if batch_balance <= 0:
            continue

        amount_to_consume = min(
            remaining,
            batch_balance
        )

        InventoryEvent.objects.create(
            batch=batch,
            event_type=EventType.ORDER_CONSUMPTION,
            quantity_delta=-amount_to_consume,
            reason="Consumed for order",
        )

        if amount_to_consume == batch_balance:
            batch.status = BatchStatus.DEPLETED
            batch.save()

        remaining -= amount_to_consume

        if remaining == 0:
            return

    raise ValueError("Insufficient inventory.")

# Record waste for a specific batch
@transaction.atomic
def record_waste(batch, quantity, reason):
    locked_batch = Batch.objects.select_for_update().get(
        id=batch.id
    )

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    balance = get_batch_balance(
        locked_batch
    )

    if quantity > balance:
        raise ValueError(
            "Cannot record waste greater than the available batch balance."
        )

    InventoryEvent.objects.create(
        batch=locked_batch,
        event_type=EventType.WASTE,
        quantity_delta=-quantity,
        reason=reason,
    )

    return get_batch_balance(
        locked_batch
    )

# Record a correction for a specific batch
@transaction.atomic
def record_correction(batch, quantity, reason):
    locked_batch = Batch.objects.select_for_update().get(
        id=batch.id
    )

    if quantity == 0:
        raise ValueError(
            "Quantity must be non-zero."
        )

    InventoryEvent.objects.create(
        batch=locked_batch,
        event_type=EventType.CORRECTION,
        quantity_delta=quantity,
        reason=reason,
    )

    return get_batch_balance(
        locked_batch
    )

# Mark a batch as expired.
@transaction.atomic
def expire_batch(batch):
    if batch.status != BatchStatus.READY:
        raise ValueError(
            "Only ready batches can be expired."
        )

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

# Consume inventory following the FEFO (First Expired, First Out) principle.
@transaction.atomic
def consume_fefo(prepared_item, quantity):
    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    batches = lock_available_batches(
        prepared_item
    )

    available = get_inventory_from_batches(
        batches
    )

    if available < quantity:
        raise ValueError(
            "Insufficient inventory."
        )

    consume_from_batches(
        batches,
        quantity
    )

# Mark a preparing batch as ready
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

# Get a summary of the inventory for all active prepared items, including their estimated servings and inventory status
def inventory_summary_view():
    prepared_items = PreparedItem.objects.filter(
        is_active=True
    )

    summary = []

    for item in prepared_items:
        estimated_servings = get_estimated_servings(
            item
        )

        status = get_inventory_status(
            item
        )

        summary.append({
            "id": item.id,
            "name": item.name,
            "estimated_servings": estimated_servings,
            "status": status,
        })

    return summary