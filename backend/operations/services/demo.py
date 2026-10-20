# Keeps the demo shop usable: fresh stock for every ingredient and order history that reaches the present.
# Called by seed_demo at build time and by the demo login, since the site may go days between deploys.
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from ..management.demo_history import seed_order_history
from ..models import (
    BatchStatus,
    InventoryEvent,
    LocationType,
    PreparedItem,
    Shop,
    StorageLocation,
)
from .inventory import create_batch, mark_batch_ready


# Top up any ingredient that's below a full batch of ready stock, then catch the order history up to now.
# Returns the names of the items that got a new batch and how many past orders were added.
def refresh_demo_shop(shop):
    now = timezone.now()

    with transaction.atomic():
        # Lock the shop row so two demo logins at the same moment take turns.
        # The second one waits here, then sees the first one's new batches and history, so nothing is added twice.
        Shop.objects.select_for_update().get(pk=shop.pk)

        refrigerator, _ = StorageLocation.objects.get_or_create(
            shop=shop,
            name="Main Refrigerator",
            defaults={"location_type": LocationType.REFRIGERATOR},
        )

        # Toppings like tapioca stay at the prep station when the shop has one
        prep_station = (
            StorageLocation.objects.filter(shop=shop, name="Prep Station").first()
            or refrigerator
        )

        restocked = []

        for item in PreparedItem.objects.filter(shop=shop, is_active=True).order_by("id"):
            if get_ready_stock(item, now) >= item.default_batch_quantity:
                continue

            batch = create_batch(
                shop=shop,
                prepared_item=item,
                storage_location=prep_station if item.is_topping else refrigerator,
                batch_fraction=Decimal("1.0"),
                started_at=now - item.preparation_time,
            )

            mark_batch_ready(batch)
            restocked.append(item.name)

        added_orders = seed_order_history(shop, now, refrigerator, prep_station)

    return restocked, added_orders


# Get the total stock left in an item's ready batches that haven't expired
def get_ready_stock(prepared_item, now):
    total = InventoryEvent.objects.filter(
        batch__prepared_item=prepared_item,
        batch__status=BatchStatus.READY,
        batch__expires_at__gt=now,
    ).aggregate(
        total=Sum("quantity_delta")
    )["total"]

    return total or Decimal("0")
