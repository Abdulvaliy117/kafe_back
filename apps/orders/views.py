from rest_framework import mixins, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer, OrderStatusSerializer


class OrderThrottle(AnonRateThrottle):
    scope = "orders"


class OrderPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """POST — всем (заказ с сайта). GET/PATCH/DELETE — только персоналу."""

    queryset = Order.objects.prefetch_related("items").all()
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action in ("update", "partial_update"):
            return OrderStatusSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAdminUser()]

    def get_throttles(self):
        if self.action == "create":
            return [OrderThrottle()]
        return []

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("delivery_type"):
            qs = qs.filter(delivery_type=params["delivery_type"])
        if params.get("is_spam") is not None and params.get("is_spam") != "":
            qs = qs.filter(is_spam=params["is_spam"].lower() in ("1", "true", "yes"))
        if params.get("date"):
            qs = qs.filter(created_at__date=params["date"])
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip = (request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
              or request.META.get("REMOTE_ADDR"))
        order = serializer.save(_ip=ip or None)

        out = OrderSerializer(order, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED,
                        headers=self.get_success_headers(out.data))
