from django.db import models
from decimal import Decimal

class Shop(models.Model):
    name = models.CharField(max_length=120)
    timezone = models.CharField(max_length=64, default="America/New_York")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class LocationType(models.TextChoices):
    REFRIGERATOR = "refrigerator", "Refrigerator" # key is saved in the database, value is human-readable
    FREEZER = "freezer", "Freezer"
    ROOM_TEMPERATURE = "room_temperature", "Room Temperature"
    PREP_STATION = "prep_station", "Prep Station"


class StorageLocation(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="storage_locations")
    name = models.CharField(max_length=120)
    location_type = models.CharField(max_length=30, choices=LocationType.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # shop and name should be unique together, so that a shop cannot have two storage locations with the same name
        constraints = [
            models.UniqueConstraint(
                fields=["shop", "name"], # name backfridge 1, backfridge 2...
                name="unique_storage_location_per_shop"
            )
        ]

    def __str__(self):
        return f"{self.shop} ({self.name})"


class Unit(models.TextChoices):
    MILLILITER = "ml", "Milliliter"
    GRAM = "g", "Gram"
    SERVING = "serving", "Serving"


class PreparedItem(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="prepared_items")
    name = models.CharField(max_length=120)
    unit = models.CharField(max_length=20, choices=Unit.choices)
    default_shelf_life = models.DurationField()
    default_batch_quantity = models.DecimalField(max_digits=12, decimal_places=3)
    usage_buffer_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["shop", "name"],
                name="unique_prepared_item_per_shop"
            )
        ]

    def __str__(self):
        return f"{self.shop} ({self.name})"


class BatchStatus(models.TextChoices):
    PREPARING = "preparing", "Preparing"
    COOLING = "cooling", "Cooling"
    READY = "ready", "Ready"
    DEPLETED = "depleted", "Depleted"
    EXPIRED = "expired", "Expired"
    DISCARDED = "discarded", "Discarded"


class Batch(models.Model):
    prepared_item = models.ForeignKey(PreparedItem, on_delete=models.PROTECT, related_name="batches")
    storage_location = models.ForeignKey(StorageLocation, on_delete=models.PROTECT, related_name="batches")
    status = models.CharField(max_length=20, choices=BatchStatus.choices, default=BatchStatus.PREPARING)
    started_at = models.DateTimeField()
    ready_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["prepared_item", "status", "expires_at"])
        ]

    def __str__(self):
        return f"{self.prepared_item.name} Batch #{self.pk}"


class EventType(models.TextChoices):
    BATCH_CREATED = "batch_created", "Batch Created"
    ORDER_CONSUMPTION = "order_consumption", "Order Consumption"
    WASTE = "waste", "Waste"
    CORRECTION = "correction", "Correction"
    EXPIRY = "expiry", "Expiry"


class MenuItem(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="menu_items")
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["shop", "name"],
                name="unique_menu_item_per_shop"
            )
        ]

    def __str__(self):
        return f"{self.shop} ({self.name})"


class RecipeComponent(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="recipe_components")
    prepared_item = models.ForeignKey(PreparedItem, on_delete=models.PROTECT, related_name="recipe_components")
    quantity = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["menu_item", "prepared_item"],
                name="unique_prepared_item_per_recipe"
            )
        ]

    def __str__(self):
        return f"{self.menu_item.name} - {self.prepared_item.name}: {self.quantity}"


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Order(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk} - {self.status}"


# drinks are allowed to exist as separate rows
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"Order #{self.order_id} - {self.quantity}x {self.menu_item.name}"


class InventoryEvent(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="inventory_events")
    order_item = models.ForeignKey(
        OrderItem,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_events"
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    quantity_delta = models.DecimalField(max_digits=12, decimal_places=3) # how much was added or removed from the batch
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["batch", "created_at"])
        ]

    def __str__(self):
        return f"Batch #{self.batch_id} - {self.event_type} ({self.quantity_delta})"