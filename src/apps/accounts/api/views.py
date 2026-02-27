from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from apps.accounts.models import User


class MobileLoginView(APIView):
    """
    POST /api/v1/auth/login/

    Flutter app login. Returns JWT access + refresh tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"success": False, "error": "Username and password required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {"success": False, "error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "role": user.role,
                    "nid_verified": user.nid_verified,
                },
            }
        )


class MobileRegisterView(APIView):
    """
    POST /api/v1/auth/register/

    Register a new victim account.
    NID hash is computed server-side from submitted raw NID.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        phone_number = request.data.get("phone_number")
        raw_nid = request.data.get("nid_number")   # Raw NID — hashed immediately

        if not all([username, password, raw_nid]):
            return Response(
                {"success": False, "error": "username, password and nid_number are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"success": False, "error": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Hash the NID immediately — never store raw
        nid_hash = User.hash_nid(raw_nid)

        if User.objects.filter(nid_hash=nid_hash).exists():
            return Response(
                {"success": False, "error": "This NID is already registered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            password=password,
            phone_number=phone_number,
            nid_hash=nid_hash,
            role=User.UserRole.VICTIM,
            nid_verified=False,
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "message": "Account created. NID verification pending.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "role": user.role,
                },
            },
            status=status.HTTP_201_CREATED,
        )