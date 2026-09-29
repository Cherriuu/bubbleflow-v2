from django.db import transaction
from django.db.models import Sum
from ..models import Batch, BatchStatus, InventoryEvent, EventType, PreparedItem


# Create a batch and record its starting inventory
@transaction.atomic
def create_batch(prepared_item, storage_location, quantity, started_at):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    if storage_location.shop != prepared_item.shop:
        raise ValueError(
            "Storage location and prepared item must belong to the same shop."
        )

    expires_at = started_at + prepared_item.default_shelf_life

    batch = Batch.objects.create(
        prepared_item=prepared_item,
        storage_location=storage_location,
        status=BatchStatus.PREPARING,
        started_at=started_at,
        expires_at=expires_at
    )

    InventoryEvent.objects.create(
        batch=batch,
        event_type=EventType.BATCH_CREATED,
        quantity_delta=quantity
    )

    return batch


# Calculate the remaining inventory in one batch
def get_batch_balance(batch):
    return batch.inventory_events.aggregate(
        total=Sum("quantity_delta")
    )["total"] or 0


# Calculate available inventory across all ready batches
def get_item_inventory(prepared_item):
    batches = Batch.objects.filter(
        prepared_item=prepared_item,
        status=BatchStatus.READY
    )

    total_inventory = 0

    for batch in batches:
        total_inventory += get_batch_balance(batch)

    return total_inventory


# Remove wasted inventory from a batch
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
        reason=reason
    )

    return get_batch_balance(batch)


# Adjust inventory after a physical count
def record_correction(batch, quantity, reason):
    if quantity == 0:
        raise ValueError("Quantity must be non-zero.")

    InventoryEvent.objects.create(
        batch=batch,
        event_type=EventType.CORRECTION,
        quantity_delta=quantity,
        reason=reason
    )

    return get_batch_balance(batch)


# Expire a batch and remove its remaining inventory
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
            reason="Batch expired"
        )

    batch.status = BatchStatus.EXPIRED
    batch.save()

    return batch


# Consume inventory from the batches that expire first
@transaction.atomic
def consume_fefo(prepared_item, quantity):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    batches = Batch.objects.filter(
        prepared_item=prepared_item,
        status=BatchStatus.READY
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
                reason="Consumed for order"
            )

            # Mark batch depleted if nothing remains
            if quantity == batch_balance:
                batch.status = BatchStatus.DEPLETED
                batch.save()

            return

        InventoryEvent.objects.create(
            batch=batch,
            event_type=EventType.ORDER_CONSUMPTION,
            quantity_delta=-batch_balance,
            reason="Consumed for order"
        )

        batch.status = BatchStatus.DEPLETED
        batch.save()

        quantity -= batch_balance

    # Rolls back all consumption if there was not enough inventory
    raise ValueError("Insufficient inventory.")

def mark_batch_ready(batch, ready_at):
    if batch.status != BatchStatus.PREPARING:
        raise ValueError(
            "Only preparing batches can be marked ready."
        )

    batch.status = BatchStatus.READY
    batch.ready_at = ready_at
    batch.save()

    return batch

def inventory_summary_view():
    prepared_items = PreparedItem.objects.all()
    summary =[]

    for item in prepared_items:
        quantity = get_item_inventory(item)
        id = item.id
        name = item.name
        unit = item.unit

        
        summary.append({
            "id": id,
            "name": name,
            "quantity": quantity,
            "unit": unit
        })

    return summary
