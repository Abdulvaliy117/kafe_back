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
