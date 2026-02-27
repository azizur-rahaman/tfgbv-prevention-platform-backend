from django.urls import path
from apps.evidence.api.views import EvidenceUploadView, EvidenceStatusView

urlpatterns = [
    path("upload/", EvidenceUploadView.as_view(), name="evidence-upload"),
    path("<uuid:vault_id>/status/", EvidenceStatusView.as_view(), name="evidence-status"),
]