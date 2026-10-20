from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.catalog.models import MenuItem, SiteInfo
from . import whatsapp
from .models import Order, OrderItem


class OrderItemInputSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.filter(is_available=True, category__is_active=True))
    quantity = serializers.IntegerField(min_value=1, max_value=99)


class OrderItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["name", "price", "quantity", "line_total"]

    def get_line_total(self, obj):
        return float(obj.line_total)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    delivery_type_display = serializers.CharField(source="get_delivery_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    delivery_fee = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    whatsapp_url = serializers.SerializerMethodField()
    number_label = serializers.CharField(source="display_number", read_only=True)

    class Meta:
        model = Order
        fields = ["id", "number", "number_date", "number_label",
                  "delivery_type", "delivery_type_display", "status",
                  "status_display", "name", "phone", "address", "comment",
                  "subtotal", "delivery_fee", "total", "items",
                  "created_at", "whatsapp_url"]

    def get_whatsapp_url(self, obj):
        if obj.is_spam:
            return ""
        return whatsapp.build_url(obj)


class OrderCreateSerializer(serializers.Serializer):
    """Приём заказа с сайта. Суммы считаются на сервере, клиент их не присылает."""

    name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=40)
    delivery_type = serializers.ChoiceField(
        choices=Order.Delivery.choices, default=Order.Delivery.PICKUP)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    website = serializers.CharField(required=False, allow_blank=True)
    items = OrderItemInputSerializer(many=True)

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Имя короче 2 символов.")
        return value.strip()

    def validate_phone(self, value):
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) < 9:
            raise serializers.ValidationError("Укажите корректный номер телефона.")
        return value.strip()

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Корзина пуста.")
        return value

    def validate(self, attrs):
        site = SiteInfo.get_solo()
        if attrs.get("delivery_type") == Order.Delivery.DELIVERY:
            if not attrs.get("address", "").strip():
                raise serializers.ValidationError({"address": "Укажите адрес доставки."})
            if not site.delivery_enabled:
                raise serializers.ValidationError(
                    {"delivery_type": "Доставка временно недоступна."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        site = SiteInfo.get_solo()
        items_data = validated_data.pop("items")

        # Схлопываем дубли блюд: {MenuItem: qty}.
        merged = {}
        for row in items_data:
            menu_item = row["item"]
            merged[menu_item] = merged.get(menu_item, 0) + row["quantity"]

        subtotal = sum((mi.price * qty for mi, qty in merged.items()), Decimal("0"))

        if site.min_order is not None and subtotal < site.min_order:
            raise serializers.ValidationError(
                {"items": f"Минимальный заказ — {int(site.min_order)} "
                          f"{site.currency or 'сом'}."})

        delivery_type = validated_data.get("delivery_type", Order.Delivery.PICKUP)
        if delivery_type == Order.Delivery.DELIVERY:
            delivery_fee = site.delivery_cost_for(subtotal)
        else:
            delivery_fee = Decimal("0")

        # Спам-заказы (honeypot) номер не занимают.
        is_spam = bool(validated_data.get("website"))
        number = number_date = None
        if not is_spam:
            number_date = timezone.localdate()
            number = Order.next_number(number_date)

        order = Order.objects.create(
            delivery_type=delivery_type,
            name=validated_data["name"],
            phone=validated_data["phone"],
            address=validated_data.get("address", ""),
            comment=validated_data.get("comment", ""),
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=subtotal + delivery_fee,
            number=number,
            number_date=number_date,
            website=validated_data.get("website", ""),
            is_spam=is_spam,
            ip=validated_data.get("_ip"),
        )

        OrderItem.objects.bulk_create([
            OrderItem(order=order, menu_item=mi, name=mi.name,
                      price=mi.price, quantity=qty)
            for mi, qty in merged.items()
        ])
        return order


class OrderStatusSerializer(serializers.ModelSerializer):
    """Менеджеру: видно всё, менять можно статус и заметку."""

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "status", "manager_note", "delivery_type", "is_spam",
                  "name", "phone", "address", "comment",
                  "subtotal", "delivery_fee", "total", "items", "ip", "created_at"]
        read_only_fields = [f for f in fields if f not in ("status", "manager_note")]
