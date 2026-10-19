# Tests for shop registration, login, and keeping each shop's data separate.
# Run with: python manage.py test operations
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .auth_views import DEMO_EMAIL
from .models import (
    Batch,
    BatchStatus,
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
from .services.inventory import create_batch, mark_batch_ready


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
