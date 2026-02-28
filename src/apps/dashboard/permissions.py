from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from apps.accounts.models import User


# ------------------------------------------------------------------ #
# Role Groups (for easy reuse across views)
# ------------------------------------------------------------------ #
POLICE_AND_ABOVE = [
    User.UserRole.POLICE,
    User.UserRole.FORENSIC_ANALYST,
    User.UserRole.BCC_ADMIN,
    User.UserRole.JUDICIARY,
]

FORENSIC_AND_ABOVE = [
    User.UserRole.FORENSIC_ANALYST,
    User.UserRole.BCC_ADMIN,
]

BCC_ONLY = [
    User.UserRole.BCC_ADMIN,
]

COURT_ROLES = [
    User.UserRole.POLICE,
    User.UserRole.FORENSIC_ANALYST,
    User.UserRole.BCC_ADMIN,
    User.UserRole.JUDICIARY,
]


def role_required(*allowed_roles):
    """
    Decorator for class-based views.
    Redirects to /dashboard/forbidden/ if user role is not in allowed_roles.

    Usage:
        @method_decorator(role_required(User.UserRole.POLICE, User.UserRole.BCC_ADMIN), name="dispatch")
        class MyView(View):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("/dashboard/login/")
            if request.user.role not in allowed_roles:
                return redirect("/dashboard/forbidden/")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_evidence_queryset_for_role(user, base_queryset):
    """
    Filters an Evidence queryset based on the user's role.

    - Police: all evidence (no upazila filter in dev; can re-enable later)
    - Forensic Analyst: all evidence
    - BCC Admin: all evidence
    - Judiciary: only evidence submitted to court
    """
    from apps.evidence.models import Evidence

    if user.role == User.UserRole.POLICE:
        # Dev: show all evidence. For production, filter by assigned_upazila if set.
        return base_queryset

    elif user.role == User.UserRole.FORENSIC_ANALYST:
        return base_queryset

    elif user.role == User.UserRole.BCC_ADMIN:
        return base_queryset

    elif user.role == User.UserRole.JUDICIARY:
        # Judiciary only sees cases submitted to court
        return base_queryset.filter(status=Evidence.EvidenceStatus.SUBMITTED)

    return base_queryset.none()