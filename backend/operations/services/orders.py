from django.db import transaction

from ..models import (
    Order,
    OrderItem,
    OrderItemTopping,
    OrderStatus,
    RecipeComponent,
)

from .inventory import get_item_inventory, consume_fefo


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

        for topping in item.get("toppings", []):
            prepared_item = topping["prepared_item"]

            if prepared_item.shop != shop:
                raise ValueError(
                    "Topping must belong to the same shop."
                )

            OrderItemTopping.objects.create(
                order_item=order_item,
                prepared_item=prepared_item,
                quantity=topping.get("quantity", 1)
            )

    return order


def calculate_order_requirements(order):
    requirements = {}

    for order_item in order.order_items.all():
        components = RecipeComponent.objects.filter(
            menu_item=order_item.menu_item
        )

        for component in components:
            prepared_item = component.prepared_item

            required_quantity = (
                component.quantity
                * order_item.quantity
            )

            if prepared_item in requirements:
                requirements[prepared_item] += required_quantity
            else:
                requirements[prepared_item] = required_quantity

        for topping in order_item.toppings.all():
            prepared_item = topping.prepared_item

            required_quantity = (
                topping.quantity
                * prepared_item.quantity_per_serving
                * order_item.quantity
            )

            if prepared_item in requirements:
                requirements[prepared_item] += required_quantity
            else:
                requirements[prepared_item] = required_quantity

    return requirements


def check_order_inventory(order):
    requirements = calculate_order_requirements(order)

    for prepared_item, required_quantity in requirements.items():
        available = get_item_inventory(prepared_item)

        if available < required_quantity:
            return False

    return True


@transaction.atomic
def complete_order(order):
    if order.status != OrderStatus.PENDING:
        raise ValueError("Only pending orders can be completed.")

    requirements = calculate_order_requirements(order)

    for prepared_item, required_quantity in requirements.items():
        available = get_item_inventory(prepared_item)

        if available < required_quantity:
            raise ValueError(
                f"Insufficient inventory for {prepared_item.name}."
            )

    for prepared_item, required_quantity in requirements.items():
        consume_fefo(
            prepared_item,
            required_quantity
        )

    order.status = OrderStatus.COMPLETED
    order.save()

    return order


def cancel_order(order):
    if order.status != OrderStatus.PENDING:
        raise ValueError("Only pending orders can be cancelled.")

    order.status = OrderStatus.CANCELLED
    order.save()

    return order