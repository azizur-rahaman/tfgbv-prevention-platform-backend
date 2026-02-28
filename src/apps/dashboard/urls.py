from django.urls import path
from apps.dashboard.views import (
    DashboardLoginView,
    DashboardLogoutView,
    DashboardForbiddenView,
    DashboardHomeView,
    PoliceHomeView,
    ForensicHomeView,
    BccHomeView,
    JudiciaryHomeView,
    DashboardCasesView,
    DashboardCaseDetailView,
    DashboardChainVerifyView,
    DashboardCertificatesView,
    DashboardCertificateView,
)

urlpatterns = [
    path("login/", DashboardLoginView.as_view(), name="dashboard-login"),
    path("logout/", DashboardLogoutView.as_view(), name="dashboard-logout"),
    path("forbidden/", DashboardForbiddenView.as_view(), name="dashboard-forbidden"),
    path("", DashboardHomeView.as_view(), name="dashboard-home"),
    path("police/", PoliceHomeView.as_view(), name="dashboard-police-home"),
    path("forensic/", ForensicHomeView.as_view(), name="dashboard-forensic-home"),
    path("bcc/", BccHomeView.as_view(), name="dashboard-bcc-home"),
    path("judiciary/", JudiciaryHomeView.as_view(), name="dashboard-judiciary-home"),
    path("cases/", DashboardCasesView.as_view(), name="dashboard-cases"),
    path("cases/<uuid:vault_id>/", DashboardCaseDetailView.as_view(), name="dashboard-case-detail"),
    path("chain/", DashboardChainVerifyView.as_view(), name="dashboard-chain-verify"),
    path("certificates/", DashboardCertificatesView.as_view(), name="dashboard-certificates"),
    path("certificates/<uuid:vault_id>/", DashboardCertificateView.as_view(), name="dashboard-certificate"),
]