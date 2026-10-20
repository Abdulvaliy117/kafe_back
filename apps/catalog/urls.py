from django.urls import path

from .views import MenuView, SiteInfoView

urlpatterns = [
    path("menu/", MenuView.as_view(), name="menu"),
    path("site/", SiteInfoView.as_view(), name="site-info"),
]
