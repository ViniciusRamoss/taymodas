from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("sacola/", views.CartView.as_view(), name="detail"),
    path("sacola/esvaziar/", views.clear, name="clear"),
    path("sacola/<int:variant_id>/", views.update, name="update"),
]
