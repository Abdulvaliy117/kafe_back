from django.urls import path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Осман Кафе API",
        default_version="v1",
        description="Меню и заказы кафе «Осман» (Ош). Заказ формируется в ссылку WhatsApp.",
        contact=openapi.Contact(email="osman.kafe.osh@gmail.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("api/v1/swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("api/v1/swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("api/v1/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
