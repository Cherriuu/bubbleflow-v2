# Serializers convert complex data types, such as Django models, into native Python datatypes that can easily be rendered into JSON by the Django Rest Framework.
# They also provide deserialization, allowing parsed data to be converted back into complex types.
# What we define in our serializers is the structure of the data that will be sent to and receieved from the frontend.

from datetime import timedelta
from decimal import Decimal

from django.db import transaction

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
            "is_topping",
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
        # The batches list adds annotated_balance in its own query; a single batch is looked up here instead
        if hasattr(batch, "annotated_balance"):
            return batch.annotated_balance or Decimal("0")

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
    # The ingredient's name, so pages can show "+1 Tapioca Pearls" without looking it up
    prepared_item_name = serializers.CharField(
        source="prepared_item.name",
        read_only=True
    )

    class Meta:
        model = OrderItemTopping
        fields = [
            "id",
            "prepared_item",
            "prepared_item_name",
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


# A length of time sent and returned as a whole number of minutes, stored as a duration
class MinutesField(serializers.Field):
    def __init__(self, min_value=0, **kwargs):
        self.min_value = min_value
        super().__init__(**kwargs)

    def to_representation(self, value):
        return int(value.total_seconds() // 60)

    def to_internal_value(self, data):
        try:
            minutes = int(data)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Enter a whole number of minutes.")

        if minutes < self.min_value:
            raise serializers.ValidationError(f"Must be at least {self.min_value} minutes.")

        return timedelta(minutes=minutes)


# An ingredient the shop prepares in batches, as edited on the Menu page
class IngredientSerializer(serializers.ModelSerializer):
    default_batch_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001")
    )
    quantity_per_serving = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001")
    )
    preparation_time = MinutesField(min_value=0)
    cooling_time = MinutesField(min_value=0, required=False)
    default_shelf_life = MinutesField(min_value=1)

    class Meta:
        model = PreparedItem
        fields = [
            "id",
            "name",
            "base_unit",
            "default_batch_quantity",
            "quantity_per_serving",
            "preparation_time",
            "cooling_time",
            "default_shelf_life",
            "requires_cooling",
            "is_topping",
            "is_active",
        ]

    # Names must be unique within the shop, ignoring capitals
    def validate_name(self, value):
        name = value.strip()

        matches = PreparedItem.objects.filter(
            shop=self.context["shop"],
            name__iexact=name
        )

        if self.instance:
            matches = matches.exclude(pk=self.instance.pk)

        if matches.exists():
            raise serializers.ValidationError(f'You already have an ingredient named "{name}".')

        return name

    # Items that don't need cooling always have a cooling time of zero
    def validate(self, attrs):
        requires_cooling = attrs.get(
            "requires_cooling",
            self.instance.requires_cooling if self.instance else False
        )

        if not requires_cooling:
            attrs["cooling_time"] = timedelta(0)

        return attrs

    def create(self, validated_data):
        return PreparedItem.objects.create(
            shop=self.context["shop"],
            **validated_data
        )


# One ingredient and how much of it goes into one drink
class RecipeRowSerializer(serializers.Serializer):
    prepared_item_id = serializers.PrimaryKeyRelatedField(
        queryset=PreparedItem.objects.all(),
        source="prepared_item"
    )
    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001")
    )


# A drink customers can order and its recipe, as edited on the Menu page
class DrinkSerializer(serializers.ModelSerializer):
    recipe = RecipeRowSerializer(
        many=True,
        source="recipe_components",
        allow_empty=False
    )

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "name",
            "is_active",
            "recipe",
        ]

    # Names must be unique within the shop, ignoring capitals
    def validate_name(self, value):
        name = value.strip()

        matches = MenuItem.objects.filter(
            shop=self.context["shop"],
            name__iexact=name
        )

        if self.instance:
            matches = matches.exclude(pk=self.instance.pk)

        if matches.exists():
            raise serializers.ValidationError(f'You already have a drink named "{name}".')

        return name

    # A recipe can't repeat an ingredient or use another shop's ingredients
    def validate_recipe(self, rows):
        ingredient_ids = [row["prepared_item"].id for row in rows]

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Each ingredient can only be used once in a recipe.")

        if any(row["prepared_item"].shop_id != self.context["shop"].id for row in rows):
            raise serializers.ValidationError("Recipe ingredients must belong to your shop.")

        return rows

    # Save the drink and its recipe rows together, or not at all
    @transaction.atomic
    def create(self, validated_data):
        rows = validated_data.pop("recipe_components")

        drink = MenuItem.objects.create(
            shop=self.context["shop"],
            **validated_data
        )

        self.save_recipe(drink, rows)

        return drink

    # Update the drink, and replace its whole recipe if a new one was sent
    @transaction.atomic
    def update(self, instance, validated_data):
        rows = validated_data.pop("recipe_components", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()

        if rows is not None:
            instance.recipe_components.all().delete()
            self.save_recipe(instance, rows)

        return instance

    # Create one recipe row per ingredient
    def save_recipe(self, drink, rows):
        RecipeComponent.objects.bulk_create([
            RecipeComponent(
                menu_item=drink,
                prepared_item=row["prepared_item"],
                quantity=row["quantity"]
            )
            for row in rows
        ])
