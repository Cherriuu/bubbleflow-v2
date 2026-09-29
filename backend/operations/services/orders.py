from django.db import transaction
from decimal import Decimal

from ..models import (
    Order,
    OrderItem,
    OrderItemTopping,
    OrderStatus,
    RecipeComponent,
    Size,
)

from .inventory import get_item_inventory, consume_fefo


# Create an order with customized drinks and toppings
@transaction.atomic
def create_order(shop, items):
    order = Order.objects.create(
        shop=shop,
        status=OrderStatus.PENDING
    )

    for item in items:
        menu_item = item["menu_item"]
        quantity = item["quantity"]

        if quantity <= 0:
            raise ValueError("Order item quantity must be greater than zero.")

        if menu_item.shop != shop:
            raise ValueError("Menu item must belong to the same shop.")

        order_item = OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=quantity,
            size=item["size"],
            sugar_level=item["sugar_level"],
            ice_level=item["ice_level"]
        )

        # Add each topping to the customized drink
        for topping in item.get("toppings", []):
            OrderItemTopping.objects.create(
                order_item=order_item,
                prepared_item=topping["prepared_item"],
                quantity=topping.get("quantity", 1)
            )

    return order


# Calculate all inventory needed to make an order
def calculate_order_requirements(order):
    requirements = {}

    size_multipliers = {
        Size.SMALL: Decimal("0.8"),
        Size.MEDIUM: Decimal("1.0"),
        Size.LARGE: Decimal("1.2")
    }

    for order_item in order.order_items.all():
        multiplier = size_multipliers[order_item.size]

        # Calculate ingredients from the drink recipe
        components = RecipeComponent.objects.filter(
            menu_item=order_item.menu_item
        )

        for component in components:
            prepared_item = component.prepared_item

            required_quantity = (
                component.quantity
                * order_item.quantity
                * multiplier
            )

            if prepared_item in requirements:
                requirements[prepared_item] += required_quantity
            else:
                requirements[prepared_item] = required_quantity

        # Add toppings to inventory requirements
        for topping in order_item.toppings.all():
            required_quantity = (
                topping.quantity * order_item.quantity
            )

            if topping.prepared_item in requirements:
                requirements[topping.prepared_item] += required_quantity
            else:
                requirements[topping.prepared_item] = required_quantity

    return requirements


# Check whether the order can currently be fulfilled
def check_order_inventory(order):
    requirements = calculate_order_requirements(order)

    for prepared_item, required_quantity in requirements.items():
        available = get_item_inventory(prepared_item)

        if available < required_quantity:
            return False

    return True


# Complete the order and deduct inventory using FEFO
@transaction.atomic
def complete_order(order):
    if order.status != OrderStatus.PENDING:
        raise ValueError("Only pending orders can be completed.")

    requirements = calculate_order_requirements(order)

    # Make sure every ingredient is available first
    for prepared_item, required_quantity in requirements.items():
        available = get_item_inventory(prepared_item)

        if available < required_quantity:
            raise ValueError(
                f"Insufficient inventory for {prepared_item.name}."
            )

    # Deduct each ingredient from earliest-expiring batches
    for prepared_item, required_quantity in requirements.items():
        consume_fefo(
            prepared_item,
            required_quantity
        )

    order.status = OrderStatus.COMPLETED
    order.save()

    return order


# Cancel an order that has not been completed
def cancel_order(order):
    if order.status != OrderStatus.PENDING:
        raise ValueError("Only pending orders can be cancelled.")

    order.status = OrderStatus.CANCELLED
    order.save()

    return order