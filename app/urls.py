from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name="homepage"),
    path('new-order/', views.new_order_view, name="new_order"),
    path('json-orders/', views.open_orders_json_view, name="json_orders"),
    path('profit-and-losses/', views.profit_and_losses_view, name="profit_and_losses"),
    path('json-profile/', views.user_profile_json_view, name="json_profile")
]