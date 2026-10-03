from django.db import transaction

from ..models import (
    Order,
    OrderItem,
    OrderItemTopping,
    OrderStatus,
    RecipeComponent,
)

from .inventory import (
    get_item_inventory,
    get_estimated_servings,
    lock_available_batches,
    get_inventory_from_batches,
    consume_from_batches,
)

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
            raise ValueError(
                "Order item quantity must be greater than zero."
            )

        if menu_item.shop != shop:
            raise ValueError(
                "Menu item must belong to the same shop."
            )

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

    requirements = calculate_order_requirements(order)

    sorted_requirements = sorted(
        requirements.items(),
        key=lambda item: item[0].id
    )

    locked_batches_by_item = {}

    for prepared_item, required_quantity in sorted_requirements:
        batches = lock_available_batches(
            prepared_item
        )

        available = get_inventory_from_batches(
            batches
        )

        if available < required_quantity:
            raise ValueError(
                f"Insufficient inventory for {prepared_item.name}."
            )

        locked_batches_by_item[
            prepared_item.id
        ] = batches

    for prepared_item, required_quantity in sorted_requirements:
        consume_from_batches(
            locked_batches_by_item[
                prepared_item.id
            ],
            required_quantity
        )

    warnings = []

    for prepared_item in requirements:
        servings_remaining = get_estimated_servings(
            prepared_item
        )

        if servings_remaining <= 3:
            warnings.append(
                f"Low stock: {prepared_item.name} has about "
                f"{servings_remaining} servings remaining."
            )

    return order, warnings


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
                requirements[
                    prepared_item
                ] += required_quantity
            else:
                requirements[
                    prepared_item
                ] = required_quantity

        for topping in order_item.toppings.all():
            prepared_item = topping.prepared_item

            required_quantity = (
                topping.quantity
                * prepared_item.quantity_per_serving
                * order_item.quantity
            )

            if prepared_item in requirements:
                requirements[
                    prepared_item
                ] += required_quantity
            else:
                requirements[
                    prepared_item
                ] = required_quantity

    return requirements


def check_order_inventory(order):
    requirements = calculate_order_requirements(
        order
    )

    for prepared_item, required_quantity in requirements.items():
        available = get_item_inventory(
            prepared_item
        )

        if available < required_quantity:
            return False

    return True


@transaction.atomic
def complete_order(order):
    if order.status != OrderStatus.PENDING:
        raise ValueError(
            "Only pending orders can be completed."
        )

    order.status = OrderStatus.COMPLETED
    order.save()

    return order


# Cancel an order and restore inventory has been removed for right now, might be added back later.