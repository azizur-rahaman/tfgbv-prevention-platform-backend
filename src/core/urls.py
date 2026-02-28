from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Root -> dashboard (avoids 404 on GET /)
    path("", RedirectView.as_view(url="/dashboard/", permanent=False)),

    # Mobile App API
    path("api/v1/auth/", include("apps.accounts.api.urls")),
    path("api/v1/evidence/", include("apps.evidence.api.urls")),
    path("api/v1/reports/", include("apps.report.api.urls")),
    path("api/v1/blockchain/", include("apps.blockchain.api.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
]