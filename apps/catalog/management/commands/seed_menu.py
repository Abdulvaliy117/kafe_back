"""Наполняет меню базовыми категориями и блюдами.

    python manage.py seed_menu          # добавить/обновить
    python manage.py seed_menu --reset  # сначала очистить меню

Цены — ориентировочные для Оша, их правят в /admin/.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, MenuItem, SiteInfo

CATEGORIES = [
    ("grill", "Шашлыки и гриль", "Мясо на углях и мангал", 1),
    ("burgers", "Бургеры", "Сочные бургеры с картофелем", 2),
    ("shawarma", "Шаурма и донер", "Быстрая и сытная классика", 3),
    ("pizza", "Пицца", "Готовим в дровяной печи", 4),
    ("soups", "Первые блюда", "Горячие супы и шорпо", 5),
    ("salads", "Салаты", "Свежие овощи и зелень", 6),
    ("snacks", "Закуски", "К пиву и просто так", 7),
    ("bakery", "Выпечка", "Самса, лепёшки, хачапури", 8),
    ("drinks", "Напитки", "Чай, кофе и прохладительные", 9),
    ("desserts", "Десерты", "Сладкое к чаю", 10),
]

ITEMS = {
    "grill": [
        ("Шашлык из баранины", "Маринованная баранина, лук, свежая зелень", "150 г", 290, True, False),
        ("Шашлык из говядины", "Сочная говядина на углях", "150 г", 260, True, False),
        ("Люля-кебаб", "Рубленое мясо с пряностями, лепёшка", "160 г", 240, True, False),
        ("Куриные крылышки на гриле", "Пикантный маринад, соус на выбор", "250 г", 220, False, False),
        ("Шашлык из курицы", "Нежное куриное филе", "150 г", 200, False, False),
        ("Овощи на гриле", "Перец, баклажан, помидор, лук", "200 г", 150, False, True),
    ],
    "burgers": [
        ("Бургер Осман", "Говяжья котлета, сыр, соус кафе, картофель фри", "1 шт", 280, True, False),
        ("Чизбургер", "Говядина, чеддер, огурчики, горчичный соус", "1 шт", 240, False, False),
        ("Чикен-бургер", "Куриная котлета, салат, томат, соус", "1 шт", 220, False, False),
        ("Двойной бургер", "Две котлеты, двойной сыр, картофель фри", "1 шт", 380, False, True),
    ],
    "shawarma": [
        ("Шаурма с курицей", "Лаваш, курица, овощи, фирменный соус", "350 г", 210, True, False),
        ("Шаурма с говядиной", "Лаваш, говядина, овощи, соус", "380 г", 250, True, False),
        ("Донер в лепёшке", "Мясо, овощи, зелень", "1 шт", 230, False, False),
    ],
    "pizza": [
        ("Пицца Маргарита", "Томатный соус, моцарелла, базилик", "30 см", 420, False, False),
        ("Пицца Пепперони", "Пепперони, моцарелла, томатный соус", "30 см", 480, True, False),
        ("Пицца Мясная", "Говядина, курица, колбаски, сыр", "30 см", 550, False, False),
        ("Пицца с курицей и грибами", "Курица, шампиньоны, сливочный соус", "30 см", 520, False, True),
    ],
    "soups": [
        ("Шорпо", "Наваристый бараний бульон, картофель, зелень", "400 мл", 220, True, False),
        ("Лагман", "Домашняя лапша, говядина, овощи", "400 мл", 260, True, False),
        ("Суп-лапша с курицей", "Лёгкий куриный бульон", "400 мл", 180, False, False),
        ("Борщ", "Со сметаной и пампушкой", "400 мл", 200, False, False),
    ],
    "salads": [
        ("Салат Ачичук", "Помидор, лук, острый перец, зелень", "200 г", 120, False, False),
        ("Цезарь с курицей", "Романо, курица, сухарики, соус", "250 г", 260, True, False),
        ("Оливье", "Классический с майонезом", "220 г", 180, False, False),
        ("Свежий овощной", "Огурцы, помидоры, зелень, сметана", "200 г", 150, False, False),
    ],
    "snacks": [
        ("Картофель фри", "Хрустящий, с соусом", "150 г", 130, True, False),
        ("Наггетсы", "Куриные, 6 шт, соус", "120 г", 160, False, False),
        ("Сырные палочки", "Моцарелла в панировке", "120 г", 180, False, True),
        ("Куриные крылышки", "Острые, с соусом барбекю", "250 г", 220, False, False),
    ],
    "bakery": [
        ("Самса с бараниной", "Тандырная, сочная", "1 шт", 90, True, False),
        ("Самса с курицей", "Тандырная", "1 шт", 80, False, False),
        ("Хачапури по-аджарски", "С сыром и яйцом", "1 шт", 240, False, True),
        ("Лепёшка тандырная", "Свежая, горячая", "1 шт", 40, False, False),
    ],
    "drinks": [
        ("Чай в чайнике", "Чёрный / зелёный с вареньем", "0.7 л", 120, True, False),
        ("Кофе Latte", "Эспрессо с молоком", "300 мл", 130, False, False),
        ("Компот домашний", "Из сухофруктов", "300 мл", 70, False, False),
        ("Лимонад", "Домашний, цитрус-мята", "400 мл", 110, False, True),
        ("Кола / Спрайт", "В бутылке", "0.5 л", 90, False, False),
        ("Айран", "Освежающий кисломолочный", "300 мл", 70, False, False),
    ],
    "desserts": [
        ("Медовик", "Домашний медовый торт", "1 шт", 150, True, False),
        ("Пахлава", "С орехами и мёдом", "1 шт", 90, False, False),
        ("Мороженое", "Ванильное, 2 шарика", "120 г", 100, False, False),
    ],
}


class Command(BaseCommand):
    help = "Заполняет меню Осман Кафе базовыми категориями и блюдами."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Удалить текущее меню перед заливкой")
        parser.add_argument("--if-empty", action="store_true",
                            help="Ничего не делать, если блюда уже есть (для деплоя)")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["if_empty"] and MenuItem.objects.exists():
            self.stdout.write("Блюда уже есть — пропускаю наполнение.")
            return

        if options["reset"]:
            # Заказы не трогаем: позиции хранят снимок названия и цены.
            MenuItem.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Меню очищено."))

        cat_by_slug = {}
        for slug, name, desc, order in CATEGORIES:
            cat, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "description": desc, "order": order, "is_active": True})
            cat_by_slug[slug] = cat

        created = updated = 0
        for slug, rows in ITEMS.items():
            cat = cat_by_slug[slug]
            for i, (name, desc, weight, price, popular, new) in enumerate(rows, start=1):
                _, was_created = MenuItem.objects.update_or_create(
                    category=cat, name=name,
                    defaults={"description": desc, "weight": weight, "price": price,
                              "is_popular": popular, "is_new": new,
                              "is_available": True, "order": i})
                created += was_created
                updated += not was_created

        site = SiteInfo.get_solo()
        self.stdout.write(self.style.SUCCESS(
            f"Готово: категорий {len(CATEGORIES)}, блюд создано {created}, "
            f"обновлено {updated}."))
        self.stdout.write(f"Номер WhatsApp для заказов: {site.effective_whatsapp()} "
                          f"(меняется в /admin/ → «Контакты и доставка»)")
