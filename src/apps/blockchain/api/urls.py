from django.urls import path
from apps.blockchain.api.views import ChainIntegrityView, EvidenceChainView

urlpatterns = [
    path("verify/", ChainIntegrityView.as_view(), name="chain-verify"),
    path("evidence/<uuid:vault_id>/", EvidenceChainView.as_view(), name="evidence-chain"),
]