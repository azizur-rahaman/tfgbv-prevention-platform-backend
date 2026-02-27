from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Mobile App API
    path("api/v1/auth/", include("apps.accounts.api.urls")),
    path("api/v1/evidence/", include("apps.evidence.api.urls")),
    path("api/v1/blockchain/", include("apps.blockchain.api.urls")),
    path("", include("apps.dashboard.urls")),
]