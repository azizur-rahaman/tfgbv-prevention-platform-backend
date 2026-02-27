from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator

from apps.evidence.models import Evidence
from apps.blockchain.services import verify_chain_integrity, verify_single_evidence_chain
from apps.accounts.models import User


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


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardHomeView(View):
    def get(self, request):
        stats = {
            "total": Evidence.objects.count(),
            "verified": Evidence.objects.filter(status="verified").count(),
            "pending": Evidence.objects.filter(status="pending").count(),
            "flagged": Evidence.objects.filter(status="flagged").count(),
        }

        chain = verify_chain_integrity()
        recent_evidence = Evidence.objects.order_by("-uploaded_at")[:10]

        return render(request, "dashboard/home.html", {
            "stats": stats,
            "chain_intact": chain["is_intact"],
            "total_blocks": chain["total_blocks"],
            "recent_evidence": recent_evidence,
        })


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardCasesView(View):
    def get(self, request):
        qs = Evidence.objects.order_by("-uploaded_at")

        status = request.GET.get("status")
        harm_type = request.GET.get("harm_type")

        if status:
            qs = qs.filter(status=status)
        if harm_type:
            qs = qs.filter(harm_type=harm_type)

        return render(request, "dashboard/cases.html", {
            "evidence_list": qs,
            "total_count": qs.count(),
        })


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardCaseDetailView(View):
    def get(self, request, vault_id):
        evidence = get_object_or_404(Evidence, vault_id=vault_id)
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
        evidence_list = Evidence.objects.filter(
            status="verified"
        ).order_by("-uploaded_at")

        return render(request, "dashboard/certificates.html", {
            "evidence_list": evidence_list,
        })


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
class DashboardCertificateView(View):
    def get(self, request, vault_id):
        evidence = get_object_or_404(Evidence, vault_id=vault_id)
        chain_result = verify_single_evidence_chain(str(vault_id))
        # Part 3 will replace this with PDF generation
        return render(request, "dashboard/case_detail.html", {
            "evidence": evidence,
            "chain_result": chain_result,
        })