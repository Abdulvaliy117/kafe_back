from django.db import models


def item_image_path(instance, filename):
    return f"menu/{instance.category.slug if instance.category else 'other'}/{filename}"


class Category(models.Model):
    """Категория меню: шашлыки, напитки и т.п. Менеджер заводит в /admin/."""

    slug = models.SlugField("Слаг", unique=True)
    name = models.CharField("Название", max_length=120)
    description = models.CharField("Описание", max_length=255, blank=True)
    emoji = models.CharField("Иконка (эмодзи, необязательно)", max_length=8, blank=True)
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Категория меню"
        verbose_name_plural = "Категории меню"

    def __str__(self):
        return self.name or self.slug


class MenuItem(models.Model):
    """Блюдо/напиток. Цена хранится в сомах (KGS), целое число без копеек."""

    category = models.ForeignKey(Category, on_delete=models.PROTECT,
                                 related_name="items", verbose_name="Категория")
    name = models.CharField("Название", max_length=160)
    description = models.TextField("Описание", max_length=600, blank=True)
    weight = models.CharField("Вес/объём", max_length=40, blank=True,
                              help_text="Например: 250 г, 0.5 л")
    price = models.DecimalField("Цена, сом", max_digits=10, decimal_places=2)
    old_price = models.DecimalField("Старая цена, сом", max_digits=10, decimal_places=2,
                                    null=True, blank=True,
                                    help_text="Если указана — на карточке зачёркнута")
    image = models.ImageField("Фото", upload_to=item_image_path, blank=True)
    is_popular = models.BooleanField("Хит", default=False)
    is_new = models.BooleanField("Новинка", default=False)
    is_available = models.BooleanField("В наличии", default=True)
    order = models.PositiveIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Блюдо"
        verbose_name_plural = "Меню (блюда)"
        indexes = [
            models.Index(fields=["category", "is_available"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.price} сом)"

    @property
    def is_discounted(self):
        return bool(self.old_price and self.old_price > self.price)


class SiteInfo(models.Model):
    """Единственная запись: контакты кафе и настройки доставки. Правки в /admin/."""

    name = models.CharField("Название", max_length=120, default="Осман Кафе")
    tagline = models.CharField("Слоган", max_length=200, blank=True,
                               default="Аш борбору в Оше — вкусно, сытно и по-домашнему")
    about = models.TextField("О кафе", max_length=1000, blank=True,
                             default="Осман — аш борбору в Оше. Готовим шашлыки на углях, "
                                     "шурпу, лагман, бургеры и домашнюю выпечку. Заказ можно "
                                     "оформить онлайн и забрать самому или заказать доставку по городу.")
    phone = models.CharField("Телефон (для показа)", max_length=40, blank=True,
                             default="0550 75 75 74")
    whatsapp_number = models.CharField(
        "WhatsApp номер (только цифры)", max_length=20, blank=True,
        help_text="Формат: 996XXXXXXXXX. Если пусто — берётся WHATSAPP_NUMBER из .env")
    instagram = models.URLField("Instagram", max_length=255, blank=True,
                                default="https://www.instagram.com/osman_kafe_osh/")
    address = models.CharField("Адрес", max_length=255, blank=True,
                               default="ул. Алымбека датки, 938 (ориентир — круг Достук), г. Ош")
    work_hours = models.CharField("Часы работы", max_length=160, blank=True,
                                  default="Ежедневно 10:00 – 24:00")
    map_url = models.URLField("Ссылка на карту", max_length=500, blank=True)
    currency = models.CharField("Валюта", max_length=10, default="сом")

    delivery_enabled = models.BooleanField("Доставка включена", default=True)
    delivery_fee = models.DecimalField("Стоимость доставки, сом", max_digits=10,
                                       decimal_places=2, default=100)
    free_delivery_from = models.DecimalField(
        "Бесплатная доставка от, сом", max_digits=10, decimal_places=2,
        null=True, blank=True, help_text="Если пусто — бесплатной доставки нет")
    min_order = models.DecimalField("Минимальный заказ, сом", max_digits=10,
                                    decimal_places=2, null=True, blank=True)
    pickup_address = models.CharField("Адрес самовывоза", max_length=255, blank=True,
                                      default="ул. Алымбека датки, 938, г. Ош")

    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Контакты и доставка"
        verbose_name_plural = "Контакты и доставка"

    def __str__(self):
        return self.name or "Осман Кафе"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def effective_whatsapp(self):
        from django.conf import settings
        digits = "".join(ch for ch in (self.whatsapp_number or "") if ch.isdigit())
        if digits:
            return digits
        return "".join(ch for ch in settings.WHATSAPP_NUMBER if ch.isdigit())

    def delivery_cost_for(self, subtotal):
        """Стоимость доставки с учётом порога бесплатной доставки."""
        from decimal import Decimal
        if not self.delivery_enabled:
            return Decimal("0")
        if self.free_delivery_from is not None and subtotal >= self.free_delivery_from:
            return Decimal("0")
        return self.delivery_fee or Decimal("0")
