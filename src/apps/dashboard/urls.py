from django.urls import path
from apps.dashboard.views import (
    DashboardLoginView,
    DashboardLogoutView,
    DashboardHomeView,
    DashboardCasesView,
    DashboardCaseDetailView,
    DashboardChainVerifyView,
    DashboardCertificatesView,
    DashboardCertificateView,
)

urlpatterns = [
    path("login/", DashboardLoginView.as_view(), name="dashboard-login"),
    path("logout/", DashboardLogoutView.as_view(), name="dashboard-logout"),
    path("", DashboardHomeView.as_view(), name="dashboard-home"),
    path("cases/", DashboardCasesView.as_view(), name="dashboard-cases"),
    path("cases/<uuid:vault_id>/", DashboardCaseDetailView.as_view(), name="dashboard-case-detail"),
    path("chain/", DashboardChainVerifyView.as_view(), name="dashboard-chain-verify"),
    path("certificates/", DashboardCertificatesView.as_view(), name="dashboard-certificates"),
    path("certificates/<uuid:vault_id>/", DashboardCertificateView.as_view(), name="dashboard-certificate"),
]