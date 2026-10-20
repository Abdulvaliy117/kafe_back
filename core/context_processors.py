from django.conf import settings


def site_links(request):
    """Ссылки на витрину и пульт менеджера для шапки админки."""
    frontend = (getattr(settings, "FRONTEND_URL", "") or "").rstrip("/")
    return {
        "frontend_url": frontend,
        "manager_url": f"{frontend}/manage" if frontend else "",
    }
