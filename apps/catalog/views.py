from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsStaffOrReadOnly

from .models import Category, MenuItem, SiteInfo
from .serializers import (CategorySerializer, MenuImportResultSerializer,
                          MenuImportSerializer, SiteInfoSerializer)


class MenuView(generics.ListCreateAPIView):
    """GET /api/v1/menu/ — активные категории с доступными блюдами.

    Один запрос для витрины: меню приходит вложенным (категория -> items).

    POST /api/v1/menu/ — массовая заливка меню (только персонал, по токену).
    Категория ищется по slug, блюдо — по паре категория + название: если уже
    есть, обновляется, нет — создаётся. Существующие позиции из payload не
    удаляются, поэтому повторная заливка безопасна.
    """

    pagination_class = None
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        return (Category.objects
                .filter(is_active=True)
                .prefetch_related("items")
                .all())

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MenuImportSerializer
        return CategorySerializer

    @swagger_auto_schema(request_body=MenuImportSerializer,
                          responses={201: MenuImportResultSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = {"categories_created": 0, "categories_updated": 0,
                  "items_created": 0, "items_updated": 0}

        for cat_data in serializer.validated_data["categories"]:
            items = cat_data.pop("items", [])
            cat, created = Category.objects.update_or_create(
                slug=cat_data["slug"], defaults=cat_data)
            result["categories_created" if created else "categories_updated"] += 1

            for position, item_data in enumerate(items, start=1):
                item_data["order"] = item_data.get("order") or position
                _, item_created = MenuItem.objects.update_or_create(
                    category=cat, name=item_data["name"], defaults=item_data)
                result["items_created" if item_created else "items_updated"] += 1

        return Response(result, status=status.HTTP_201_CREATED)


class SiteInfoView(APIView):
    """GET /api/v1/site/ — контакты кафе и настройки доставки."""

    def get(self, request):
        return Response(SiteInfoSerializer(SiteInfo.get_solo()).data)
