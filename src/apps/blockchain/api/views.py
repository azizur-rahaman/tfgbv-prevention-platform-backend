from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.blockchain.services import verify_chain_integrity, verify_single_evidence_chain
from apps.accounts.models import User


class ChainIntegrityView(APIView):
    """
    GET /api/v1/blockchain/verify/

    Full chain integrity check.
    Only accessible by police, forensic analysts, and BCC admins.
    This is the "Kill Demo" endpoint — shows GREEN or RED.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Only authorized roles can run full chain verification
        allowed_roles = [
            User.UserRole.POLICE,
            User.UserRole.FORENSIC_ANALYST,
            User.UserRole.BCC_ADMIN,
            User.UserRole.JUDICIARY,
        ]

        if request.user.role not in allowed_roles:
            return Response(
                {
                    "success": False,
                    "error": "Insufficient permissions. "
                             "Only police and forensic roles can verify the chain."
                },
                status=403,
            )

        result = verify_chain_integrity()

        return Response({
            "success": True,
            "chain_status": "INTACT" if result["is_intact"] else "COMPROMISED",
            "is_intact": result["is_intact"],
            "total_blocks": result["total_blocks"],
            "broken_at_block": result["broken_at_block"],
            "error": result["error"],
            "blocks_checked": result["blocks_checked"],
        })


class EvidenceChainView(APIView):
    """
    GET /api/v1/blockchain/evidence/<vault_id>/

    Verify the chain for a single piece of evidence.
    Accessible by the reporter (victim) and police.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, vault_id):
        result = verify_single_evidence_chain(str(vault_id))

        return Response({
            "success": True,
            "vault_id": str(vault_id),
            "chain_status": "INTACT" if result["is_intact"] else "COMPROMISED",
            "is_intact": result["is_intact"],
            "error": result["error"],
            "blocks": result["blocks"],
        })