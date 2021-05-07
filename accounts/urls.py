from django.urls import path
from . import views

urlpatterns = [
    path('registration/', views.registration_view, name="registration_view"),
    path('login/', views.login_view, name="login")
]