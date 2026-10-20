from django.contrib import admin, messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from . import whatsapp
from .models import Order, OrderCounter, OrderItem

STATUS_COLORS = {
    Order.Status.NEW: "#b48736",
    Order.Status.IN_WORK: "#2f6db0",
    Order.Status.DONE: "#2f855a",
    Order.Status.CANCELED: "#9a1c22",
}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("name", "price", "quantity", "line_total")
    readonly_fields = ("name", "price", "quantity", "line_total")
    can_delete = False

    @admin.display(description="Сумма")
    def line_total(self, obj):
        return f"{int(obj.line_total)} сом" if obj.pk else "—"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number_label", "created_short", "name", "phone",
                    "delivery_type", "total", "status_badge", "quick_actions")
    list_display_links = ("number_label", "name")
    list_filter = ("status", "delivery_type", "is_spam", "created_at")
    search_fields = ("name", "phone", "address", "number")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    save_on_top = True
    list_per_page = 30
    readonly_fields = ("number", "number_date", "subtotal", "delivery_fee",
                       "total", "ip", "website", "created_at", "wa_link")
    inlines = [OrderItemInline]
    actions = ("action_in_work", "action_done", "action_canceled", "action_spam")
    fieldsets = (
        ("Клиент", {"fields": ("name", "phone", "delivery_type", "address", "comment")}),
        ("Суммы", {"fields": ("subtotal", "delivery_fee", "total")}),
        ("Работа", {"fields": ("status", "manager_note")}),
        ("Служебное", {"fields": ("number", "number_date", "ip", "website",
                                  "is_spam", "created_at", "wa_link")}),
    )

    class Media:
        css = {"all": ("orders/admin_orders.css",)}
        js = ("orders/admin_orders.js",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related().prefetch_related("items")

    # --- Колонки ---

    @admin.display(description="Заказ", ordering="-created_at")
    def number_label(self, obj):
        if obj.number:
            return f"№{obj.number}"
        return "спам" if obj.is_spam else f"#{obj.pk}"

    @admin.display(description="Время", ordering="-created_at")
    def created_short(self, obj):
        return timezone.localtime(obj.created_at).strftime("%d.%m %H:%M")

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, "#8a8a8a")
        return format_html(
            '<span class="osman-badge" style="background:{}">{}</span>',
            color, obj.get_status_display())

    @admin.display(description="Быстро")
    def quick_actions(self, obj):
        if obj.is_spam:
            return "—"
        buttons = []
        for status, label in ((Order.Status.IN_WORK, "В работу"),
                              (Order.Status.DONE, "Готово")):
            if obj.status != status:
                url = reverse("admin:orders_order_set_status", args=[obj.pk, status])
                buttons.append(format_html(
                    '<a class="osman-quick" href="{}">{}</a>', url, label))
        return mark_safe(" ".join(buttons)) if buttons else mark_safe(
            '<span class="osman-muted">—</span>')

    @admin.display(description="Заказ")
    def wa_link(self, obj):
        if not obj.pk or obj.is_spam:
            return "—"
        return format_html(
            '<a class="button" href="{}" target="_blank" rel="noopener">Написать в WhatsApp</a>',
            whatsapp.build_url(obj))

    # --- Действия ---

    @admin.action(description="✅ Принять в работу")
    def action_in_work(self, request, queryset):
        self._set_status(request, queryset, Order.Status.IN_WORK)

    @admin.action(description="🏁 Отметить выполненными")
    def action_done(self, request, queryset):
        self._set_status(request, queryset, Order.Status.DONE)

    @admin.action(description="❌ Отменить")
    def action_canceled(self, request, queryset):
        self._set_status(request, queryset, Order.Status.CANCELED)

    @admin.action(description="🚫 Пометить спамом")
    def action_spam(self, request, queryset):
        n = queryset.update(is_spam=True, status=Order.Status.CANCELED)
        self.message_user(request, f"Помечено спамом: {n}", messages.WARNING)

    def _set_status(self, request, queryset, status):
        n = queryset.update(status=status)
        label = dict(Order.Status.choices).get(status, status)
        self.message_user(request, f"«{label}»: {n} заказ(ов)", messages.SUCCESS)

    # --- Быстрая смена статуса из списка без открытия заказа ---

    def get_urls(self):
        custom = [
            path("<int:pk>/set-status/<str:status>/",
                 self.admin_site.admin_view(self.set_status_view),
                 name="orders_order_set_status"),
        ]
        return custom + super().get_urls()

    def set_status_view(self, request, pk, status):
        order = get_object_or_404(Order, pk=pk)
        if status in dict(Order.Status.choices):
            order.status = status
            order.save(update_fields=["status"])
            self.message_user(
                request, f"Заказ {order.display_number}: {order.get_status_display()}",
                messages.SUCCESS)
        return redirect(request.META.get("HTTP_REFERER", reverse("admin:orders_order_changelist")))

    # --- Сводка за смену ---

    def changelist_view(self, request, extra_context=None):
        today = timezone.localdate()
        daily = Order.objects.filter(number_date=today, is_spam=False)
        extra_context = extra_context or {}
        extra_context["osman_summary"] = {
            "new": Order.objects.filter(status=Order.Status.NEW, is_spam=False).count(),
            "today_count": daily.count(),
            "today_sum": int(daily.aggregate(s=Sum("total"))["s"] or 0),
        }
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(OrderCounter)
class OrderCounterAdmin(admin.ModelAdmin):
    list_display = ("date", "last_number")
    ordering = ("-date",)
