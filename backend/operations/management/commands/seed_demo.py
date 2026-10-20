from datetime import timedelta
from decimal import Decimal
import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ...models import (
    Shop,
    StorageLocation,
    LocationType,
    PreparedItem,
    Unit,
    MenuItem,
    RecipeComponent,
)


from ...services.demo import refresh_demo_shop
from ...auth_views import DEMO_EMAIL
from ..demo_history import HISTORY_DAYS


class Command(BaseCommand):
    help = "Seed BubbleFlow prototype data"

    def handle(self, *args, **options):

        # --------------------------------------------------
        # DEMO USER
        # --------------------------------------------------
        #
        # The "Try the demo" button logs in as this user,
        # so nobody needs its password. It gets a random
        # one that is never printed or stored anywhere.
        # --------------------------------------------------

        User = get_user_model()

        demo_user, created = User.objects.get_or_create(
            username=DEMO_EMAIL,
            defaults={"email": DEMO_EMAIL},
        )

        if created:
            demo_user.set_password(secrets.token_urlsafe(32))
            demo_user.save()

        self.stdout.write("Seeded demo user")


        # --------------------------------------------------
        # SHOP
        # --------------------------------------------------
        #
        # Look the shop up by its owner first, so a
        # registered shop that happens to be named
        # "BubbleFlow Demo" is never taken over.
        # --------------------------------------------------

        shop = (
            Shop.objects.filter(owner=demo_user).first()
            or Shop.objects.filter(
                name="BubbleFlow Demo",
                owner__isnull=True,
            ).first()
            or Shop(name="BubbleFlow Demo")
        )

        shop.owner = demo_user
        shop.timezone = "America/New_York"
        shop.inventory_buffer_percent = Decimal("10.00")
        shop.low_stock_threshold_servings = 3
        shop.save()

        self.stdout.write("Seeded shop")


        # --------------------------------------------------
        # STORAGE LOCATIONS
        # --------------------------------------------------

        refrigerator, _ = StorageLocation.objects.update_or_create(
            shop=shop,
            name="Main Refrigerator",
            defaults={
                "location_type": LocationType.REFRIGERATOR,
                "is_active": True,
            },
        )

        prep_station, _ = StorageLocation.objects.update_or_create(
            shop=shop,
            name="Prep Station",
            defaults={
                "location_type": LocationType.PREP_STATION,
                "is_active": True,
            },
        )

        room_temperature, _ = StorageLocation.objects.update_or_create(
            shop=shop,
            name="Room Temperature Storage",
            defaults={
                "location_type": LocationType.ROOM_TEMPERATURE,
                "is_active": True,
            },
        )

        self.stdout.write("Seeded storage locations")


        # --------------------------------------------------
        # PREPARED ITEMS
        # --------------------------------------------------

        prepared_data = [
            {
                "name": "Thai Tea",
                "unit": Unit.MILLILITER,
                "batch_quantity": 4000,
                "serving_quantity": 500,
                "prep_minutes": 20,
                "shelf_life": timedelta(days=3),
                "requires_cooling": True,
            },
            {
                "name": "Black Tea",
                "unit": Unit.MILLILITER,
                "batch_quantity": 4000,
                "serving_quantity": 500,
                "prep_minutes": 15,
                "shelf_life": timedelta(days=3),
                "requires_cooling": True,
            },
            {
                "name": "Oolong Tea",
                "unit": Unit.MILLILITER,
                "batch_quantity": 4000,
                "serving_quantity": 500,
                "prep_minutes": 15,
                "shelf_life": timedelta(days=3),
                "requires_cooling": True,
            },
            {
                "name": "Jasmine Tea",
                "unit": Unit.MILLILITER,
                "batch_quantity": 4000,
                "serving_quantity": 500,
                "prep_minutes": 15,
                "shelf_life": timedelta(days=3),
                "requires_cooling": True,
            },
            {
                "name": "Brown Sugar Milk",
                "unit": Unit.MILLILITER,
                "batch_quantity": 4000,
                "serving_quantity": 500,
                "prep_minutes": 20,
                "shelf_life": timedelta(days=3),
                "requires_cooling": True,
            },
            {
                "name": "Tapioca Pearls",
                "unit": Unit.GRAM,
                "batch_quantity": 2000,
                "serving_quantity": 60,
                "prep_minutes": 45,
                "shelf_life": timedelta(hours=4),
                "requires_cooling": False,
            },
        ]

        prepared_items = {}

        for data in prepared_data:

            item, _ = PreparedItem.objects.update_or_create(
                shop=shop,
                name=data["name"],
                defaults={
                    "base_unit": data["unit"],
                    "default_batch_quantity": Decimal(
                        str(data["batch_quantity"])
                    ),
                    "batch_label": "batch",
                    "quantity_per_serving": Decimal(
                        str(data["serving_quantity"])
                    ),
                    "preparation_time": timedelta(
                        minutes=data["prep_minutes"]
                    ),
                    "default_shelf_life": data["shelf_life"],
                    "requires_cooling": data["requires_cooling"],
                    "is_topping": data["name"] == "Tapioca Pearls",
                    # Items that need cooling take 20 minutes to cool before serving
                    "cooling_time": timedelta(
                        minutes=20 if data["requires_cooling"] else 0
                    ),
                    "is_active": True,
                },
            )

            prepared_items[data["name"]] = item

            self.stdout.write(
                f"Seeded prepared item: {data['name']}"
            )


        # --------------------------------------------------
        # MENU ITEMS
        # --------------------------------------------------

        menu_data = [
            ("Thai Tea", "Thai Tea", 500),
            ("Black Tea", "Black Tea", 500),
            ("Oolong Tea", "Oolong Tea", 500),
            ("Jasmine Tea", "Jasmine Tea", 500),
            ("Brown Sugar Milk", "Brown Sugar Milk", 500),
        ]

        for menu_name, prepared_name, quantity in menu_data:

            menu_item, _ = MenuItem.objects.update_or_create(
                shop=shop,
                name=menu_name,
                defaults={
                    "is_active": True,
                },
            )

            RecipeComponent.objects.update_or_create(
                menu_item=menu_item,
                prepared_item=prepared_items[prepared_name],
                defaults={
                    "quantity": Decimal(str(quantity)),
                },
            )

            self.stdout.write(
                f"Seeded menu item: {menu_name}"
            )


        # --------------------------------------------------
        # STOCK AND ORDER HISTORY
        # --------------------------------------------------
        #
        # Give every ingredient at least a full batch of
        # ready stock, and catch the past orders up to now.
        # The demo login does the same thing, so the live
        # demo stays stocked between deploys. Both steps
        # only add what's missing, so rerunning is safe.
        # --------------------------------------------------

        restocked, added_orders = refresh_demo_shop(shop)

        for name in restocked:
            self.stdout.write(
                f"Created READY batch for {name}"
            )

        if not restocked:
            self.stdout.write(
                "Every ingredient has a full batch ready - skipped"
            )

        if added_orders:
            self.stdout.write(
                f"Added {added_orders} past orders "
                f"(up to {HISTORY_DAYS} days of history)"
            )
        else:
            self.stdout.write(
                "Order history already up to date - skipped"
            )


        # --------------------------------------------------
        # DONE
        # --------------------------------------------------

        self.stdout.write(
            self.style.SUCCESS(
                "\nBubbleFlow prototype data seeded successfully!"
            )
        )