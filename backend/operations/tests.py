# Tests for shop registration, login, and keeping each shop's data separate.
# Run with: python manage.py test operations
from datetime import timedelta
from decimal import Decimal
import threading
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.db.models import Sum
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .auth_views import DEMO_EMAIL
from .models import (
    Batch,
    BatchStatus,
    EventType,
    ImmutableEventError,
    InventoryEvent,
    LocationType,
    MenuItem,
    Order,
    OrderItem,
    OrderItemTopping,
    OrderStatus,
    PreparedItem,
    RecipeComponent,
    Shop,
    StorageLocation,
    Unit,
)
from .services.inventory import (
    create_batch,
    expire_batch,
    get_batch_balance,
    get_item_inventory,
    mark_batch_ready,
    record_correction,
)
from .services.demo import refresh_demo_shop
from .services.orders import create_order
from .services.forecasting import (
    forecast_demand,
    get_same_hours_usage,
    get_start_by,
    recommend_production,
)


PASSWORD = "tapioca-pearls-42"


# Create a shop with its own login, one drink, and a ready batch of tea
def make_shop(name, email):
    user = get_user_model().objects.create_user(
        username=email,
        email=email,
        password=PASSWORD
    )

    shop = Shop.objects.create(
        owner=user,
        name=name
    )

    location = StorageLocation.objects.create(
        shop=shop,
        name="Main Refrigerator",
        location_type=LocationType.REFRIGERATOR
    )

    tea = PreparedItem.objects.create(
        shop=shop,
        name="Black Tea",
        base_unit=Unit.MILLILITER,
        default_batch_quantity=Decimal("4000"),
        quantity_per_serving=Decimal("500"),
        preparation_time=timedelta(minutes=15),
        default_shelf_life=timedelta(days=3)
    )

    menu_item = MenuItem.objects.create(
        shop=shop,
        name="Black Tea"
    )

    RecipeComponent.objects.create(
        menu_item=menu_item,
        prepared_item=tea,
        quantity=Decimal("500")
    )

    batch = create_batch(
        shop=shop,
        prepared_item=tea,
        storage_location=location,
        batch_fraction=Decimal("1"),
        started_at=timezone.now() - tea.preparation_time
    )

    mark_batch_ready(batch)

    order = Order.objects.create(
        shop=shop
    )

    return {
        "user": user,
        "shop": shop,
        "location": location,
        "tea": tea,
        "menu_item": menu_item,
        "batch": batch,
        "order": order,
    }


# The validated items list that create_order expects, one entry per quantity
def order_items(menu_item, *quantities):
    return [
        {
            "menu_item": menu_item,
            "quantity": quantity,
            "size": "medium",
            "sugar_level": "100",
            "ice_level": "regular_ice",
        }
        for quantity in quantities
    ]


def order_body(menu_item, **extra):
    return {
        "items": [
            {
                "menu_item_id": menu_item.id,
                "quantity": 1,
                "size": "medium",
                "sugar_level": "100",
                "ice_level": "regular_ice",
            }
        ],
        **extra,
    }


class AuthTests(APITestCase):
    def setUp(self):
        # Login and register are rate limited, and the limit is stored in the cache
        cache.clear()

    def test_register_creates_shop_and_logs_in(self):
        response = self.client.post(
            "/api/auth/register/",
            {"shop_name": "Pearl House", "email": "Owner@Pearl.test", "password": PASSWORD},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["shop"]["name"], "Pearl House")

        user = get_user_model().objects.get(username="owner@pearl.test")
        self.assertEqual(user.shop.name, "Pearl House")

        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["shop"]["id"], user.shop.id)

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            "/api/auth/register/",
            {"shop_name": "Pearl House", "email": "owner@pearl.test", "password": "12345678"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Shop.objects.filter(name="Pearl House").exists())

    def test_register_rejects_existing_email(self):
        make_shop("Pearl House", "owner@pearl.test")

        response = self.client.post(
            "/api/auth/register/",
            {"shop_name": "Copycat", "email": "OWNER@pearl.test", "password": PASSWORD},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Shop.objects.filter(name="Copycat").exists())

    def test_login_and_me(self):
        data = make_shop("Pearl House", "owner@pearl.test")

        response = self.client.post(
            "/api/auth/login/",
            {"email": "Owner@Pearl.test", "password": PASSWORD},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["shop"], {"id": data["shop"].id, "name": "Pearl House"})

    def test_wrong_password_fails(self):
        make_shop("Pearl House", "owner@pearl.test")

        response = self.client.post(
            "/api/auth/login/",
            {"email": "owner@pearl.test", "password": "wrong-password"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_when_logged_out_returns_401_and_sets_csrf_cookie(self):
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("csrftoken", response.cookies)

    def test_logout(self):
        data = make_shop("Pearl House", "owner@pearl.test")
        self.client.force_login(data["user"])

        response = self.client.post("/api/auth/logout/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_demo_login(self):
        self.assertEqual(
            self.client.post("/api/auth/demo-login/").status_code,
            status.HTTP_404_NOT_FOUND
        )

        data = make_shop("BubbleFlow Demo", DEMO_EMAIL)

        response = self.client.post("/api/auth/demo-login/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["shop"]["id"], data["shop"].id)

    def test_user_without_shop_cannot_use_api(self):
        user = get_user_model().objects.create_user(
            username="admin@pearl.test",
            password=PASSWORD
        )
        self.client.force_login(user)

        self.assertEqual(self.client.get("/api/batches/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED)


class LoggedOutTests(APITestCase):
    def test_health_check_is_public(self):
        self.assertEqual(self.client.get("/api/health/").status_code, status.HTTP_200_OK)

    def test_logged_out_requests_get_403(self):
        data = make_shop("Pearl House", "owner@pearl.test")

        get_urls = [
            "/api/prepared-items/",
            "/api/storage-locations/",
            "/api/batches/",
            "/api/menu-items/",
            "/api/orders/",
            "/api/inventory/",
            "/api/recommendations/",
        ]

        for url in get_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

        post_urls = [
            "/api/batches/create/",
            f"/api/batches/{data['batch'].id}/ready/",
            f"/api/batches/{data['batch'].id}/waste/",
            f"/api/batches/{data['batch'].id}/correction/",
            "/api/orders/create/",
            f"/api/orders/{data['order'].id}/complete/",
        ]

        for url in post_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {}, format="json").status_code, status.HTTP_403_FORBIDDEN)


class ShopIsolationTests(APITestCase):
    def setUp(self):
        self.a = make_shop("Shop A", "a@shop.test")
        self.b = make_shop("Shop B", "b@shop.test")
        self.client.force_login(self.a["user"])

    def ids(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return {row["id"] for row in response.data}

    def test_lists_only_show_own_shop(self):
        self.assertEqual(self.ids("/api/prepared-items/"), {self.a["tea"].id})
        self.assertEqual(self.ids("/api/storage-locations/"), {self.a["location"].id})
        self.assertEqual(self.ids("/api/batches/"), {self.a["batch"].id})
        self.assertEqual(self.ids("/api/menu-items/"), {self.a["menu_item"].id})
        self.assertEqual(self.ids("/api/orders/"), {self.a["order"].id})
        self.assertEqual(self.ids("/api/inventory/"), {self.a["tea"].id})
        self.assertEqual(self.ids("/api/recommendations/"), {self.a["tea"].id})

    def test_cannot_change_other_shops_batch(self):
        batch = self.b["batch"]
        batch.status = BatchStatus.PREPARING
        batch.save()

        responses = [
            self.client.post(f"/api/batches/{batch.id}/ready/"),
            self.client.post(f"/api/batches/{batch.id}/waste/", {"quantity": "100", "reason": "spilled"}, format="json"),
            self.client.post(f"/api/batches/{batch.id}/correction/", {"quantity": "100", "reason": "recount"}, format="json"),
        ]

        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        batch.refresh_from_db()
        self.assertEqual(batch.status, BatchStatus.PREPARING)
        self.assertEqual(batch.inventory_events.count(), 1)

    def test_cannot_complete_other_shops_order(self):
        response = self.client.post(f"/api/orders/{self.b['order'].id}/complete/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.b["order"].refresh_from_db()
        self.assertEqual(self.b["order"].status, OrderStatus.PENDING)

    def test_cannot_create_batch_with_other_shops_item(self):
        response = self.client.post(
            "/api/batches/create/",
            {
                "prepared_item_id": self.b["tea"].id,
                "storage_location_id": self.a["location"].id,
                "batch_fraction": "1",
                "started_at": timezone.now().isoformat(),
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Batch.objects.filter(prepared_item=self.b["tea"]).count(), 1)

    def test_cannot_order_other_shops_menu_item(self):
        response = self.client.post(
            "/api/orders/create/",
            order_body(self.b["menu_item"]),
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.filter(shop=self.b["shop"]).count(), 1)

    def test_order_uses_logged_in_shop_even_if_body_sends_another(self):
        response = self.client.post(
            "/api/orders/create/",
            order_body(self.a["menu_item"], shop_id=self.b["shop"].id),
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(id=response.data["order"]["id"])
        self.assertEqual(order.shop, self.a["shop"])
        self.assertEqual(Order.objects.filter(shop=self.b["shop"]).count(), 1)


class CsrfTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.data = make_shop("Pearl House", "owner@pearl.test")

        # The default test client skips CSRF checks, so this one turns them on
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf_token(self):
        self.client.get("/api/auth/me/")
        return self.client.cookies["csrftoken"].value

    def test_logged_in_post_without_csrf_token_is_rejected(self):
        self.client.force_login(self.data["user"])

        response = self.client.post(
            "/api/orders/create/",
            order_body(self.data["menu_item"]),
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Order.objects.count(), 1)

    def test_logged_in_post_with_csrf_token_works(self):
        self.client.force_login(self.data["user"])
        token = self.csrf_token()

        response = self.client.post(
            "/api/orders/create/",
            order_body(self.data["menu_item"]),
            format="json",
            HTTP_X_CSRFTOKEN=token
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_login_without_csrf_token_is_rejected(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "owner@pearl.test", "password": PASSWORD},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_with_csrf_token_works(self):
        token = self.csrf_token()

        response = self.client.post(
            "/api/auth/login/",
            {"email": "owner@pearl.test", "password": PASSWORD},
            format="json",
            HTTP_X_CSRFTOKEN=token
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LedgerTests(TestCase):
    def setUp(self):
        self.data = make_shop("Pearl House", "owner@pearl.test")
        self.batch = self.data["batch"]

    def test_expiring_twice_writes_one_expiry_event(self):
        # Two copies of the same batch, like two requests that both loaded it while it was ready
        first = Batch.objects.get(id=self.batch.id)
        second = Batch.objects.get(id=self.batch.id)

        expire_batch(first)
        expire_batch(second)

        self.assertEqual(
            self.batch.inventory_events.filter(event_type=EventType.EXPIRY).count(),
            1
        )
        self.assertEqual(get_batch_balance(self.batch), Decimal("0"))

        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, BatchStatus.EXPIRED)

    def test_correction_that_goes_negative_is_rejected(self):
        with self.assertRaisesMessage(ValueError, "Correction would make the batch balance negative."):
            record_correction(self.batch, Decimal("-4000.001"), "recount")

        self.assertEqual(get_batch_balance(self.batch), Decimal("4000"))

    def test_correction_to_zero_depletes_and_positive_correction_makes_ready(self):
        record_correction(self.batch, Decimal("-4000"), "spilled everything")

        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, BatchStatus.DEPLETED)

        record_correction(self.batch, Decimal("500"), "found a pitcher")

        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, BatchStatus.READY)
        self.assertEqual(get_batch_balance(self.batch), Decimal("500"))

    def test_positive_correction_on_expired_depleted_batch_stays_depleted(self):
        record_correction(self.batch, Decimal("-4000"), "spilled everything")

        Batch.objects.filter(id=self.batch.id).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        record_correction(self.batch, Decimal("500"), "found a pitcher")

        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, BatchStatus.DEPLETED)

    def test_order_consumes_earliest_expiring_batch_first(self):
        tea = self.data["tea"]

        # Started two days ago, so it expires about a day before the batch from make_shop
        older = create_batch(
            shop=self.data["shop"],
            prepared_item=tea,
            storage_location=self.data["location"],
            batch_fraction=Decimal("1"),
            started_at=timezone.now() - timedelta(days=2)
        )
        mark_batch_ready(older)

        create_order(self.data["shop"], order_items(self.data["menu_item"], 1))

        self.assertEqual(get_batch_balance(older), Decimal("3500"))
        self.assertEqual(get_batch_balance(self.batch), Decimal("4000"))

    def test_consumption_events_point_to_their_order_item(self):
        order, _ = create_order(
            self.data["shop"],
            order_items(self.data["menu_item"], 1, 2)
        )

        events = InventoryEvent.objects.filter(event_type=EventType.ORDER_CONSUMPTION)

        self.assertEqual(events.count(), 2)
        self.assertFalse(events.filter(order_item__isnull=True).exists())

        for order_item in order.order_items.all():
            event = events.get(order_item=order_item)
            self.assertEqual(event.quantity_delta, Decimal("-500") * order_item.quantity)

    def test_inventory_events_cannot_be_changed_or_deleted(self):
        event = self.batch.inventory_events.get()

        event.quantity_delta = Decimal("999999")

        with self.assertRaises(ImmutableEventError):
            event.save()

        with self.assertRaises(ImmutableEventError):
            event.delete()

        event.refresh_from_db()
        self.assertEqual(event.quantity_delta, Decimal("4000"))

    def test_low_stock_warning_uses_shop_threshold(self):
        shop = self.data["shop"]
        menu_item = self.data["menu_item"]

        # After one drink: 3500 ml, minus the 10% buffer, is 6 servings of 500 ml
        shop.low_stock_threshold_servings = 7
        shop.save()

        _, warnings = create_order(shop, order_items(menu_item, 1))
        self.assertEqual(len(warnings), 1)
        self.assertIn("Black Tea", warnings[0])

        # After two drinks: 5 servings, which is not below a threshold of 5
        shop.low_stock_threshold_servings = 5
        shop.save()

        _, warnings = create_order(shop, order_items(menu_item, 1))
        self.assertEqual(warnings, [])


# Uses real transactions, so each thread's row locks actually block the other thread
@skipUnlessDBFeature("has_select_for_update")
class ConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.data = make_shop("Pearl House", "owner@pearl.test")
        self.batch = self.data["batch"]

    # Run the same function in two threads that start together
    def run_twice_at_once(self, function):
        barrier = threading.Barrier(2)
        results = []

        def worker():
            try:
                barrier.wait()
                function()
                results.append("ok")
            except ValueError:
                results.append("rejected")
            finally:
                # Each thread opens its own database connection
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=30)

        return results

    def test_two_orders_for_the_last_serving(self):
        # Leave exactly one 500 ml serving in the only batch
        record_correction(self.batch, Decimal("-3500"), "leave one serving")

        results = self.run_twice_at_once(
            lambda: create_order(self.data["shop"], order_items(self.data["menu_item"], 1))
        )

        self.assertEqual(sorted(results), ["ok", "rejected"])
        self.assertEqual(get_batch_balance(self.batch), Decimal("0"))
        self.assertEqual(Order.objects.filter(order_items__isnull=False).distinct().count(), 1)

    def test_two_requests_expire_the_same_batch(self):
        results = self.run_twice_at_once(
            lambda: expire_batch(Batch.objects.get(id=self.batch.id))
        )

        self.assertEqual(results, ["ok", "ok"])
        self.assertEqual(
            self.batch.inventory_events.filter(event_type=EventType.EXPIRY).count(),
            1
        )
        self.assertEqual(get_batch_balance(self.batch), Decimal("0"))

    # Run a function in many threads that start together, each calling it several times
    def run_many_at_once(self, function, thread_count, attempts_per_thread):
        barrier = threading.Barrier(thread_count)
        results = []

        # Only one thread at a time may add to the shared results list
        results_lock = threading.Lock()

        def worker():
            try:
                barrier.wait()

                for _ in range(attempts_per_thread):
                    try:
                        function()
                        result = "ok"
                    except ValueError:
                        result = "rejected"

                    with results_lock:
                        results.append(result)
            finally:
                # Each thread opens its own database connection
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(thread_count)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=60)

        return results

    def test_rush_never_oversells(self):
        SERVINGS_IN_STOCK = 100
        THREAD_COUNT = 20
        ATTEMPTS_PER_THREAD = 10

        SERVING_ML = Decimal("500")
        TOTAL_ATTEMPTS = THREAD_COUNT * ATTEMPTS_PER_THREAD
        STOCK_ML = SERVINGS_IN_STOCK * SERVING_ML

        # make_shop creates one empty order of its own during setup
        ORDERS_FROM_SETUP = 1

        # The batch starts at 4,000 ml, so add the difference to reach exactly 50,000 ml
        record_correction(
            self.batch,
            STOCK_ML - get_batch_balance(self.batch),
            "stock up for the rush"
        )
        self.assertEqual(get_batch_balance(self.batch), STOCK_ML)

        results = self.run_many_at_once(
            lambda: create_order(self.data["shop"], order_items(self.data["menu_item"], 1)),
            THREAD_COUNT,
            ATTEMPTS_PER_THREAD
        )

        # Every attempt finished, and each one either sold a drink or was turned away
        self.assertEqual(len(results), TOTAL_ATTEMPTS)
        self.assertEqual(results.count("ok"), SERVINGS_IN_STOCK)
        self.assertEqual(results.count("rejected"), TOTAL_ATTEMPTS - SERVINGS_IN_STOCK)

        # Exactly sold out, never below zero
        self.assertEqual(get_batch_balance(self.batch), Decimal("0"))

        consumed = self.batch.inventory_events.filter(
            event_type=EventType.ORDER_CONSUMPTION
        ).aggregate(
            total=Sum("quantity_delta")
        )["total"]
        self.assertEqual(consumed, -STOCK_ML)

        # Rejected orders were rolled back completely, so no empty Order rows were left behind
        self.assertEqual(
            Order.objects.filter(order_items__isnull=False).distinct().count(),
            SERVINGS_IN_STOCK
        )
        self.assertEqual(Order.objects.count(), SERVINGS_IN_STOCK + ORDERS_FROM_SETUP)


# A depleted batch that holds past sales, so the history doesn't change the shop's current inventory
def make_history_batch(data):
    now = timezone.now()

    return Batch.objects.create(
        prepared_item=data["tea"],
        storage_location=data["location"],
        initial_quantity=Decimal("0"),
        status=BatchStatus.DEPLETED,
        started_at=now - timedelta(days=10),
        expires_at=now - timedelta(days=9)
    )


# Record order usage at a past time
def record_usage(batch, quantity, when):
    event = InventoryEvent.objects.create(
        batch=batch,
        event_type=EventType.ORDER_CONSUMPTION,
        quantity_delta=-Decimal(quantity)
    )

    # Bulk update is only used here to backdate test data, since created_at is set automatically
    InventoryEvent.objects.filter(pk=event.pk).update(created_at=when)


class RecommenderTests(TestCase):
    def setUp(self):
        self.data = make_shop("Pearl House", "owner@pearl.test")
        self.tea = self.data["tea"]
        self.history = make_history_batch(self.data)
        self.now = timezone.now()

    def test_same_hours_usage_averages_past_days_and_ignores_other_hours(self):
        record_usage(self.history, "700", self.now - timedelta(days=1) + timedelta(hours=1))
        record_usage(self.history, "700", self.now - timedelta(days=2) + timedelta(minutes=30))

        # Outside the 2-hour window on those days
        record_usage(self.history, "5000", self.now - timedelta(days=1) + timedelta(hours=3))
        record_usage(self.history, "5000", self.now - timedelta(days=1) - timedelta(hours=1))

        # 1400 over 7 days
        self.assertEqual(get_same_hours_usage(self.tea), Decimal("200"))

    def test_forecast_demand_falls_back_to_trailing_rate(self):
        record_usage(self.history, "800", self.now - timedelta(hours=1))

        self.assertEqual(get_same_hours_usage(self.tea), Decimal("0"))

        # 800 over 4 hours is 200 an hour, for 2 hours, plus the 10% buffer
        self.assertEqual(forecast_demand(self.tea), Decimal("440"))

    def test_recommends_batch_when_past_days_were_busy_but_last_hours_quiet(self):
        for day in range(1, 8):
            record_usage(self.history, "7000", self.now - timedelta(days=day) + timedelta(hours=1))

        # 7000 expected plus the 10% buffer, minus the 4000 ready
        self.assertEqual(recommend_production(self.tea), Decimal("3700"))

    def test_start_by_subtracts_prep_and_cooling(self):
        self.tea.cooling_time = timedelta(minutes=20)
        self.tea.save()

        for day in range(1, 8):
            record_usage(self.history, "1000", self.now - timedelta(days=day) + timedelta(hours=1))

        before = timezone.now()
        start_time = get_start_by(self.tea)
        after = timezone.now()

        # 1000 over 2 hours plus the buffer is 550 an hour, so 4000 lasts 4000 / 550 hours
        hours_left = timedelta(hours=4000 / 550)
        lead_time = self.tea.preparation_time + self.tea.cooling_time

        self.assertGreaterEqual(start_time, before + hours_left - lead_time - timedelta(seconds=1))
        self.assertLessEqual(start_time, after + hours_left - lead_time + timedelta(seconds=1))

    def test_start_by_is_none_with_no_demand(self):
        self.assertIsNone(get_start_by(self.tea))


class RecommendationsApiTests(APITestCase):
    def test_includes_start_by_and_only_shows_own_shop(self):
        a = make_shop("Shop A", "a@shop.test")
        make_shop("Shop B", "b@shop.test")

        self.client.force_login(a["user"])
        response = self.client.get("/api/recommendations/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data], [a["tea"].id])
        self.assertIn("start_by", response.data[0])
        self.assertIsNone(response.data[0]["start_by"])


class BatchLedgerApiTests(APITestCase):
    def setUp(self):
        self.data = make_shop("Pearl House", "owner@pearl.test")
        self.batch = self.data["batch"]
        self.client.force_login(self.data["user"])

    def test_events_are_newest_first_with_order_id(self):
        order, _ = create_order(self.data["shop"], order_items(self.data["menu_item"], 1))

        self.client.post(
            f"/api/batches/{self.batch.id}/waste/",
            {"quantity": "100", "reason": "spilled"},
            format="json"
        )

        response = self.client.get(f"/api/batches/{self.batch.id}/events/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(response.data["balance"])), Decimal("3400"))
        self.assertEqual(response.data["status"], BatchStatus.READY)

        events = response.data["events"]

        self.assertEqual(
            [event["event_type"] for event in events],
            [EventType.WASTE, EventType.ORDER_CONSUMPTION, EventType.BATCH_CREATED]
        )
        self.assertEqual(
            [event["order_id"] for event in events],
            [None, order.id, None]
        )
        self.assertEqual(events[0]["reason"], "spilled")

    def test_events_for_other_shops_batch_return_404(self):
        other = make_shop("Shop B", "b@shop.test")

        response = self.client.get(f"/api/batches/{other['batch'].id}/events/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_wasting_whole_balance_depletes_batch(self):
        response = self.client.post(
            f"/api/batches/{self.batch.id}/waste/",
            {"quantity": "4000", "reason": "dropped the pitcher"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], BatchStatus.DEPLETED)

        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, BatchStatus.DEPLETED)

    def test_waste_larger_than_balance_returns_400(self):
        response = self.client.post(
            f"/api/batches/{self.batch.id}/waste/",
            {"quantity": "4000.5", "reason": "too much"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_correction_that_goes_negative_returns_400(self):
        response = self.client.post(
            f"/api/batches/{self.batch.id}/correction/",
            {"quantity": "-5000", "reason": "recount"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Correction would make the batch balance negative.")
        self.assertEqual(get_batch_balance(self.batch), Decimal("4000"))


INGREDIENT = {
    "name": "Thai Tea",
    "base_unit": "ml",
    "default_batch_quantity": "4000",
    "quantity_per_serving": "500",
    "preparation_time": 20,
    "cooling_time": 30,
    "default_shelf_life": 4320,
    "requires_cooling": True,
    "is_topping": False,
    "is_active": True,
}


class MenuApiTests(APITestCase):
    def setUp(self):
        self.data = make_shop("Pearl House", "owner@pearl.test")
        self.client.force_login(self.data["user"])

    def test_create_and_edit_ingredient_with_minutes(self):
        response = self.client.post("/api/menu/ingredients/", INGREDIENT, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["preparation_time"], 20)
        self.assertEqual(response.data["cooling_time"], 30)
        self.assertEqual(response.data["default_shelf_life"], 4320)

        item = PreparedItem.objects.get(id=response.data["id"])
        self.assertEqual(item.shop, self.data["shop"])
        self.assertEqual(item.preparation_time, timedelta(minutes=20))
        self.assertEqual(item.default_shelf_life, timedelta(days=3))

        response = self.client.put(
            f"/api/menu/ingredients/{item.id}/",
            {**INGREDIENT, "name": "Thai Tea Concentrate", "preparation_time": 25, "requires_cooling": False},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Thai Tea Concentrate")
        self.assertEqual(response.data["preparation_time"], 25)

        # Turning off cooling clears the cooling time
        self.assertEqual(response.data["cooling_time"], 0)

    def test_ingredient_rejects_non_positive_numbers(self):
        response = self.client.post(
            "/api/menu/ingredients/",
            {**INGREDIENT, "quantity_per_serving": "0", "default_shelf_life": 0},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity_per_serving", response.data)
        self.assertIn("default_shelf_life", response.data)

    def test_duplicate_names_return_400(self):
        response = self.client.post(
            "/api/menu/ingredients/",
            {**INGREDIENT, "name": "black tea"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already have an ingredient", str(response.data["name"][0]))

        response = self.client.post(
            "/api/menu/drinks/",
            {"name": "Black Tea", "is_active": True, "recipe": [{"prepared_item_id": self.data["tea"].id, "quantity": "500"}]},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_create_and_edit_drink_replaces_recipe(self):
        pearls = PreparedItem.objects.create(
            shop=self.data["shop"],
            name="Tapioca Pearls",
            base_unit=Unit.GRAM,
            default_batch_quantity=Decimal("2000"),
            quantity_per_serving=Decimal("60"),
            preparation_time=timedelta(minutes=45),
            default_shelf_life=timedelta(hours=4),
            is_topping=True
        )

        response = self.client.post(
            "/api/menu/drinks/",
            {
                "name": "Black Milk Tea",
                "is_active": True,
                "recipe": [
                    {"prepared_item_id": self.data["tea"].id, "quantity": "400"},
                    {"prepared_item_id": pearls.id, "quantity": "60"},
                ],
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        drink = MenuItem.objects.get(id=response.data["id"])
        self.assertEqual(drink.recipe_components.count(), 2)

        response = self.client.put(
            f"/api/menu/drinks/{drink.id}/",
            {
                "name": "Black Milk Tea",
                "is_active": True,
                "recipe": [{"prepared_item_id": self.data["tea"].id, "quantity": "450"}],
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [(row.prepared_item_id, row.quantity) for row in drink.recipe_components.all()],
            [(self.data["tea"].id, Decimal("450"))]
        )

    def test_drink_needs_a_recipe_without_repeats(self):
        tea_row = {"prepared_item_id": self.data["tea"].id, "quantity": "500"}

        empty = self.client.post("/api/menu/drinks/", {"name": "Air", "recipe": []}, format="json")
        repeated = self.client.post("/api/menu/drinks/", {"name": "Double", "recipe": [tea_row, tea_row]}, format="json")

        self.assertEqual(empty.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(repeated.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recipe_cannot_use_other_shops_ingredient(self):
        other = make_shop("Shop B", "b@shop.test")

        response = self.client.post(
            "/api/menu/drinks/",
            {"name": "Stolen Tea", "recipe": [{"prepared_item_id": other["tea"].id, "quantity": "500"}]},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("recipe", response.data)
        self.assertFalse(MenuItem.objects.filter(name="Stolen Tea").exists())

    def test_cannot_edit_other_shops_items(self):
        other = make_shop("Shop B", "b@shop.test")

        ingredient = self.client.patch(f"/api/menu/ingredients/{other['tea'].id}/", {"is_active": False}, format="json")
        drink = self.client.patch(f"/api/menu/drinks/{other['menu_item'].id}/", {"is_active": False}, format="json")

        self.assertEqual(ingredient.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(drink.status_code, status.HTTP_404_NOT_FOUND)

    def test_inactive_items_are_hidden_from_order_and_batch_lists(self):
        self.client.patch(f"/api/menu/ingredients/{self.data['tea'].id}/", {"is_active": False}, format="json")
        self.client.patch(f"/api/menu/drinks/{self.data['menu_item'].id}/", {"is_active": False}, format="json")

        self.assertEqual(self.client.get("/api/prepared-items/").data, [])
        self.assertEqual(self.client.get("/api/menu-items/").data, [])

        # Pages that show names for old batches and orders can still ask for them
        self.assertEqual(len(self.client.get("/api/prepared-items/?include_inactive=true").data), 1)
        self.assertEqual(len(self.client.get("/api/menu-items/?include_inactive=true").data), 1)

        # The Menu page still lists everything
        self.assertEqual(len(self.client.get("/api/menu/ingredients/").data), 1)
        self.assertEqual(len(self.client.get("/api/menu/drinks/").data), 1)

    def test_toppings_only_include_active_topping_ingredients(self):
        for name, is_topping, is_active in [
            ("Tapioca Pearls", True, True),
            ("Grass Jelly", True, False),
            ("Brown Sugar Syrup", False, True),
        ]:
            PreparedItem.objects.create(
                shop=self.data["shop"],
                name=name,
                base_unit=Unit.GRAM,
                default_batch_quantity=Decimal("1000"),
                quantity_per_serving=Decimal("50"),
                preparation_time=timedelta(minutes=30),
                default_shelf_life=timedelta(hours=4),
                is_topping=is_topping,
                is_active=is_active
            )

        response = self.client.get("/api/toppings/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["name"] for row in response.data], ["Tapioca Pearls"])


class RegistrationSetupTests(APITestCase):
    def test_new_shop_gets_main_refrigerator(self):
        cache.clear()

        response = self.client.post(
            "/api/auth/register/",
            {"shop_name": "Fresh Start Tea", "email": "new@fresh.test", "password": PASSWORD},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        shop = Shop.objects.get(id=response.data["shop"]["id"])
        self.assertEqual(
            list(shop.storage_locations.values_list("name", "location_type")),
            [("Main Refrigerator", LocationType.REFRIGERATOR)]
        )


class OrdersListTests(APITestCase):
    def setUp(self):
        # make_shop also creates one pending order, placed today
        self.data = make_shop("Pearl House", "owner@pearl.test")
        self.client.force_login(self.data["user"])

    # Create an order for the shop, moved to a past time if one is given
    def make_order(self, status, when=None):
        order = Order.objects.create(shop=self.data["shop"], status=status)

        if when is not None:
            # Bulk update is only used here to backdate test data, since created_at is set automatically
            Order.objects.filter(pk=order.pk).update(created_at=when)

        return order

    def test_lists_todays_orders_and_older_pending_orders(self):
        three_days_ago = timezone.now() - timedelta(days=3)

        completed_today = self.make_order(OrderStatus.COMPLETED)
        pending_earlier = self.make_order(OrderStatus.PENDING, three_days_ago)
        completed_earlier = self.make_order(OrderStatus.COMPLETED, three_days_ago)
        other_shops_order = make_shop("Shop B", "b@shop.test")["order"]

        response = self.client.get("/api/orders/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [order["id"] for order in response.data]

        self.assertEqual(
            set(ids),
            {self.data["order"].id, completed_today.id, pending_earlier.id}
        )
        self.assertNotIn(completed_earlier.id, ids)
        self.assertNotIn(other_shops_order.id, ids)

        # Newest first, so the order from three days ago comes last
        self.assertEqual(ids, [completed_today.id, self.data["order"].id, pending_earlier.id])

    def test_query_count_does_not_grow_with_orders(self):
        pearls = PreparedItem.objects.create(
            shop=self.data["shop"],
            name="Tapioca Pearls",
            base_unit=Unit.GRAM,
            default_batch_quantity=Decimal("2000"),
            quantity_per_serving=Decimal("60"),
            preparation_time=timedelta(minutes=45),
            default_shelf_life=timedelta(hours=4),
            is_topping=True
        )

        # Ten orders with two drinks each, and a topping on every drink
        for _ in range(10):
            order = self.make_order(OrderStatus.COMPLETED)

            for _ in range(2):
                order_item = OrderItem.objects.create(order=order, menu_item=self.data["menu_item"])
                OrderItemTopping.objects.create(order_item=order_item, prepared_item=pearls)

        # Session, user, shop, then one query each for orders, their items, and the items' toppings.
        # Without prefetch_related this would be one more query per order and per drink (30 more here).
        with self.assertNumQueries(6):
            response = self.client.get("/api/orders/")

        self.assertEqual(len(response.data), 11)
        self.assertEqual(len(response.data[0]["order_items"]), 2)
        self.assertEqual(len(response.data[0]["order_items"][0]["toppings"]), 1)


# Most refresh tests skip the order history, which plans three weeks of orders, to keep the suite fast
NO_HISTORY = patch("operations.services.demo.seed_order_history", return_value=0)


class DemoRefreshTests(TestCase):
    def setUp(self):
        self.data = make_shop("BubbleFlow Demo", DEMO_EMAIL)
        self.tea = self.data["tea"]

        # Use up the starting batch, and add one that already expired
        self.starting_batch = self.data["batch"]
        self.starting_batch.status = BatchStatus.DEPLETED
        self.starting_batch.save()

        Batch.objects.create(
            prepared_item=self.tea,
            storage_location=self.data["location"],
            initial_quantity=Decimal("4000"),
            status=BatchStatus.EXPIRED,
            started_at=timezone.now() - timedelta(days=4),
            expires_at=timezone.now() - timedelta(days=1)
        )

    def ready_batches(self):
        return Batch.objects.filter(prepared_item=self.tea, status=BatchStatus.READY)

    def test_creates_ready_batch_when_only_depleted_or_expired_batches_exist(self):
        with NO_HISTORY:
            restocked, _ = refresh_demo_shop(self.data["shop"])

        self.assertEqual(restocked, ["Black Tea"])
        self.assertEqual(self.ready_batches().count(), 1)
        self.assertEqual(get_item_inventory(self.tea), self.tea.default_batch_quantity)

    def test_running_twice_creates_no_duplicates(self):
        refresh_demo_shop(self.data["shop"])

        counts = (Batch.objects.count(), Order.objects.count(), InventoryEvent.objects.count())

        restocked, added_orders = refresh_demo_shop(self.data["shop"])

        self.assertEqual((restocked, added_orders), ([], 0))
        self.assertEqual((Batch.objects.count(), Order.objects.count(), InventoryEvent.objects.count()), counts)
        self.assertEqual(self.ready_batches().count(), 1)

    def test_demo_login_leaves_every_active_item_with_stock(self):
        # An ingredient with no batches at all should be stocked too
        PreparedItem.objects.create(
            shop=self.data["shop"],
            name="Tapioca Pearls",
            base_unit=Unit.GRAM,
            default_batch_quantity=Decimal("2000"),
            quantity_per_serving=Decimal("60"),
            preparation_time=timedelta(minutes=45),
            default_shelf_life=timedelta(hours=4),
            is_topping=True
        )

        with NO_HISTORY:
            response = self.client.post("/api/auth/demo-login/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for item in PreparedItem.objects.filter(shop=self.data["shop"], is_active=True):
            with self.subTest(item=item.name):
                self.assertGreaterEqual(get_item_inventory(item), item.default_batch_quantity)


class BatchesListTests(APITestCase):
    def setUp(self):
        self.data = make_shop("Pearl House", "owner@pearl.test")
        self.client.force_login(self.data["user"])

    # Create a batch for the shop's tea with a given status and expiry
    def make_batch(self, status, expires_at):
        return Batch.objects.create(
            prepared_item=self.data["tea"],
            storage_location=self.data["location"],
            initial_quantity=Decimal("4000"),
            status=status,
            started_at=expires_at - timedelta(days=3),
            expires_at=expires_at
        )

    def test_default_list_skips_old_history(self):
        now = timezone.now()

        ready = self.data["batch"]
        depleted = self.make_batch(BatchStatus.DEPLETED, now - timedelta(days=5))
        expired_long_ago = self.make_batch(BatchStatus.EXPIRED, now - timedelta(days=3))
        expired_recently = self.make_batch(BatchStatus.EXPIRED, now - timedelta(hours=2))

        preparing = create_batch(
            shop=self.data["shop"],
            prepared_item=self.data["tea"],
            storage_location=self.data["location"],
            batch_fraction=Decimal("1"),
            started_at=now
        )

        response = self.client.get("/api/batches/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {batch["id"] for batch in response.data},
            {ready.id, expired_recently.id, preparing.id}
        )

        # The balance comes from the annotation and still matches the ledger
        ready_row = next(batch for batch in response.data if batch["id"] == ready.id)
        self.assertEqual(Decimal(str(ready_row["balance"])), Decimal("4000"))

        history = self.client.get("/api/batches/?include_history=true")

        self.assertEqual(
            {batch["id"] for batch in history.data},
            {ready.id, depleted.id, expired_long_ago.id, expired_recently.id, preparing.id}
        )

    def test_query_count_does_not_grow_with_batches(self):
        now = timezone.now()

        for _ in range(10):
            batch = create_batch(
                shop=self.data["shop"],
                prepared_item=self.data["tea"],
                storage_location=self.data["location"],
                batch_fraction=Decimal("1"),
                started_at=now - self.data["tea"].preparation_time
            )
            mark_batch_ready(batch)

        for _ in range(30):
            self.make_batch(BatchStatus.DEPLETED, now - timedelta(days=5))

        # Session, user, shop, the batches whose status may change, then the list with every balance
        with self.assertNumQueries(5):
            response = self.client.get("/api/batches/")

        self.assertEqual(len(response.data), 11)
