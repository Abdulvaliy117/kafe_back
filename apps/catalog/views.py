from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, SiteInfo
from .serializers import CategorySerializer, SiteInfoSerializer


class MenuView(generics.ListAPIView):
    """GET /api/v1/menu/ — активные категории с доступными блюдами.

    Один запрос для витрины: меню приходит вложенным (категория -> items).
    """

    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return (Category.objects
                .filter(is_active=True)
                .prefetch_related("items")
                .all())


class SiteInfoView(APIView):
    """GET /api/v1/site/ — контакты кафе и настройки доставки."""

    def get(self, request):
        return Response(SiteInfoSerializer(SiteInfo.get_solo()).data)
