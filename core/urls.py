from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from .yasg import urlpatterns as doc_urls

admin.site.site_header = "Осман Кафе — админка"
admin.site.site_title = "Осман Кафе"
# Прячем дефолтную ссылку «View site» — в шапке свои кнопки на витрину и пульт.
admin.site.site_url = None

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/token/', obtain_auth_token, name='api-token'),
    path('api/v1/', include('apps.catalog.urls')),   # /menu/, /site/
    path('api/v1/orders/', include('apps.orders.urls')),  # заказы с сайта
]

urlpatterns += doc_urls

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
