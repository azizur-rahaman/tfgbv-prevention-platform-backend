from django.urls import path
from apps.dashboard.views import (
    DashboardLoginView,
    DashboardLogoutView,
    DashboardHomeView,
    EvidenceListView,
    EvidenceDetailView,
    ChainVerifyView,
    UserManagementView,
    UserDetailView,
    SystemHealthView,
    ForbiddenView,
)

app_name = "dashboard"

urlpatterns = [
    # Auth
    path("login/", DashboardLoginView.as_view(), name="login"),
    path("logout/", DashboardLogoutView.as_view(), name="logout"),
    path("forbidden/", ForbiddenView.as_view(), name="forbidden"),

    # Main
    path("", DashboardHomeView.as_view(), name="home"),

    # Evidence
    path("evidence/", EvidenceListView.as_view(), name="evidence_list"),
    path("evidence/<uuid:vault_id>/", EvidenceDetailView.as_view(), name="evidence_detail"),

    # Blockchain
    path("chain/", ChainVerifyView.as_view(), name="chain_verify"),

    # BCC Admin only
    path("users/", UserManagementView.as_view(), name="user_management"),
    path("users/<uuid:user_id>/", UserDetailView.as_view(), name="user_detail"),
    path("system/", SystemHealthView.as_view(), name="system_health"),
]