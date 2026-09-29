# Django REST Framework takes the HTTP request and parses it into Python data types using its built-in JSON parser.
# The serializers.py file defines how the data is validated against our defined rules to ensure that the data is in the correct format before it is saved to the database.
# Django ORM takes the validated data and saves it to the database using the defined models in models.py.

from rest_framework import serializers

from .models import (
    Shop,
    StorageLocation,
    PreparedItem,
    Batch,
    InventoryEvent,
    MenuItem,
    RecipeComponent,
    Order,
    OrderItem,
    OrderItemTopping,
)

from .services.inventory import get_batch_balance


# Shop information
class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "timezone",
            "created_at",
            "updated_at",
        ]


# Storage locations such as refrigerators and prep stations
class StorageLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageLocation
        fields = [
            "id",
            "shop",
            "name",
            "location_type",
            "is_active",
            "created_at",
            "updated_at",
        ]


# Items prepared and tracked by the shop
class PreparedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreparedItem
        fields = [
            "id",
            "shop",
            "name",
            "unit",
            "default_shelf_life",
            "default_batch_quantity",
            "usage_buffer_percentage",
            "is_active",
            "created_at",
            "updated_at",
        ]


# Individual prepared inventory batches
class BatchSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = [
            "id",
            "prepared_item",
            "storage_location",
            "status",
            "started_at",
            "ready_at",
            "expires_at",
            "created_at",
            "balance",
        ]

    def get_balance(self, batch):
        return get_batch_balance(batch)


# Changes made to inventory
class InventoryEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryEvent
        fields = [
            "id",
            "batch",
            "event_type",
            "quantity_delta",
            "reason",
            "created_at",
        ]


# Drinks or other products sold by the shop
class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = [
            "id",
            "shop",
            "name",
            "is_active",
            "created_at",
            "updated_at",
        ]


# Prepared ingredients required by a menu item
class RecipeComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeComponent
        fields = [
            "id",
            "menu_item",
            "prepared_item",
            "quantity",
        ]


# Toppings attached to a customized order item
class OrderItemToppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemTopping
        fields = [
            "id",
            "prepared_item",
            "quantity",
        ]


# Individual customized drinks in an order
class OrderItemSerializer(serializers.ModelSerializer):
    toppings = OrderItemToppingSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "menu_item",
            "quantity",
            "size",
            "sugar_level",
            "ice_level",
            "toppings",
        ]


# Customer order containing its customized drinks
class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "shop",
            "status",
            "created_at",
            "order_items",
        ]

# Validate data for creating a batch
class CreateBatchSerializer(serializers.Serializer):
    prepared_item_id = serializers.PrimaryKeyRelatedField(
        queryset=PreparedItem.objects.all(),
        source="prepared_item"
    )
    storage_location_id = serializers.PrimaryKeyRelatedField(
        queryset=StorageLocation.objects.all(),
        source="storage_location"
    )
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3
    )
    started_at = serializers.DateTimeField()


# Validate data for marking a batch ready
class MarkBatchReadySerializer(serializers.Serializer):
    ready_at = serializers.DateTimeField()


# Validate waste input
class WasteSerializer(serializers.Serializer):
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3
    )
    reason = serializers.CharField()


# Validate inventory correction input
class CorrectionSerializer(serializers.Serializer):
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3
    )
    reason = serializers.CharField()


# Validate topping input
class ToppingInputSerializer(serializers.Serializer):
    prepared_item_id = serializers.PrimaryKeyRelatedField(
        queryset=PreparedItem.objects.all(),
        source="prepared_item"
    )
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=1
    )


# Validate customized order item input
class OrderItemInputSerializer(serializers.Serializer):
    menu_item_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(),
        source="menu_item"
    )

    quantity = serializers.IntegerField(
        min_value=1
    )

    size = serializers.CharField()
    sugar_level = serializers.CharField()
    ice_level = serializers.CharField()

    toppings = ToppingInputSerializer(
        many=True,
        required=False,
        default=list
    )


# Validate order input
class CreateOrderSerializer(serializers.Serializer):
    shop_id = serializers.PrimaryKeyRelatedField(
        queryset=Shop.objects.all(),
        source="shop"
    )

    items = OrderItemInputSerializer(
        many=True,
        allow_empty=False
    )