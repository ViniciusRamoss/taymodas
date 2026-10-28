from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("health/", views.healthcheck, name="healthcheck"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("entregas/", views.DeliveryView.as_view(), name="delivery"),
    path("como-comprar/", views.HowToBuyView.as_view(), name="how_to_buy"),
]
