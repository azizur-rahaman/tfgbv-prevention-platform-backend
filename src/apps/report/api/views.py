from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from apps.report.models import Report
from apps.report.api.serializers import (
    ReportSubmitSerializer,
    ReportListSerializer,
    ReportDetailSerializer,
)
from apps.report.services.submit import submit_report


class ReportCreateView(APIView):
    """
    GET /api/v1/reports/ — list current user's reports.
    POST /api/v1/reports/ — place a new report (multipart: evidence_vault_ids, testimonial, signature).
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        qs = Report.objects.filter(reporter=request.user).order_by("-created_at")
        serializer = ReportListSerializer(qs, many=True)
        return Response({
            "success": True,
            "count": qs.count(),
            "results": serializer.data,
        })

    def post(self, request):
        serializer = ReportSubmitSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": "VALIDATION_ERROR",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            result = submit_report(
                reporter=request.user,
                evidence_vault_ids=data["evidence_vault_ids"],
                testimonial_text=data.get("testimonial_text") or "",
                testimonial_voice_file=data.get("testimonial_voice"),
                testimonial_video_file=data.get("testimonial_video"),
                digital_signature=data["digital_signature"],
                signature_algorithm=data.get("signature_algorithm") or "RSA-SHA256",
            )
        except ValueError as e:
            return Response(
                {
                    "success": False,
                    "error": "REPORT_ERROR",
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Report filed and sealed in blockchain.",
                "report_id": result["report_id"],
                "block_number": result["block_number"],
                "testimonial_voice_stored": bool(result.get("testimonial_voice_path")),
                "testimonial_video_stored": bool(result.get("testimonial_video_path")),
            },
            status=status.HTTP_201_CREATED,
        )


class ReportDetailView(APIView):
    """
    GET /api/v1/reports/<report_id>/

    Retrieve a single report (only if owned by the user).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, report_id):
        report = Report.objects.filter(
            id=report_id,
            reporter=request.user,
        ).first()
        if not report:
            return Response(
                {"success": False, "error": "NOT_FOUND", "message": "Report not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ReportDetailSerializer(report)
        return Response({"success": True, "report": serializer.data})
