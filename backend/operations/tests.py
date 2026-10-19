# Tests for shop registration, login, and keeping each shop's data separate.
# Run with: python manage.py test operations
from datetime import timedelta
from decimal import Decimal
import threading

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
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
    mark_batch_ready,
    record_correction,
)
from .services.orders import create_order


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
