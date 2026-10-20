# Builds realistic past orders for the demo shop, so the production recommender has history to learn from.
# seed_demo calls seed_order_history() on every run; it only adds orders that are missing, up to now.
import random
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Max

from ..models import (
    Batch,
    BatchStatus,
    EventType,
    IceLevel,
    InventoryEvent,
    MenuItem,
    Order,
    OrderItem,
    OrderItemTopping,
    OrderStatus,
    PreparedItem,
    RecipeComponent,
    Size,
    SugarLevel,
)


# Combined with each date and hour, so the same hour always gets the same orders
RANDOM_SEED = 42

# How far back the history goes
HISTORY_DAYS = 21

# How busy each open hour is (11am to 9pm, shop time): a lunch bump, the after-school peak, a quieter evening
HOUR_WEIGHTS = {
    11: 0.5,
    12: 1.0,
    13: 1.0,
    14: 0.7,
    15: 1.4,
    16: 1.6,
    17: 1.4,
    18: 0.9,
    19: 0.7,
    20: 0.5,
}

# A typical weekday sells about 225 drinks; weekends are about 30% busier, so the busiest days reach about 300
WEEKDAY_DRINKS = 225
WEEKEND_MULTIPLIER = 1.3

# How often each drink is picked; drinks not listed here get the default
DRINK_POPULARITY = {
    "Thai Tea": 30,
    "Brown Sugar Milk": 25,
    "Black Tea": 20,
    "Jasmine Tea": 15,
    "Oolong Tea": 10,
}
DEFAULT_POPULARITY = 10

# Most orders are one drink; some customers order for friends
DRINKS_PER_ORDER = [1, 2, 3]
DRINKS_PER_ORDER_WEIGHTS = [70, 22, 8]

# For each topping on each drink: no extra, one scoop, or two scoops
TOPPING_SCOOPS = [0, 1, 2]
TOPPING_SCOOP_WEIGHTS = [40, 50, 10]

# Marks the events this module writes, so the next run knows where the seeded history ends
SEEDED_REASON = "Seeded order history"


# Add any missing past orders for the shop, from the last seeded order (or 21 days ago) up to now
def seed_order_history(shop, now, refrigerator, prep_station):
    last_seeded = InventoryEvent.objects.filter(
        batch__prepared_item__shop=shop,
        reason=SEEDED_REASON
    ).aggregate(
        latest=Max("created_at")
    )["latest"]

    start = now - timedelta(days=HISTORY_DAYS)

    if last_seeded is not None and last_seeded > start:
        start = last_seeded

    menu, recipes = get_menu_and_recipes(shop)

    toppings = list(
        PreparedItem.objects.filter(
            shop=shop,
            is_topping=True,
            is_active=True
        ).order_by("id")
    )

    planned_orders = plan_orders(
        ZoneInfo(shop.timezone),
        start,
        now,
        menu,
        toppings
    )

    if not planned_orders:
        return 0

    # Everything is saved together, so a failed run leaves nothing half-written
    with transaction.atomic():
        save_orders(
            shop,
            planned_orders,
            recipes,
            refrigerator,
            prep_station
        )

    return len(planned_orders)


# Get the shop's active drinks and, for each one, the prepared items and amounts in its recipe
def get_menu_and_recipes(shop):
    recipes = {}

    for component in RecipeComponent.objects.filter(
        menu_item__shop=shop,
        menu_item__is_active=True
    ).select_related("prepared_item").order_by("id"):
        recipes.setdefault(component.menu_item_id, []).append(
            (component.prepared_item, component.quantity)
        )

    # A drink without a recipe wouldn't use any inventory, so leave it out
    menu = list(
        MenuItem.objects.filter(
            shop=shop,
            is_active=True,
            id__in=recipes.keys()
        ).order_by("id")
    )

    return menu, recipes


# Plan the orders for every open hour between start and now, without saving anything yet
def plan_orders(shop_timezone, start, now, menu, toppings):
    if not menu:
        return []

    total_weight = sum(HOUR_WEIGHTS.values())
    planned_orders = []

    day = start.astimezone(shop_timezone).date()
    last_day = now.astimezone(shop_timezone).date()

    while day <= last_day:
        # Each day gets its own random number generator, so its total is the same on every run
        day_random = random.Random(f"{RANDOM_SEED}-{day.isoformat()}")

        drinks_today = WEEKDAY_DRINKS * day_random.uniform(0.92, 1.08)

        # weekday() is 5 for Saturday and 6 for Sunday
        if day.weekday() >= 5:
            drinks_today *= WEEKEND_MULTIPLIER

        for hour, weight in HOUR_WEIGHTS.items():
            hour_start = datetime.combine(day, time(hour), tzinfo=shop_timezone)
            hour_random = random.Random(f"{RANDOM_SEED}-{hour_start.isoformat()}")

            expected_drinks = drinks_today * weight / total_weight
            drink_count = round(expected_drinks * hour_random.uniform(0.85, 1.15))

            # Plan the whole hour, then keep only the orders in the missing window.
            # Because the hour is always planned the same way, a top-up never repeats or skips an order.
            for order in plan_hour(hour_random, hour_start, drink_count, menu, toppings):
                if start < order["time"] < now:
                    planned_orders.append(order)

        day += timedelta(days=1)

    return planned_orders


# Split one hour's drinks into orders at random times within that hour
def plan_hour(hour_random, hour_start, drink_count, menu, toppings):
    orders = []
    drinks_left = drink_count

    while drinks_left > 0:
        size = min(
            hour_random.choices(DRINKS_PER_ORDER, weights=DRINKS_PER_ORDER_WEIGHTS)[0],
            drinks_left
        )

        orders.append({
            "time": hour_start + timedelta(seconds=hour_random.uniform(0, 3600)),
            "drinks": [plan_drink(hour_random, menu, toppings) for _ in range(size)],
        })

        drinks_left -= size

    return orders


# Pick one drink, its sugar and ice, and any extra toppings
def plan_drink(hour_random, menu, toppings):
    menu_item = hour_random.choices(
        menu,
        weights=[DRINK_POPULARITY.get(item.name, DEFAULT_POPULARITY) for item in menu]
    )[0]

    drink_toppings = []

    for topping in toppings:
        scoops = hour_random.choices(TOPPING_SCOOPS, weights=TOPPING_SCOOP_WEIGHTS)[0]

        if scoops > 0:
            drink_toppings.append((topping, scoops))

    return {
        "menu_item": menu_item,
        "sugar_level": hour_random.choice(SugarLevel.values),
        "ice_level": hour_random.choice(IceLevel.values),
        "toppings": drink_toppings,
    }


# Save the planned orders, their drinks and toppings, and the inventory events they used
def save_orders(shop, planned_orders, recipes, refrigerator, prep_station):
    shop_timezone = ZoneInfo(shop.timezone)

    orders = [
        Order(shop=shop, status=OrderStatus.COMPLETED)
        for _ in planned_orders
    ]

    Order.objects.bulk_create(orders, batch_size=1000)
    backdate(Order, orders, [plan["time"] for plan in planned_orders])

    order_items = []
    drink_plans = []

    for order, plan in zip(orders, planned_orders):
        for drink in plan["drinks"]:
            order_items.append(OrderItem(
                order=order,
                menu_item=drink["menu_item"],
                quantity=1,
                size=Size.MEDIUM,
                sugar_level=drink["sugar_level"],
                ice_level=drink["ice_level"],
            ))
            drink_plans.append((drink, plan["time"]))

    # On PostgreSQL, bulk_create fills in each new row's id, so the toppings and events below can point to it
    OrderItem.objects.bulk_create(order_items, batch_size=1000)

    order_item_toppings = []

    # Each usage is (order item, prepared item, quantity used, time)
    usage = []

    for order_item, (drink, when) in zip(order_items, drink_plans):
        for topping, scoops in drink["toppings"]:
            order_item_toppings.append(OrderItemTopping(
                order_item=order_item,
                prepared_item=topping,
                quantity=Decimal(scoops),
            ))

        for prepared_item, quantity in get_drink_requirements(order_item, drink, recipes).items():
            usage.append((order_item, prepared_item, quantity, when))

    OrderItemTopping.objects.bulk_create(order_item_toppings, batch_size=1000)

    save_usage(shop_timezone, usage, refrigerator, prep_station)


# Work out how much of each prepared item one drink uses, the same way calculate_order_item_requirements does
def get_drink_requirements(order_item, drink, recipes):
    requirements = {}

    for prepared_item, quantity in recipes[order_item.menu_item_id]:
        requirements[prepared_item] = (
            requirements.get(prepared_item, Decimal("0"))
            + quantity * order_item.quantity
        )

    for topping, scoops in drink["toppings"]:
        requirements[topping] = (
            requirements.get(topping, Decimal("0"))
            + Decimal(scoops) * topping.quantity_per_serving * order_item.quantity
        )

    return requirements


# Record the usage on past batches: one used-up batch per prepared item per day, so current inventory doesn't change
def save_usage(shop_timezone, usage, refrigerator, prep_station):
    usage_by_batch = {}

    for order_item, prepared_item, quantity, when in usage:
        key = (prepared_item.id, when.astimezone(shop_timezone).date())
        usage_by_batch.setdefault(key, []).append((order_item, prepared_item, quantity, when))

    batches = []
    batch_usage = []

    for rows in usage_by_batch.values():
        prepared_item = rows[0][1]
        first_use = min(row[3] for row in rows)
        last_use = max(row[3] for row in rows)

        # The batch holds exactly what was used, so its balance ends at zero, like a real used-up batch
        batches.append(Batch(
            prepared_item=prepared_item,
            storage_location=prep_station if prepared_item.is_topping else refrigerator,
            initial_quantity=sum(row[2] for row in rows),
            status=BatchStatus.DEPLETED,
            started_at=first_use - prepared_item.preparation_time - prepared_item.cooling_time,
            ready_at=first_use - prepared_item.cooling_time,
            expires_at=last_use + timedelta(minutes=1),
        ))
        batch_usage.append(rows)

    Batch.objects.bulk_create(batches, batch_size=1000)
    backdate(Batch, batches, [batch.started_at for batch in batches])

    events = []
    event_times = []

    for batch, rows in zip(batches, batch_usage):
        events.append(InventoryEvent(
            batch=batch,
            event_type=EventType.BATCH_CREATED,
            quantity_delta=batch.initial_quantity,
            reason=SEEDED_REASON,
        ))
        event_times.append(batch.started_at)

        for order_item, _, quantity, when in rows:
            events.append(InventoryEvent(
                batch=batch,
                order_item=order_item,
                event_type=EventType.ORDER_CONSUMPTION,
                quantity_delta=-quantity,
                reason=SEEDED_REASON,
            ))
            event_times.append(when)

    # bulk_create only inserts new rows, which the append-only ledger allows; it never calls save() on old ones
    InventoryEvent.objects.bulk_create(events, batch_size=1000)
    backdate(InventoryEvent, events, event_times)


# Move just-created rows to their real time in the past, since auto_now_add always stamps the current time.
# For inventory events this is the one deliberate exception to the append-only rule, like record_usage in tests.py:
# it runs in the same transaction that created the rows, before anyone can read them, and only changes created_at.
def backdate(model, objects, times):
    for obj, when in zip(objects, times):
        obj.created_at = when

    model.objects.bulk_update(objects, ["created_at"], batch_size=1000)
