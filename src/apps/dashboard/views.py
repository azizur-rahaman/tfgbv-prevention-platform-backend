from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Count, Q
from django.utils import timezone

from apps.evidence.models import Evidence
from apps.blockchain.models import ForensicLog
from apps.blockchain.services import (
    verify_chain_integrity,
    verify_single_evidence_chain,
)
from apps.accounts.models import User
from apps.dashboard.permissions import (
    role_required,
    get_evidence_queryset_for_role,
    POLICE_AND_ABOVE,
    FORENSIC_AND_ABOVE,
    BCC_ONLY,
    COURT_ROLES,
)


# ------------------------------------------------------------------ #
# AUTH VIEWS
# ------------------------------------------------------------------ #

class DashboardLoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        return render(request, "dashboard/login.html")

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, "dashboard/login.html", {
                "error": "Invalid credentials."
            })

        if user.role not in POLICE_AND_ABOVE:
            return render(request, "dashboard/login.html", {
                "error": "Access denied. Only authorized personnel can access this dashboard."
            })

        login(request, user)
        return redirect("dashboard:home")


class DashboardLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("dashboard:login")


class ForbiddenView(View):
    def get(self, request):
        return render(request, "dashboard/forbidden.html", status=403)


# ------------------------------------------------------------------ #
# HOME — Role-aware overview
# ------------------------------------------------------------------ #

@method_decorator(
    login_required(login_url="/dashboard/login/"),
    name="dispatch"
)
class DashboardHomeView(View):
    def get(self, request):
        user = request.user
        base_qs = Evidence.objects.all()
        filtered_qs = get_evidence_queryset_for_role(user, base_qs)

        # Stats
        total_evidence = filtered_qs.count()
        pending = filtered_qs.filter(status=Evidence.EvidenceStatus.PENDING).count()
        verified = filtered_qs.filter(status=Evidence.EvidenceStatus.VERIFIED).count()
        submitted = filtered_qs.filter(status=Evidence.EvidenceStatus.SUBMITTED).count()
        flagged = filtered_qs.filter(status=Evidence.EvidenceStatus.FLAGGED).count()
        total_blocks = ForensicLog.objects.count()

        recent_evidence = filtered_qs.select_related(
            "reporter"
        ).order_by("-uploaded_at")[:10]

        harm_breakdown = (
            filtered_qs.values("harm_type")
            .annotate(count=Count("vault_id"))
            .order_by("-count")
        )

        # Chain integrity — only for forensic and above
        chain_result = {"is_intact": None, "error": None}
        if user.role in FORENSIC_AND_ABOVE + [User.UserRole.POLICE]:
            chain_result = verify_chain_integrity()

        # BCC Admin extras
        total_users = None
        users_by_role = None
        if user.role == User.UserRole.BCC_ADMIN:
            total_users = User.objects.count()
            users_by_role = (
                User.objects.values("role")
                .annotate(count=Count("id"))
                .order_by("-count")
            )

        context = {
            "total_evidence": total_evidence,
            "pending": pending,
            "verified": verified,
            "submitted": submitted,
            "flagged": flagged,
            "total_blocks": total_blocks,
            "recent_evidence": recent_evidence,
            "harm_breakdown": harm_breakdown,
            "chain_intact": chain_result["is_intact"],
            "chain_error": chain_result["error"],
            "total_users": total_users,
            "users_by_role": users_by_role,
            "officer": user,
        }
        return render(request, "dashboard/home.html", context)


# ------------------------------------------------------------------ #
# EVIDENCE LIST
# ------------------------------------------------------------------ #

@method_decorator(
    login_required(login_url="/dashboard/login/"),
    name="dispatch"
)
class EvidenceListView(View):
    def get(self, request):
        base_qs = Evidence.objects.select_related("reporter")
        queryset = get_evidence_queryset_for_role(
            request.user, base_qs
        ).order_by("-uploaded_at")

        # Filters
        status_filter = request.GET.get("status", "")
        harm_filter = request.GET.get("harm_type", "")
        search = request.GET.get("search", "")

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if harm_filter:
            queryset = queryset.filter(harm_type=harm_filter)
        if search:
            queryset = queryset.filter(
                Q(reporter__username__icontains=search) |
                Q(file_hash__icontains=search) |
                Q(vault_id__icontains=search)
            )

        context = {
            "evidence_list": queryset,
            "status_choices": Evidence.EvidenceStatus.choices,
            "harm_choices": Evidence.HarmType.choices,
            "status_filter": status_filter,
            "harm_filter": harm_filter,
            "search": search,
            "officer": request.user,
        }
        return render(request, "dashboard/evidence_list.html", context)


# ------------------------------------------------------------------ #
# EVIDENCE DETAIL — Forensic Dossier
# ------------------------------------------------------------------ #

@method_decorator(
    login_required(login_url="/dashboard/login/"),
    name="dispatch"
)
class EvidenceDetailView(View):
    def get(self, request, vault_id):
        base_qs = Evidence.objects.all()
        filtered_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(filtered_qs, vault_id=vault_id)

        blockchain_logs = ForensicLog.objects.filter(
            evidence=evidence
        ).order_by("block_number")

        chain_result = verify_single_evidence_chain(str(vault_id))

        # Log this access in blockchain
        ForensicLog.objects.create(
            event_type=ForensicLog.EventType.ACCESS,
            evidence=evidence,
            evidence_hash_snapshot=evidence.file_hash,
            actor_user_id=str(request.user.id),
            actor_role=request.user.role,
            notes=(
                f"Accessed by {request.user.get_role_display()} "
                f"'{request.user.username}' via dashboard."
            ),
        )

        context = {
            "evidence": evidence,
            "blockchain_logs": blockchain_logs,
            "chain_intact": chain_result["is_intact"],
            "chain_error": chain_result["error"],
            "chain_blocks": chain_result["blocks"],
            "can_update_status": request.user.role in COURT_ROLES,
            "can_generate_certificate": request.user.role in COURT_ROLES,
            "officer": request.user,
        }
        return render(request, "dashboard/evidence_detail.html", context)

    def post(self, request, vault_id):
        if request.user.role not in COURT_ROLES:
            return redirect("dashboard:forbidden")

        base_qs = Evidence.objects.all()
        filtered_qs = get_evidence_queryset_for_role(request.user, base_qs)
        evidence = get_object_or_404(filtered_qs, vault_id=vault_id)

        new_status = request.POST.get("status")
        valid_statuses = [s[0] for s in Evidence.EvidenceStatus.choices]

        if new_status in valid_statuses:
            evidence.status = new_status
            evidence.verified_by = request.user
            evidence.verified_at = timezone.now()
            evidence.save()

            ForensicLog.objects.create(
                event_type=ForensicLog.EventType.VERIFICATION,
                evidence=evidence,
                evidence_hash_snapshot=evidence.file_hash,
                actor_user_id=str(request.user.id),
                actor_role=request.user.role,
                notes=f"Status updated to '{new_status}' by {request.user.username}.",
            )

        return redirect("dashboard:evidence_detail", vault_id=vault_id)


# ------------------------------------------------------------------ #
# CHAIN VERIFY — Forensic + BCC only
# ------------------------------------------------------------------ #

@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(*FORENSIC_AND_ABOVE + [User.UserRole.POLICE]), name="dispatch")
class ChainVerifyView(View):
    def get(self, request):
        result = verify_chain_integrity()
        context = {
            "is_intact": result["is_intact"],
            "total_blocks": result["total_blocks"],
            "broken_at_block": result["broken_at_block"],
            "error": result["error"],
            "blocks_checked": result["blocks_checked"],
            "officer": request.user,
        }
        return render(request, "dashboard/chain_verify.html", context)


# ------------------------------------------------------------------ #
# USER MANAGEMENT — BCC Admin only
# ------------------------------------------------------------------ #

@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(*BCC_ONLY), name="dispatch")
class UserManagementView(View):
    def get(self, request):
        search = request.GET.get("search", "")
        role_filter = request.GET.get("role", "")

        users = User.objects.order_by("-created_at")

        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(phone_number__icontains=search)
            )
        if role_filter:
            users = users.filter(role=role_filter)

        context = {
            "users": users,
            "role_choices": User.UserRole.choices,
            "search": search,
            "role_filter": role_filter,
            "officer": request.user,
            "total_users": User.objects.count(),
        }
        return render(request, "dashboard/user_management.html", context)


@method_decorator(login_required(login_url="/dashboard/login/"), name="dispatch")
@method_decorator(role_required(*BCC_ONLY), name="dispatch")
class UserDetailView(View):
    def get(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)
        user_evidence = Evidence.objects.filter(
            reporter=target_user
        ).order_by("-uploaded_at")

        context = {
            "target_user": target_user,
            "user_evidence": user_evidence,
            "officer": request.user,
        }
        return render(request, "dashboard/user_detail.html", context)

    def post(self, request, user_id):
        """BCC Admin can toggle active status or change role."""
        target_user = get_object_or_404(User, id=user_id)
        action = request.POST.get("action")

        if action == "toggle_active":
            target_user.is_active = not target_user.is_active
            target_user.save()

        elif action == "change_role":
            new_role = request.POST.get("role")
            valid_roles = [r[0] for r in User.UserRole.ch