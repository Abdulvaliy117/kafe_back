from rest_framework import serializers

from .models import Category, MenuItem, SiteInfo


class MenuItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    old_price = serializers.DecimalField(max_digits=10, decimal_places=2,
                                         coerce_to_string=False, allow_null=True)
    image = serializers.SerializerMethodField()
    is_discounted = serializers.BooleanField(read_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "name", "description", "weight", "price", "old_price",
                  "image", "is_popular", "is_new", "is_available", "is_discounted"]

    def get_image(self, obj):
        if not obj.image:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


class CategorySerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["slug", "name", "description", "emoji", "items"]

    def get_items(self, obj):
        items = [i for i in obj.items.all() if i.is_available]
        return MenuItemSerializer(items, many=True, context=self.context).data


class MenuItemImportSerializer(serializers.Serializer):
    """Одно блюдо в массовом импорте меню."""

    name = serializers.CharField(max_length=160)
    description = serializers.CharField(max_length=600, allow_blank=True, required=False, default="")
    weight = serializers.CharField(max_length=40, allow_blank=True, required=False, default="")
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    is_popular = serializers.BooleanField(required=False, default=False)
    is_new = serializers.BooleanField(required=False, default=False)
    is_available = serializers.BooleanField(required=False, default=True)
    order = serializers.IntegerField(required=False, min_value=0, default=0)


class CategoryImportSerializer(serializers.Serializer):
    """Категория вместе со своими блюдами."""

    slug = serializers.SlugField(max_length=50)
    name = serializers.CharField(max_length=120)
    description = serializers.CharField(max_length=255, allow_blank=True, required=False, default="")
    emoji = serializers.CharField(max_length=8, allow_blank=True, required=False, default="")
    order = serializers.IntegerField(required=False, min_value=0, default=0)
    is_active = serializers.BooleanField(required=False, default=True)
    items = MenuItemImportSerializer(many=True, required=False)


class MenuImportSerializer(serializers.Serializer):
    """POST /api/v1/menu/ — заливка меню целиком (категории + блюда)."""

    categories = CategoryImportSerializer(many=True, allow_empty=False)


class MenuImportResultSerializer(serializers.Serializer):
    """Что изменилось после импорта."""

    categories_created = serializers.IntegerField()
    categories_updated = serializers.IntegerField()
    items_created = serializers.IntegerField()
    items_updated = serializers.IntegerField()


class SiteInfoSerializer(serializers.ModelSerializer):
    delivery_fee = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    free_delivery_from = serializers.DecimalField(max_digits=10, decimal_places=2,
                                                  coerce_to_string=False, allow_null=True)
    min_order = serializers.DecimalField(max_digits=10, decimal_places=2,
                                         coerce_to_string=False, allow_null=True)
    whatsapp_number = serializers.SerializerMethodField()

    class Meta:
        model = SiteInfo
        fields = ["name", "tagline", "about", "phone", "whatsapp_number", "instagram",
                  "address", "work_hours", "map_url", "currency",
                  "delivery_enabled", "delivery_fee", "free_delivery_from",
                  "min_order", "pickup_address"]

    def get_whatsapp_number(self, obj):
        return obj.effective_whatsapp()
