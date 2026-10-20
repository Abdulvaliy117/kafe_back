from django.contrib import admin
from django.utils.html import format_html

from .models import Category, MenuItem, SiteInfo


admin.site.site_header = "Осман Кафе — администрирование"
admin.site.site_title = "Осман Кафе"
admin.site.index_title = "Управление сайтом"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "items_count", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Блюд")
    def items_count(self, obj):
        return obj.items.count()


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("thumb", "name", "category", "price", "weight",
                    "is_available", "is_popular", "is_new", "order")
    list_display_links = ("thumb", "name")
    list_editable = ("price", "is_available", "is_popular", "is_new", "order")
    list_filter = ("category", "is_available", "is_popular", "is_new")
    search_fields = ("name", "description")
    list_select_related = ("category",)
    fieldsets = (
        ("Основное", {"fields": ("category", "name", "description", "weight")}),
        ("Цена", {"fields": ("price", "old_price")}),
        ("Фото", {"fields": ("image", "image_preview")}),
        ("Метки", {"fields": ("is_popular", "is_new", "is_available", "order")}),
    )
    readonly_fields = ("image_preview",)

    @admin.display(description="Фото")
    def thumb(self, obj):
        if not obj.image:
            return "—"
        return format_html('<img src="{}" style="height:40px;border-radius:6px" />', obj.image.url)

    @admin.display(description="Превью")
    def image_preview(self, obj):
        if not obj.image:
            return "Фото не загружено"
        return format_html('<img src="{}" style="max-height:220px;border-radius:10px" />', obj.image.url)


@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Кафе", {"fields": ("name", "tagline", "about", "currency")}),
        ("Контакты", {"fields": ("phone", "whatsapp_number", "instagram",
                                 "address", "work_hours", "map_url")}),
        ("Доставка", {"fields": ("delivery_enabled", "delivery_fee",
                                 "free_delivery_from", "min_order", "pickup_address")}),
        ("Служебное", {"fields": ("updated_at",)}),
    )
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        # Только одна строка настроек.
        return not SiteInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
