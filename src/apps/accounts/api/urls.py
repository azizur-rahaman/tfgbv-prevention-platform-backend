from django.urls import path
from apps.accounts.api.views import MobileLoginView, MobileRegisterView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("login/", MobileLoginView.as_view(), name="mobile-login"),
    path("register/", MobileRegisterView.as_view(), name="mobile-register"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]