from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Category, MenuItem

MENU_URL = "/api/v1/menu/"

PAYLOAD = {
    "categories": [
        {
            "slug": "grill",
            "name": "Шашлыки и гриль",
            "description": "Мясо на углях и мангал",
            "order": 1,
            "items": [
                {"name": "Шашлык из баранины", "description": "Маринованная баранина",
                 "weight": "150 г", "price": "290", "is_popular": True},
                {"name": "Овощи на гриле", "description": "Перец, баклажан",
                 "weight": "200 г", "price": "150", "is_new": True},
            ],
        },
        {
            "slug": "drinks",
            "name": "Напитки",
            "order": 9,
            "items": [
                {"name": "Чай в чайнике", "weight": "0.7 л", "price": "120"},
            ],
        },
    ]
}


def staff_client():
    user = get_user_model().objects.create_user(username="manager", password="x",
                                                is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")
    return client


class MenuImportTests(TestCase):
    def test_import_creates_categories_and_items(self):
        response = staff_client().post(MENU_URL, PAYLOAD, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            "categories_created": 2, "categories_updated": 0,
            "items_created": 3, "items_updated": 0,
        })
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(MenuItem.objects.count(), 3)
        self.assertEqual(MenuItem.objects.get(name="Шашлык из баранины").price, 290)

    def test_reimport_updates_instead_of_duplicating(self):
        client = staff_client()
        client.post(MENU_URL, PAYLOAD, format="json")
        changed = {"categories": [{
            "slug": "grill", "name": "Шашлыки и гриль",
            "items": [{"name": "Шашлык из баранины", "price": "320"}],
        }]}
        response = client.post(MENU_URL, changed, format="json")

        self.assertEqual(response.data["categories_created"], 0)
        self.assertEqual(response.data["categories_updated"], 1)
        self.assertEqual(response.data["items_created"], 0)
        self.assertEqual(response.data["items_updated"], 1)
        self.assertEqual(MenuItem.objects.count(), 3)
        self.assertEqual(MenuItem.objects.get(name="Шашлык из баранины").price, 320)

    def test_import_requires_staff(self):
        anonymous = APIClient()
        self.assertEqual(anonymous.post(MENU_URL, PAYLOAD, format="json").status_code, 401)

        guest = APIClient()
        user = get_user_model().objects.create_user(username="guest", password="x")
        guest.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")
        self.assertEqual(guest.post(MENU_URL, PAYLOAD, format="json").status_code, 403)

    def test_get_menu_still_public_and_nested(self):
        staff_client().post(MENU_URL, PAYLOAD, format="json")

        response = APIClient().get(MENU_URL)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([c["slug"] for c in response.data], ["grill", "drinks"])
        self.assertEqual(len(response.data[0]["items"]), 2)
        self.assertEqual(response.data[0]["items"][0]["price"], 290)
