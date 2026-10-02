from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from .models import (
    Batch,
    BatchStatus,
    EventType,
    InventoryEvent,
    PreparedItem,
    Shop,
    StorageLocation,
)
from .services.forecasting import recommend_production
from .services.inventory import create_batch


class RecommendationTests(TestCase):
    def setUp(self):
        self.shop = Shop.objects.create(name="Test Shop")
        self.location = StorageLocation.objects.create(
            shop=self.shop, name="Fridge 1", location_type="refrigerator"
        )
        self.tea = PreparedItem.objects.create(
            shop=self.shop,
            name="Thai Tea",
            base_unit="ml",
            default_batch_quantity=Decimal("10000"),
            quantity_per_serving=Decimal("500"),
            preparation_time=timedelta(minutes=30),
            default_shelf_life=timedelta(hours=8),
        )

        # Recent demand: a finished batch that was fully used up in the last 4 hours.
        now = timezone.now()
        used_up = Batch.objects.create(
            prepared_item=self.tea,
            storage_location=self.location,
            initial_quantity=Decimal("4000"),
            status=BatchStatus.DEPLETED,
            started_at=now - timedelta(hours=3),
            ready_at=now - timedelta(hours=2, minutes=30),
            expires_at=now + timedelta(hours=5),
        )
        InventoryEvent.objects.create(
            batch=used_up, event_type=EventType.BATCH_CREATED, quantity_delta=Decimal("4000")
        )
        InventoryEvent.objects.create(
            batch=used_up, event_type=EventType.ORDER_CONSUMPTION, quantity_delta=Decimal("-4000")
        )

    def test_recommends_production_when_nothing_is_cooking(self):
        self.assertGreater(recommend_production(self.tea), Decimal("0"))

    def test_batch_in_progress_cancels_the_recommendation(self):
        create_batch(self.tea, self.location, Decimal("1"), timezone.now())

        self.assertEqual(recommend_production(self.tea), Decimal("0"))