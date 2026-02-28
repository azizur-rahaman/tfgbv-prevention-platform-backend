from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator

from apps.evidence.models import Evidence
from apps.blockchain.models import ForensicLog
from apps.blockchain.services import verify_chain_integrity, verify_single_evidence_chain
from apps.accounts.models import User
from apps.dashboard.permissions import get_evidence_queryset_for_role, role_required


DASHBOARD_ROLES = [
    User.UserRole.POLICE,
    User.UserRole.FORENSIC_ANALYST,
    User.UserRole.BCC_ADMIN,
    User.UserRole.JUDICIARY,
]


class DashboardLoginView(View):
    def get(self, request):
        if request.user.is_authenticated and request.user.role in DASHBOARD_ROLES:
            return redirect("dashboard-home")
        if request.user.is_authenticated and request.user.role not in DASHBOARD_ROLES:
            return redirect("dashboard-forbidden")
        return render(request, "dashboard/login.html")

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user and user.role in DASHBOARD_ROLES:
            login(request, user)
            return redirect("dashboard-home")

        return render(request, "dashboard/login.html", {
            "form": {"errors": True}
        })


class DashboardLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("dashboard-login")


class DashboardForbiddenView(View):
    """Rendered when role_required redirects; no login required."""
    def get(self, request):
        return render(request, "dashboard/forbidden.html")


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardHomeView(View):
    """Redirects to role-specific dashboard home. Non-dashboard roles go to forbidden (avoid redirect loop)."""
    def get(self, request):
        role = request.user.role
        if role == User.UserRole.POLICE:
            return redirect("dashboard-police-home")
        if role == User.UserRole.FORENSIC_ANALYST:
            return redirect("dashboard-forensic-home")
        if role == User.UserRole.BCC_ADMIN:
            return redirect("dashboard-bcc-home")
        if role == User.UserRole.JUDICIARY:
            return redirect("dashboard-judiciary-home")
        return redirect("dashboard-forbidden")


def _role_home_context(request):
    """Build stats and recent_evidence for role home using get_evidence_queryset_for_role."""
    base_qs = Evidence.objects.order_by("-uploaded_at")
    qs = get_evidence_queryset_for_role(request.user, base_qs)
    stats = {
        "total": qs.count(),
        "verified": qs.filter(status="verified").count(),
        "pending": qs.filter(status="pending").count(),
        "flagged": qs.filter(status="flagged").count(),
    }
    chain = verify_chain_integrity()
    recent_evidence = qs[:10]
    return {
        "stats": stats,
        "chain_intact": chain["is_intact"],
        "total_blocks": chain["total_blocks"],
        "recent_evidence": recent_evidence,
    }


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(User.UserRole.POLICE), name="dispatch")
class PoliceHomeView(View):
    """Police dashboard: upazila case stats, case inbox link, chain status (Phase 3)."""
    def get(self, request):
        context = _role_home_context(request)
        context["role_label"] = "Police"
        context["upazila"] = request.user.assigned_upazila or "All regions"
        return render(request, "dashboard/police/home.html", context)


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(User.UserRole.FORENSIC_ANALYST), name="dispatch")
class ForensicHomeView(View):
    """Forensic analyst dashboard: flagged queue, chain audit link (Phase 4)."""
    def get(self, request):
        context = _role_home_context(request)
        context["role_label"] = "Forensic Analyst"
        context["flagged_count"] = Evidence.objects.filter(status=Evidence.EvidenceStatus.FLAGGED).count()
        return render(request, "dashboard/forensic/home.html", context)


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(User.UserRole.FORENSIC_ANALYST), name="dispatch")
class ForensicFlaggedCasesView(View):
    """List all evidence with status=flagged (Phase 4)."""
    def get(self, request):
        qs = Evidence.objects.filter(status=Evidence.EvidenceStatus.FLAGGED).order_by("-uploaded_at")
        return render(request, "dashboard/forensic/flagged.html", {"evidence_list": qs, "total_count": qs.count()})


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(User.UserRole.FORENSIC_ANALYST), name="dispatch")
class ForensicChainAuditView(View):
    """Block-by-block chain audit with raw hash comparison (Phase 4)."""
    def get(self, request):
        result = verify_chain_integrity()
        return render(request, "dashboard/forensic/chain_audit.html", {"result": result})


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(User.UserRole.FORENSIC_ANALYST), name="dispatch")
class ForensicHashReverifyView(View):
    """Hash re-verification tool: re-download, decrypt, re-hash, compare (Phase 4)."""
    def get(self, request, vault_id):
        from apps.evidence.services.reverify import reverify_evidence_hash
        base_qs = Evidence.objects.all()
        allowed_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(allowed_qs, vault_id=vault_id)
        report = reverify_evidence_hash(str(vault_id))
        report["evidence"] = evidence
        return render(request, "dashboard/forensic/reverify_report.html", report)


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(User.UserRole.FORENSIC_ANALYST), name="dispatch")
class ForensicEncryptionIntegrityView(View):
    """Encryption integrity: stored size and nonce vs record (Phase 4)."""
    def get(self, request, vault_id):
        from apps.evidence.services.reverify import check_encryption_integrity
        base_qs = Evidence.objects.all()
        allowed_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(allowed_qs, vault_id=vault_id)
        report = check_encryption_integrity(str(vault_id))
        report["evidence"] = evidence
        return render(request, "dashboard/forensic/encryption_integrity.html", report)


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(User.UserRole.FORENSIC_ANALYST), name="dispatch")
class ForensicTamperLogView(View):
    """Blocks where hash verification failed (Phase 4)."""
    def get(self, request):
        result = verify_chain_integrity()
        invalid_blocks = [b for b in result.get("blocks_checked", []) if not b.get("is_valid", True)]
        return render(request, "dashboard/forensic/tamper_log.html", {
            "result": result,
            "invalid_blocks": invalid_blocks,
        })


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(User.UserRole.FORENSIC_ANALYST), name="dispatch")
class ForensicExpertReportPdfView(View):
    """Expert forensic report PDF: hashes, block numbers, nonce (Phase 4)."""
    def get(self, request, vault_id):
        from django.http import HttpResponse
        base_qs = Evidence.objects.all()
        allowed_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(allowed_qs, vault_id=vault_id)
        chain_result = verify_single_evidence_chain(str(vault_id))
        pdf_response = _build_expert_report_pdf(evidence, chain_result)
        if pdf_response is None:
            return redirect("dashboard-case-detail", vault_id=vault_id)
        return pdf_response


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class BccHomeView(View):
    def get(self, request):
        context = _role_home_context(request)
        context["role_label"] = "BCC Admin"
        return render(request, "dashboard/home.html", context)


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class JudiciaryHomeView(View):
    def get(self, request):
        context = _role_home_context(request)
        context["role_label"] = "Judiciary"
        return render(request, "dashboard/home.html", context)


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(User.UserRole.JUDICIARY), name="dispatch")
class VerdictView(View):
    """Record or update court disposition (Judiciary only). Writes ForensicLog VERDICT."""
    def get(self, request, vault_id):
        base_qs = Evidence.objects.filter(status=Evidence.EvidenceStatus.SUBMITTED)
        allowed_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(allowed_qs, vault_id=vault_id)
        return render(request, "dashboard/judiciary/verdict.html", {
            "evidence": evidence,
            "verdict_choices": Evidence.VerdictStatus.choices,
        })

    def post(self, request, vault_id):
        base_qs = Evidence.objects.filter(status=Evidence.EvidenceStatus.SUBMITTED)
        allowed_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(allowed_qs, vault_id=vault_id)
        verdict = (request.POST.get("verdict") or "").strip()
        if verdict not in dict(Evidence.VerdictStatus.choices):
            return render(request, "dashboard/judiciary/verdict.html", {
                "evidence": evidence,
                "verdict_choices": Evidence.VerdictStatus.choices,
                "error": "Invalid disposition. Select Admitted, Rejected, or Under Review.",
            })
        from django.utils import timezone
        evidence.verdict = verdict
        evidence.verdict_at = timezone.now()
        evidence.verdict_by = request.user
        evidence.save(update_fields=["verdict", "verdict_at", "verdict_by"])
        ForensicLog.objects.create(
            event_type=ForensicLog.EventType.VERDICT,
            evidence=evidence,
            evidence_hash_snapshot=evidence.file_hash,
            actor_user_id=str(request.user.id),
            actor_role=request.user.role,
            notes=f"Disposition: {evidence.get_verdict_display()}. Recorded by {request.user.username}.",
        )
        return redirect("dashboard-case-detail", vault_id=vault_id)


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(User.UserRole.POLICE), name="dispatch")
class MarkForSubmissionView(View):
    """Mark evidence as submitted to court (Police only). POST only; adds ForensicLog TRANSFER (Phase 3)."""
    def post(self, request, vault_id):
        base_qs = Evidence.objects.all()
        allowed_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(allowed_qs, vault_id=vault_id)
        if evidence.status != Evidence.EvidenceStatus.VERIFIED:
            return redirect("dashboard-case-detail", vault_id=vault_id)
        evidence.status = Evidence.EvidenceStatus.SUBMITTED
        evidence.save(update_fields=["status"])
        ForensicLog.objects.create(
            event_type=ForensicLog.EventType.TRANSFER,
            evidence=evidence,
            evidence_hash_snapshot=evidence.file_hash,
            actor_user_id=str(request.user.id),
            actor_role=request.user.role,
            notes=f"Submitted to court by police. Officer: {request.user.username}.",
        )
        return redirect("dashboard-case-detail", vault_id=vault_id)

    def get(self, request, vault_id):
        return redirect("dashboard-case-detail", vault_id=vault_id)


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardCasesView(View):
    def get(self, request):
        base_qs = Evidence.objects.order_by("-uploaded_at")
        status = request.GET.get("status")
        harm_type = request.GET.get("harm_type")
        if status:
            base_qs = base_qs.filter(status=status)
        if harm_type:
            base_qs = base_qs.filter(harm_type=harm_type)
        qs = get_evidence_queryset_for_role(request.user, base_qs)

        return render(request, "dashboard/cases.html", {
            "evidence_list": qs,
            "total_count": qs.count(),
        })


def _show_victim_identity(user):
    """Victim identity (NID hash, verification) visible only to Police and BCC (Phase 2.4)."""
    return user.role in (User.UserRole.POLICE, User.UserRole.BCC_ADMIN)


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardCaseDetailView(View):
    def get(self, request, vault_id):
        base_qs = Evidence.objects.all()
        allowed_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(allowed_qs, vault_id=vault_id)
        chain_result = verify_single_evidence_chain(str(vault_id))

        return render(request, "dashboard/case_detail.html", {
            "evidence": evidence,
            "chain_result": chain_result,
            "show_victim_identity": _show_victim_identity(request.user),
        })


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardChainVerifyView(View):
    def get(self, request):
        result = verify_chain_integrity()
        return render(request, "dashboard/chain_verify.html", {
            "result": result,
        })


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardCertificatesView(View):
    def get(self, request):
        # Police/Forensic/BCC see verified (and submitted); Judiciary sees only submitted
        base_qs = Evidence.objects.filter(
            status__in=[Evidence.EvidenceStatus.VERIFIED, Evidence.EvidenceStatus.SUBMITTED]
        ).order_by("-uploaded_at")
        evidence_list = get_evidence_queryset_for_role(request.user, base_qs)

        return render(request, "dashboard/certificates.html", {
            "evidence_list": evidence_list,
        })


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardCertificateView(View):
    """65B certificate inline view (Phase 2.3)."""
    def get(self, request, vault_id):
        base_qs = Evidence.objects.all()
        allowed_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(allowed_qs, vault_id=vault_id)
        chain_result = verify_single_evidence_chain(str(vault_id))
        return render(request, "dashboard/certificate_view.html", {
            "evidence": evidence,
            "chain_result": chain_result,
        })


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardCertificatePdfView(View):
    """65B certificate PDF download (Phase 2.3)."""
    def get(self, request, vault_id):
        from django.http import HttpResponse
        base_qs = Evidence.objects.all()
        allowed_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(allowed_qs, vault_id=vault_id)
        chain_result = verify_single_evidence_chain(str(vault_id))
        pdf_response = _build_certificate_pdf(evidence, chain_result)
        if pdf_response is None:
            return render(request, "dashboard/certificate_view.html", {
                "evidence": evidence,
                "chain_result": chain_result,
                "pdf_error": "PDF generation unavailable. Install reportlab: pip install reportlab",
            })
        return pdf_response


def _build_certificate_pdf(evidence, chain_result):
    """Build 65B certificate PDF using ReportLab. Returns HttpResponse or None if reportlab missing."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from io import BytesIO
        from django.http import HttpResponse
    except ImportError:
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="CertTitle",
        parent=styles["Heading1"],
        fontSize=14,
        spaceAfter=6,
        alignment=1,
    )
    heading_style = ParagraphStyle(
        name="CertHeading",
        parent=styles["Heading2"],
        fontSize=10,
        spaceAfter=4,
        textColor=colors.HexColor("#64748b"),
    )
    body_style = styles["Normal"]
    body_style.fontSize = 9
    body_style.spaceAfter = 4

    story = []
    story.append(Paragraph("CERTIFICATE UNDER SECTION 65B", title_style))
    story.append(Paragraph("Bangladesh Evidence Act 2022 — Electronic Evidence", body_style))
    story.append(Spacer(1, 8*mm))

    data = [
        ["Vault ID (Evidence Reference)", str(evidence.vault_id)],
        ["SHA-256 File Hash", evidence.file_hash],
        ["Chain of Custody", "INTACT" if chain_result["is_intact"] else "COMPROMISED"],
        ["Hash Verified", "Yes" if evidence.is_hash_verified else "Pending"],
        ["Evidence Type", evidence.get_evidence_type_display()],
        ["Harm Classification", evidence.get_harm_type_display()],
        ["Captured At", evidence.captured_at.strftime("%B %d, %Y, %H:%M")],
        ["Uploaded to Vault", evidence.uploaded_at.strftime("%B %d, %Y, %H:%M")],
    ]
    if evidence.verdict:
        data.append(["Court Disposition", evidence.get_verdict_display()])
    t = Table(data, colWidths=[60*mm, 100*mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#64748b")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1e293b")),
    ]))
    story.append(t)
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "This certificate attests to the integrity and chain of custody of the above digital evidence "
        "as maintained by the Nirvhoy platform. The cryptographic hash and blockchain audit trail "
        "support admissibility under Section 65B of the Bangladesh Evidence Act 2022.",
        body_style
    ))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="65b-certificate-{evidence.vault_id}.pdf"'
    return response


def _build_expert_report_pdf(evidence, chain_result):
    """Expert forensic report PDF: hashes, block numbers, nonce (Phase 4)."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from io import BytesIO
        from django.http import HttpResponse
    except ImportError:
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    body_style = styles["Normal"]
    body_style.fontSize = 8
    body_style.spaceAfter = 3

    story = []
    story.append(Paragraph("EXPERT FORENSIC REPORT", ParagraphStyle(name="Title", parent=styles["Heading1"], fontSize=12, spaceAfter=4)))
    story.append(Paragraph("Nirvhoy — Technical Chain of Custody & Cryptographic Evidence", body_style))
    story.append(Spacer(1, 6*mm))

    data = [
        ["Vault ID", str(evidence.vault_id)],
        ["SHA-256 File Hash", evidence.file_hash],
        ["Encryption Nonce (hex)", evidence.encryption_nonce.hex() if evidence.encryption_nonce else "N/A"],
        ["Stored Size (bytes)", str(evidence.stored_size_bytes or "N/A")],
        ["Original Size (bytes)", str(evidence.original_size_bytes or "N/A")],
        ["Chain Intact", "Yes" if chain_result.get("is_intact") else "No"],
    ]
    t = Table(data, colWidths=[45*mm, 120*mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Blockchain Audit Trail", ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=10, spaceAfter=3)))
    for block in chain_result.get("blocks", []):
        story.append(Paragraph(f"Block #{block.get('block_number')} — {block.get('event_type', '')} — Valid: {block.get('is_valid', False)}", body_style))
        if block.get("notes"):
            story.append(Paragraph(f"  Notes: {block['notes']}", body_style))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("This report is for forensic testimony and includes raw cryptographic metadata.", body_style))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="expert-report-{evidence.vault_id}.pdf"'
    return response