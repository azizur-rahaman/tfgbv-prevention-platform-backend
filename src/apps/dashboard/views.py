from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator

from apps.evidence.models import Evidence
from apps.blockchain.services import verify_chain_integrity, verify_single_evidence_chain
from apps.accounts.models import User
from apps.dashboard.permissions import get_evidence_queryset_for_role


DASHBOARD_ROLES = [
    User.UserRole.POLICE,
    User.UserRole.FORENSIC_ANALYST,
    User.UserRole.BCC_ADMIN,
    User.UserRole.JUDICIARY,
]


class DashboardLoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard-home")
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
    """Redirects to role-specific dashboard home."""
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
        return redirect("dashboard-login")


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
class PoliceHomeView(View):
    def get(self, request):
        context = _role_home_context(request)
        context["role_label"] = "Police"
        return render(request, "dashboard/home.html", context)


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class ForensicHomeView(View):
    def get(self, request):
        context = _role_home_context(request)
        context["role_label"] = "Forensic Analyst"
        return render(request, "dashboard/home.html", context)


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
        base_qs = Evidence.objects.filter(status="verified").order_by("-uploaded_at")
        evidence_list = get_evidence_queryset_for_role(request.user, base_qs)

        return render(request, "dashboard/certificates.html", {
            "evidence_list": evidence_list,
        })


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardCertificateView(View):
    def get(self, request, vault_id):
        base_qs = Evidence.objects.all()
        allowed_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(allowed_qs, vault_id=vault_id)
        chain_result = verify_single_evidence_chain(str(vault_id))
        # Part 3 will replace this with PDF generation
        return render(request, "dashboard/case_detail.html", {
            "evidence": evidence,
            "chain_result": chain_result,
        })