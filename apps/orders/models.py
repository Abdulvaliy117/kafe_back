from django.db import models, transaction
from django.utils import timezone


class OrderCounter(models.Model):
    """Счётчик номера заказа внутри дня. Сбрасывается каждые сутки (Asia/Bishkek)."""

    date = models.DateField("Дата", unique=True)
    last_number = models.PositiveIntegerField("Последний номер", default=0)

    class Meta:
        verbose_name = "Счётчик заказов"
        verbose_name_plural = "Счётчики заказов"

    def __str__(self):
        return f"{self.date:%d.%m.%Y}: {self.last_number}"


class Order(models.Model):
    """Заказ с сайта. Оформляется в WhatsApp-ссылку (см. whatsapp.py).

    Итоговая цена считается на сервере по актуальному меню, клиентские суммы
    не принимаются — в модель попадают только снимки цен на момент заказа.
    """

    class Delivery(models.TextChoices):
        PICKUP = "pickup", "Самовывоз"
        DELIVERY = "delivery", "Доставка"

    class Status(models.TextChoices):
        NEW = "new", "Новый"
        IN_WORK = "in_work", "В работе"
        DONE = "done", "Выполнен"
        CANCELED = "canceled", "Отменён"

    delivery_type = models.CharField("Способ получения", max_length=20,
                                     choices=Delivery.choices, default=Delivery.PICKUP)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.NEW)

    name = models.CharField("Имя клиента", max_length=120)
    phone = models.CharField("Телефон", max_length=40)
    address = models.CharField("Адрес доставки", max_length=255, blank=True)
    comment = models.TextField("Комментарий", max_length=1000, blank=True)

    subtotal = models.DecimalField("Сумма блюд, сом", max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField("Доставка, сом", max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField("Итого, сом", max_digits=10, decimal_places=2, default=0)

    number = models.PositiveIntegerField("Номер за день", null=True, blank=True, editable=False)
    number_date = models.DateField("Дата номера", null=True, blank=True, editable=False)

    manager_note = models.TextField("Заметка менеджера", blank=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    website = models.CharField("Honeypot", max_length=200, blank=True)
    is_spam = models.BooleanField("Спам", default=False)

    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["number_date", "number"],
                                    name="uniq_order_number_per_day"),
        ]

    def __str__(self):
        return f"Заказ {self.display_number} — {self.name} ({self.total} сом)"

    @property
    def display_number(self):
        """Человеческий номер: «№12 от 18.10.2026» или «#pk» для старых/спама."""
        if self.number and self.number_date:
            return f"№{self.number} от {self.number_date:%d.%m.%Y}"
        if self.is_spam:
            return "—"
        return f"#{self.pk}"

    @classmethod
    def next_number(cls, day=None):
        """Следующий номер за день. Блокировка строки защищает от гонок."""
        day = day or timezone.localdate()
        with transaction.atomic():
            OrderCounter.objects.get_or_create(date=day)
            counter = OrderCounter.objects.select_for_update().get(date=day)
            counter.last_number += 1
            counter.save(update_fields=["last_number"])
            return counter.last_number

    @property
    def item_count(self):
        return sum(i.quantity for i in self.items.all())


class OrderItem(models.Model):
    """Строка заказа: снимок названия и цены блюда (блюдо могут позже удалить)."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey("catalog.MenuItem", on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name="order_items",
                                  verbose_name="Блюдо")
    name = models.CharField("Название", max_length=160)
    price = models.DecimalField("Цена, сом", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Количество", default=1)

    class Meta:
        ordering = ["id"]
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.name} x{self.quantity}"

    @property
    def line_total(self):
        return self.price * self.quantity
