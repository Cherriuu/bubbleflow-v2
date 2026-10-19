# Serializers convert complex data types, such as Django models, into native Python datatypes that can easily be rendered into JSON by the Django Rest Framework.
# They also provide deserialization, allowing parsed data to be converted back into complex types.
# What we define in our serializers is the structure of the data that will be sent to and receieved from the frontend.

from decimal import Decimal

from rest_framework import serializers
from .services.inventory import get_batch_balance

# Import all of our models to use them in our serializers
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

# Shop information
class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "timezone",
            "inventory_buffer_percent",
            "low_stock_threshold_servings",
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
            "base_unit",
            "default_batch_quantity",
            "batch_label",
            "quantity_per_serving",
            "preparation_time",
            "default_shelf_life",
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
            "initial_quantity",
            "status",
            "started_at",
            "ready_at",
            "expires_at",
            "created_at",
            "balance",
        ]

    # We also went to send over the current balance of the batch, which is not a field in the model, so we define a method to get it.
    def get_balance(self, batch):
        return get_batch_balance(batch)


# Changes made to inventory, shown in a batch's history
class InventoryEventSerializer(serializers.ModelSerializer):
    order_id = serializers.SerializerMethodField()

    class Meta:
        model = InventoryEvent
        fields = [
            "id",
            "event_type",
            "quantity_delta",
            "reason",
            "created_at",
            "order_id",
        ]

    # The order that used this stock, or None for events that aren't from an order
    def get_order_id(self, event):
        if event.order_item is None:
            return None

        return event.order_item.order_id


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
# When an order item is serialized, also serialize its toppings, this is a nested serializer.
class OrderItemSerializer(serializers.ModelSerializer):
    toppings = OrderItemToppingSerializer(many=True, read_only=True) # Read-only so that toppings cannot be created or updated through this serializer.

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
    order_items = OrderItemSerializer(many=True, read_only=True)

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
    # When we define a serializer field with a PrimaryKeyRelatedField, it means that the frontend will send the ID of the related object instead of the full object data. The serializer will then validate that the ID corresponds to an existing object in the database.
    prepared_item_id = serializers.PrimaryKeyRelatedField(
        queryset=PreparedItem.objects.all(),
        source="prepared_item"
    )
    storage_location_id = serializers.PrimaryKeyRelatedField(
        queryset=StorageLocation.objects.all(),
        source="storage_location"
    )
    batch_fraction = serializers.DecimalField(
        max_digits=5,
        decimal_places=3,
        min_value=Decimal("0.001")
    )
    started_at = serializers.DateTimeField()


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
# The shop is not part of the input. The view always uses the logged-in user's shop, so any shop_id in the body is ignored.
class CreateOrderSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(
        many=True,
        allow_empty=False
    )


# Validate shop registration input
class RegisterSerializer(serializers.Serializer):
    shop_name = serializers.CharField(
        max_length=120
    )
    # The email is also the username, which Django limits to 150 characters
    email = serializers.EmailField(
        max_length=150
    )
    password = serializers.CharField(
        write_only=True
    )


# Validate login input
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True
    )