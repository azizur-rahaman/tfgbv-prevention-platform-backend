from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from apps.evidence.api.serializers import EvidenceUploadSerializer
from apps.evidence.services.upload import ingest_evidence
from apps.blockchain.models import ForensicLog


class EvidenceUploadView(APIView):
    """
    POST /api/v1/evidence/upload/

    Receives encrypted evidence from the Flutter app.
    Verifies hash, encrypts, stores in MinIO, seals in blockchain.

    Authentication: Bearer JWT token required.
    Content-Type: multipart/form-data
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = EvidenceUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": "VALIDATION_ERROR",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Read raw file bytes from the uploaded file
        uploaded_file = serializer.validated_data["file"]
        raw_bytes = uploaded_file.read()

        try:
            result = ingest_evidence(
                reporter=request.user,
                raw_file=raw_bytes,
                submitted_hash=serializer.validated_data["file_hash"],
                captured_at=serializer.validated_data["captured_at"],
                evidence_type=serializer.validated_data["evidence_type"],
                harm_type=serializer.validated_data["harm_type"],
                file_mime_type=serializer.validated_data["file_mime_type"],
                latitude=serializer.validated_data.get("latitude"),
                longitude=serializer.validated_data.get("longitude"),
                description=serializer.validated_data.get("description"),
                device_id=serializer.validated_data.get("device_id"),
                app_version=serializer.validated_data.get("app_version"),
                assigned_upazila=serializer.validated_data.get("assigned_upazila") or None,
            )

            return Response(
                {
                    "success": True,
                    "message": "Evidence sealed in vault.",
                    "vault_id": result["vault_id"],
                    "file_hash": result["file_hash"],
                    "block_number": result["block_number"],
                    "status": result["status"],
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as e:
            # Hash mismatch — evidence rejected
            return Response(
                {
                    "success": False,
                    "error": "HASH_MISMATCH",
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": "SERVER_ERROR",
                    "message": "Evidence ingest failed. Please retry.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EvidenceStatusView(APIView):
    """
    GET /api/v1/evidence/<vault_id>/status/

    Flutter app polls this to confirm upload was sealed in blockchain.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, vault_id):
        from apps.evidence.models import Evidence

        try:
            evidence = Evidence.objects.get(
                vault_id=vault_id,
                reporter=request.user,   # Victims can only see their own
            )
        except Evidence.DoesNotExist:
            return Response(
                {"success": False, "error": "NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        logs = ForensicLog.objects.filter(evidence=evidence).values(
            "block_number", "event_type", "timestamp", "notes"
        )

        return Response(
            {
                "success": True,
                "vault_id": str(evidence.vault_id),
                "status": evidence.status,
                "is_hash_verified": evidence.is_hash_verified,
                "uploaded_at": evidence.uploaded_at,
                "blockchain_entries": list(logs),
            }
        )