from urllib.parse import quote

from apps.catalog.models import SiteInfo


def _num(value):
    """1000.00 -> '1 000' (сома целые, копейки не показываем)."""
    value = value or 0
    try:
        return f"{int(round(float(value))):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def build_text(order):
    """Сообщение для WhatsApp с полным составом заказа."""
    site = SiteInfo.get_solo()
    cur = site.currency or "сом"

    lines = [f"Здравствуйте! Хочу оформить заказ в {site.name}."]
    if order.number:
        lines.append(f"Заказ {order.display_number}")
    lines.append("")

    for idx, item in enumerate(order.items.all(), start=1):
        lines.append(
            f"{idx}. {item.name} x{item.quantity} — {_num(item.line_total)} {cur}"
        )

    lines.append("")
    lines.append(f"Сумма блюд: {_num(order.subtotal)} {cur}")
    if order.delivery_type == order.Delivery.DELIVERY:
        if order.delivery_fee and float(order.delivery_fee) > 0:
            lines.append(f"Доставка: {_num(order.delivery_fee)} {cur}")
        else:
            lines.append("Доставка: бесплатно")
    lines.append(f"Итого: {_num(order.total)} {cur}")
    lines.append("")

    if order.delivery_type == order.Delivery.DELIVERY:
        lines.append("Получение: доставка")
        if order.address:
            lines.append(f"Адрес: {order.address}")
    else:
        lines.append("Получение: самовывоз")
        if site.pickup_address:
            lines.append(f"Заберу по адресу: {site.pickup_address}")

    lines.append(f"Меня зовут {order.name}.")
    lines.append(f"Мой телефон: {order.phone}")
    if order.comment:
        lines.append(f"Комментарий: {order.comment}")

    return "\n".join(lines)


def get_whatsapp_number():
    return SiteInfo.get_solo().effective_whatsapp()


def build_url(order):
    """Ссылка wa.me с готовым текстом заказа."""
    return f"https://wa.me/{get_whatsapp_number()}?text={quote(build_text(order))}"
