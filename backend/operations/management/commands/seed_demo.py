from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import (
    Shop,
    StorageLocation,
    LocationType,
    PreparedItem,
    Unit,
    MenuItem,
    RecipeComponent,
    Batch,
)


from ...services.inventory import create_batch, mark_batch_ready


class Command(BaseCommand):
    help = "Seed BubbleFlow prototype data"

    def handle(self, *args, **options):

        # --------------------------------------------------
        # SHOP
        # --------------------------------------------------

        shop, _ = Shop.objects.update_or_create(
            name="BubbleFlow Demo",
            defaults={
                "timezone": "America/New_York",
                "inventory_buffer_percent": Decimal("10.00"),
                "low_stock_threshold_servings": 15,
            },
        )

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
        # INITIAL INVENTORY
        # --------------------------------------------------
        #
        # Orders cannot consume inventory unless READY
        # batches exist.
        #
        # Only create an initial batch if that item has
        # no batches yet, so rerunning the seed command
        # doesn't keep duplicating inventory.
        # --------------------------------------------------

        now = timezone.now()

        for name, item in prepared_items.items():

            if Batch.objects.filter(prepared_item=item).exists():
                self.stdout.write(
                    f"Batch already exists for {name} - skipped"
                )
                continue

            # Tapioca stays at the prep station.
            if name == "Tapioca Pearls":
                location = prep_station
            else:
                location = refrigerator

            batch = create_batch(
                prepared_item=item,
                storage_location=location,
                batch_fraction=Decimal("1.0"),
                started_at=now - item.preparation_time,
            )

            mark_batch_ready(batch)

            self.stdout.write(
                f"Created READY batch for {name}"
            )


        # --------------------------------------------------
        # DONE
        # --------------------------------------------------

        self.stdout.write(
            self.style.SUCCESS(
                "\nBubbleFlow prototype data seeded successfully!"
            )
        )